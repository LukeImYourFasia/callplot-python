"""The entry points, run in process (DESIGN-PYTHON.md sections 3.6 and 4.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Delta over DESIGN-PYTHON.md section 4.2, recorded in docs/appendix-b.md: the
design's six ``tests/unit/`` files cover the helpers, and DESIGN-PYTHON.md
section 4.5 reaches the commands as subprocesses, whose statements pytest-cov
cannot see.  That left ``cli``, ``plottable``, ``prep_cli`` and ``__main__``
near 0% and the section 4.7 gate ``[tool.coverage.report] fail_under = 90``
short, so this file adds the in-process leg of the same four entry points.
The published-command behaviour stays owned by ``tests/cli/test_cli.py``.

How the in-process leg stays honest:

* the streams are real files: section 3.6 rules 7, 10 and 11 write through
  ``sys.stdout.buffer`` and ``sys.stderr``, and rule 10's
  ``os.dup2(os.devnull, sys.stdout.fileno())`` needs a real fd;
* the handlers are reached by making the module's own collaborator raise
  (``monkeypatch`` puts it back the moment the test ends) -- the same traps of
  DESIGN.md section 4.4 the CLI layer pins from outside;
* cwd moves to the pytest folder, so ``plottable -debug``'s one side file
  ``_x_<pid>.xml`` (DESIGN.md section 3.13.5) never lands in the repository;
* ``python -m callplot`` (section 3.1 rule 3) runs the package through ``runpy``,
  the way the interpreter's ``-m`` switch does, which is what lets the gate see
  ``__main__``'s two statements.

The last tests pin what only this layer can reach: ``render``'s fresh default
``ctx``/``options``, its ``unknown output mode`` throw, the ``parse_table_style``
and ``parse_html_layout`` helpers of DESIGN-PYTHON.md section 2.3, and the
``opt/htmlLayout`` route of DESIGN.md section 3.12.6 (the snapshots force a
layout, so no golden walks that branch).  No fixture, golden or sample is read.
"""

import io
import runpy
import sys

import pytest
from conftest import TABLE_STYLES

from callplot import cli, plottable, prep_cli, render
from callplot.constants import Mode
from callplot.context import RunContext
from callplot.errors import CallplotError, IllegalArgumentError
from callplot.options import (
    HtmlLayout,
    RenderOptions,
    TableStyle,
    parse_html_layout,
    parse_table_style,
)
from callplot.trace_prep import prep

DIAGRAM = "guy/alice/first\nguy/bob/second\nalice->bob/HELLO\n"
DIAGRAM_2 = "guy/alice/first\nguy/bob/second\nalice->bob/THERE\n"
TRACE = "@ 0x1 bob\n@ 0x2 carol\nguy/alice/first\n"
BAD_GUY = "guy/alice\nalice->bob/HELLO\n"
LAYOUT_OPT = DIAGRAM + "opt/htmlLayout/sidebyside\n"
BAD_LAYOUT_OPT = DIAGRAM + "opt/htmlLayout/bogus\n"

# the page's two radios (renderers/html/page.py): exactly one carries the bare
# ``checked`` attribute, and that is the layout the page uses
RADIO_TB = 'id="lay-tb" class="cpf-radio" checked'
RADIO_SBS = 'id="lay-sbs" class="cpf-radio" checked'


def raiser(exc):
    """A collaborator that fails with ``exc``, for the handler tests."""

    def boom(*args, **kwargs):
        raise exc

    return boom


def entry(monkeypatch, tmp_path, run, argv, *, stdin=b""):
    """Run ``run(argv)`` in this process; the streams become real files.

    Returns the exit code, the bytes on stdout and the text on stderr.  A
    ``SystemExit`` (argparse of DESIGN-PYTHON.md section 3.6) becomes its code.
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / "stdin.bin").write_bytes(stdin)
    with (
        (tmp_path / "stdout.bin").open("wb") as out_bin,
        (tmp_path / "stderr.bin").open("wb") as err_bin,
        (tmp_path / "stdin.bin").open("rb") as in_bin,
    ):
        streams = (
            io.TextIOWrapper(out_bin, encoding="utf-8"),
            io.TextIOWrapper(err_bin, encoding="utf-8"),
            io.TextIOWrapper(in_bin, encoding="utf-8"),
        )
        monkeypatch.setattr(sys, "stdout", streams[0])
        monkeypatch.setattr(sys, "stderr", streams[1])
        monkeypatch.setattr(sys, "stdin", streams[2])
        try:
            code = run(argv)
        except SystemExit as stop:
            code = stop.code
        finally:
            for stream in streams:
                stream.close()
    return (
        code,
        (tmp_path / "stdout.bin").read_bytes(),
        (tmp_path / "stderr.bin").read_text(encoding="utf-8"),
    )


def input_file(tmp_path, text, *, name="in.callplot"):
    """One input file in the run folder; the path the command argument gets."""
    path = tmp_path / name
    path.write_bytes(text.encode("utf-8"))
    return str(path)


def run_as_main(argv):
    """``python -m callplot {argv}`` (DESIGN-PYTHON.md section 3.1 rule 3).

    ``runpy.run_module`` is what ``python -m`` does, so the gate measures
    ``__main__``'s two statements; ``sys.exit(main())`` always raises, and
    :func:`entry` turns that raise into the exit code.
    """
    runpy.run_module("callplot", run_name="__main__", alter_sys=True)
    return 0


def as_main(monkeypatch, tmp_path, argv):
    """``python -m callplot {argv}`` through the same stream swap."""
    monkeypatch.setitem(sys.modules, "__main__", sys.modules["__main__"])
    monkeypatch.setattr(sys, "argv", ["callplot", *argv])
    return entry(monkeypatch, tmp_path, run_as_main, [])


# --------------------------------------------------------------------------------------
# callplot: DESIGN.md section 4.4, DESIGN-PYTHON.md section 3.6
# --------------------------------------------------------------------------------------


@pytest.mark.unit
def test_cli_main__no_arguments_usage_on_stderr_exit_1(monkeypatch, tmp_path):
    """Main.java:41-44: nothing on stdout, the usage block on stderr, exit 1."""
    code, out, err = entry(monkeypatch, tmp_path, cli.main, [])
    assert code == 1
    assert out == b""
    assert err.startswith("Usage: callplot")


@pytest.mark.unit
@pytest.mark.parametrize("flag", ["-?", "--help"])
def test_cli_main__help_flag_exits_0(flag, monkeypatch, tmp_path):
    """Main.java:64-66: the run stops at the usage block, exit 0."""
    code, out, err = entry(monkeypatch, tmp_path, cli.main, [flag])
    assert code == 0
    assert out == b""
    assert err.startswith("Usage: callplot")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("mode", "flag"),
    [
        (Mode.TEXT, []),
        (Mode.PIC, ["-pic"]),
        (Mode.SVG, ["-svg"]),
        (Mode.VML, ["-vml"]),
        (Mode.XML, ["-xml"]),
        (Mode.VXML, ["-vxml"]),
        (Mode.GRAFFLE, ["-graffle"]),
        (Mode.MERMAID, ["-mermaid"]),
        (Mode.PLANTUML, ["-plantuml"]),
    ],
)
def test_cli_main__every_core_mode_flag_renders(mode, flag, monkeypatch, tmp_path):
    """One flag per mode of DESIGN.md section 2.2: bytes out, exit 0."""
    code, out, err = entry(monkeypatch, tmp_path, cli.main, [*flag, input_file(tmp_path, DIAGRAM)])
    assert code == 0
    assert err == ""
    assert out != b""


@pytest.mark.unit
def test_cli_main__last_mode_flag_wins(monkeypatch, tmp_path):
    """section 3.6 rule 8: the flag loop keeps the mode it saw last."""
    code, out, err = entry(
        monkeypatch, tmp_path, cli.main, ["-pic", "-graffle", input_file(tmp_path, DIAGRAM)]
    )
    assert code == 0
    assert err == ""
    assert "<!DOCTYPE plist" in out.decode("utf-8")


@pytest.mark.unit
def test_cli_main__dash_reads_stdin(monkeypatch, tmp_path):
    """section 3.2: ``-`` is stdin, bytes in and bytes out."""
    code, out, err = entry(monkeypatch, tmp_path, cli.main, ["-"], stdin=DIAGRAM.encode())
    assert code == 0
    assert err == ""
    assert out.decode("utf-8") == render(DIAGRAM, Mode.TEXT)


@pytest.mark.unit
def test_cli_main__file_argument_gives_the_same_bytes(monkeypatch, tmp_path):
    """A path argument reads the file (section 3.2), same bytes as stdin."""
    code, out, err = entry(monkeypatch, tmp_path, cli.main, [input_file(tmp_path, DIAGRAM)])
    assert code == 0
    assert err == ""
    assert out.decode("utf-8") == render(DIAGRAM, Mode.TEXT)


@pytest.mark.unit
def test_cli_main__two_files_each_get_their_own_page(monkeypatch, tmp_path):
    """section 3.6 rule 2: one RunContext for the whole loop over the files."""
    first = input_file(tmp_path, DIAGRAM, name="one.callplot")
    second = input_file(tmp_path, DIAGRAM_2, name="two.callplot")
    code, out, _err = entry(monkeypatch, tmp_path, cli.main, ["-graffle", first, second])
    assert code == 0
    assert out.decode("utf-8").count("</plist>") == 2
    assert "HELLO" in out.decode("utf-8")
    assert "THERE" in out.decode("utf-8")


@pytest.mark.unit
def test_cli_main__unreadable_file_is_one_line_and_exit_1(monkeypatch, tmp_path):
    """section 3.6 rule 7: the name it was given, then the OS reason."""
    code, out, err = entry(monkeypatch, tmp_path, cli.main, ["no-such-file.callplot"])
    assert code == 1
    assert out == b""
    assert err == "callplot: no-such-file.callplot: No such file or directory\n"


@pytest.mark.unit
def test_cli_main__bad_input_names_the_error_class(monkeypatch, tmp_path):
    """section 3.6 rules 7 and 11: the Java class name, not a JVM stack trace.

    A ``guy`` line with no caption is the out-of-range line field of DESIGN.md
    section 4.4, whose class is ``IndexError``.
    """
    code, out, err = entry(monkeypatch, tmp_path, cli.main, [input_file(tmp_path, BAD_GUY)])
    assert code == 1
    assert out == b""
    assert err == "callplot: IndexError: Index out of range\n"


@pytest.mark.unit
def test_cli_main__table_style_is_rejected_before_the_file(monkeypatch, tmp_path):
    """section 3.13.5: no file is read, no byte is written."""
    code, out, err = entry(monkeypatch, tmp_path, cli.main, ["-table=bogus"])
    assert code == 1
    assert out == b""
    assert err == "callplot: unknown table style: bogus\n"


@pytest.mark.unit
def test_cli_main__unknown_html_layout_is_rejected(monkeypatch, tmp_path):
    """The new ``-html={layout}`` name is checked the way the style is."""
    code, out, err = entry(monkeypatch, tmp_path, cli.main, ["-html=bogus"])
    assert code == 1
    assert out == b""
    assert err == "callplot: unknown html layout: bogus\n"


@pytest.mark.unit
@pytest.mark.parametrize("layout", [HtmlLayout.TOPBOTTOM, HtmlLayout.SIDEBYSIDE])
def test_cli_main__html_layout_flag_checks_that_radio(layout, monkeypatch, tmp_path):
    """DESIGN.md section 3.12.6: ``-html={layout}`` forces that layout."""
    code, out, err = entry(
        monkeypatch,
        tmp_path,
        cli.main,
        [f"-html={layout.value}", input_file(tmp_path, DIAGRAM)],
    )
    assert code == 0
    assert err == ""
    want = RADIO_TB if layout is HtmlLayout.TOPBOTTOM else RADIO_SBS
    other = RADIO_SBS if want is RADIO_TB else RADIO_TB
    assert want.encode() in out
    assert other.encode() not in out


@pytest.mark.unit
def test_cli_main__bare_html_flag_defaults_to_topbottom(monkeypatch, tmp_path):
    """``-html`` alone clears any force: the input has no opt line (3.12.6)."""
    code, out, err = entry(
        monkeypatch, tmp_path, cli.main, ["-html", input_file(tmp_path, DIAGRAM)]
    )
    assert code == 0
    assert err == ""
    assert RADIO_TB.encode() in out
    assert RADIO_SBS.encode() not in out


@pytest.mark.unit
@pytest.mark.parametrize(
    ("module", "attr", "exc", "want", "note"),
    [
        (cli, "render", KeyboardInterrupt, 130, ""),
        (cli, "write_out", BrokenPipeError, 0, ""),
        (cli, "render", KeyError("boom"), 1, "internal error, please report it"),
        (plottable, "render", KeyboardInterrupt, 130, ""),
        (plottable, "write_out", BrokenPipeError, 0, ""),
        (plottable, "render", KeyError("boom"), 1, "internal error, please report it"),
        (prep_cli, "prep", KeyboardInterrupt, 130, ""),
        (prep_cli, "write_out", BrokenPipeError, 0, ""),
        (prep_cli, "prep", KeyError("boom"), 1, "internal error, please report it"),
    ],
)
def test_entry_main__handlers_of_section_3_6(module, attr, exc, want, note, monkeypatch, tmp_path):
    """Rule 9 exits 130 with nothing printed, rule 10 exits 0 quietly, and
    rule 8 prints the traceback plus one line asking to report it.  The
    collaborator is swapped only for the run and put back by monkeypatch."""
    monkeypatch.setattr(module, attr, raiser(exc))
    code, _out, err = entry(monkeypatch, tmp_path, module.main, [input_file(tmp_path, DIAGRAM)])
    assert code == want
    assert note in err
    assert ("Traceback" in err) is bool(note)


@pytest.mark.unit
def test_cli_main__as_main_equals_the_entry_point(monkeypatch, tmp_path):
    """section 3.1 rule 3: ``python -m callplot`` gives the same result."""
    path = input_file(tmp_path, DIAGRAM)
    direct, direct_out, direct_err = entry(monkeypatch, tmp_path, cli.main, ["-mermaid", path])
    code, out, err = as_main(monkeypatch, tmp_path, ["-mermaid", path])
    assert code == direct == 0
    assert out == direct_out
    assert err == direct_err


@pytest.mark.unit
def test_cli_main__as_main_no_arguments(monkeypatch, tmp_path):
    """``python -m callplot`` with nothing to do exits 1 like the command."""
    code, out, err = as_main(monkeypatch, tmp_path, [])
    assert code == 1
    assert out == b""
    assert err.startswith("Usage: callplot")


# --------------------------------------------------------------------------------------
# plottable: DESIGN.md sections 3.13 and 3.13.5
# --------------------------------------------------------------------------------------


@pytest.mark.unit
def test_plottable_main__usage_goes_to_stdout(monkeypatch, tmp_path):
    """plottable.sh echoed the usage, so it lands on stdout and exits 1."""
    code, out, err = entry(monkeypatch, tmp_path, plottable.main, [])
    assert code == 1
    assert err == ""
    assert out.decode("utf-8").startswith("usage: plottable")


@pytest.mark.unit
def test_plottable_main__too_many_arguments_print_the_usage(monkeypatch, tmp_path):
    """The script needed exactly one file after its own flag order."""
    first = input_file(tmp_path, DIAGRAM, name="one.callplot")
    second = input_file(tmp_path, DIAGRAM_2, name="two.callplot")
    code, out, err = entry(monkeypatch, tmp_path, plottable.main, [first, second])
    assert code == 1
    assert err == ""
    assert out.decode("utf-8").startswith("usage: plottable")


@pytest.mark.unit
def test_plottable_main__style_flag_with_no_name_uses_the_usage(monkeypatch, tmp_path):
    """``-style`` eats the file slot, so no file is left: usage, exit 1."""
    code, out, err = entry(
        monkeypatch, tmp_path, plottable.main, ["-style", input_file(tmp_path, DIAGRAM)]
    )
    assert code == 1
    assert err == ""
    assert out.decode("utf-8").startswith("usage: plottable")


@pytest.mark.unit
def test_plottable_main__table_bytes(monkeypatch, tmp_path):
    """DESIGN.md section 3.13: the table comes straight from the style."""
    code, out, err = entry(monkeypatch, tmp_path, plottable.main, [input_file(tmp_path, DIAGRAM)])
    assert code == 0
    assert err == ""
    assert "<table" in out.decode("utf-8")


@pytest.mark.unit
@pytest.mark.parametrize("style", TABLE_STYLES)
def test_plottable_main__every_table_style_exits_0(style, monkeypatch, tmp_path):
    """``-style {style}`` over the names of DESIGN.md section 3.13.2."""
    code, out, err = entry(
        monkeypatch, tmp_path, plottable.main, ["-style", style, input_file(tmp_path, DIAGRAM)]
    )
    assert code == 0
    assert err == ""
    assert "<table" in out.decode("utf-8")


@pytest.mark.unit
def test_plottable_main__debug_keeps_exactly_one_side_file(monkeypatch, tmp_path):
    """DESIGN.md section 3.13.5: one side file ``_x_<pid>.xml`` in the folder
    the command ran in, holding the XML step, named on stderr; no file named
    ``debug`` (DESIGN.md section 3.14.4's erratum of the awk)."""
    path = input_file(tmp_path, DIAGRAM)
    code, out, err = entry(monkeypatch, tmp_path, plottable.main, ["-debug", path])
    assert code == 0
    assert "<table" in out.decode("utf-8")
    assert err.startswith("retaining xml intermediate file in _x_")
    sides = [p for p in tmp_path.iterdir() if p.name.startswith("_x_")]
    assert len(sides) == 1
    assert sides[0].read_bytes().decode("utf-8") == render(DIAGRAM, Mode.XML)
    assert not (tmp_path / "debug").exists()


@pytest.mark.unit
def test_plottable_main__unknown_style_is_one_line(monkeypatch, tmp_path):
    """The script died inside Xalan finding no ``{style}.xsl`` (3.13.5)."""
    code, out, err = entry(
        monkeypatch, tmp_path, plottable.main, ["-style", "bogus", input_file(tmp_path, DIAGRAM)]
    )
    assert code == 1
    assert out == b""
    assert err == "plottable: unknown table style: bogus\n"


@pytest.mark.unit
def test_plottable_main__unreadable_file_is_one_line(monkeypatch, tmp_path):
    """section 3.6 rule 7 for this command."""
    code, out, err = entry(monkeypatch, tmp_path, plottable.main, ["no-such-file.callplot"])
    assert code == 1
    assert out == b""
    assert err == "plottable: no-such-file.callplot: No such file or directory\n"


@pytest.mark.unit
def test_plottable_main__bad_input_names_the_class(monkeypatch, tmp_path):
    """section 3.6 rules 7 and 11 for this command."""
    code, out, err = entry(monkeypatch, tmp_path, plottable.main, [input_file(tmp_path, BAD_GUY)])
    assert code == 1
    assert out == b""
    assert err == "plottable: IndexError: Index out of range\n"


# --------------------------------------------------------------------------------------
# callplot-prep: DESIGN.md sections 3.14 and 3.14.4
# --------------------------------------------------------------------------------------


@pytest.mark.unit
def test_prep_cli_main__no_argument_reads_stdin(monkeypatch, tmp_path):
    """The ``file`` argument defaults to ``-`` (DESIGN.md section 3.14)."""
    code, out, err = entry(monkeypatch, tmp_path, prep_cli.main, [], stdin=TRACE.encode())
    assert code == 0
    assert err == ""
    assert out.decode("utf-8") == prep(TRACE)


@pytest.mark.unit
def test_prep_cli_main__file_and_dash_are_the_same(monkeypatch, tmp_path):
    """A path or ``-`` both end at the same converted text."""
    path = input_file(tmp_path, DIAGRAM)
    code, out, err = entry(monkeypatch, tmp_path, prep_cli.main, [path])
    assert code == 0
    assert err == ""
    assert out.decode("utf-8") == prep(DIAGRAM)
    code2, out2, err2 = entry(monkeypatch, tmp_path, prep_cli.main, ["-"], stdin=DIAGRAM.encode())
    assert code2 == 0
    assert err2 == ""
    assert out2 == out


@pytest.mark.unit
def test_prep_cli_main__links_flag_is_the_awk_links_variable(monkeypatch, tmp_path):
    """``--links`` turns the emitted ``opt/links`` line on."""
    code, out, err = entry(
        monkeypatch, tmp_path, prep_cli.main, ["--links", input_file(tmp_path, DIAGRAM)]
    )
    assert code == 0
    assert err == ""
    assert out.decode("utf-8") == prep(DIAGRAM, links=True)


@pytest.mark.unit
def test_prep_cli_main__debug_file_appends(monkeypatch, tmp_path):
    """DESIGN.md section 3.14.4: the awk appended to a file named ``debug``;
    this port writes only where ``--debug-file`` points, and appends (the
    awk's ``>> debug``), and never makes a file called ``debug``."""
    path = input_file(tmp_path, TRACE)
    sink = tmp_path / "conv-debug.txt"
    code, _out, err = entry(monkeypatch, tmp_path, prep_cli.main, ["--debug-file", str(sink), path])
    assert code == 0
    assert err == ""
    assert sink.read_text().splitlines() == ["[bob] going into guys", "[carol] going into guys"]
    code2, _out2, _err2 = entry(
        monkeypatch, tmp_path, prep_cli.main, ["--debug-file", str(sink), path]
    )
    assert code2 == 0
    assert len(sink.read_text().splitlines()) == 4
    assert not (tmp_path / "debug").exists()


@pytest.mark.unit
def test_prep_cli_main__unreadable_file_is_one_line(monkeypatch, tmp_path):
    """section 3.6 rule 7, named for this command."""
    code, out, err = entry(monkeypatch, tmp_path, prep_cli.main, ["no-such-file.callplot"])
    assert code == 1
    assert out == b""
    assert err == "callplot-prep: no-such-file.callplot: No such file or directory\n"


@pytest.mark.unit
def test_prep_cli_main__unknown_option_exits_2(monkeypatch, tmp_path):
    """DESIGN-PYTHON.md section 3.6: the flags are argparse, and argparse
    exits 2 for an unknown option (the JS command exited 1: Appendix B)."""
    code, out, err = entry(monkeypatch, tmp_path, prep_cli.main, ["--nope"])
    assert code == 2
    assert out == b""
    assert err.startswith("usage: callplot-prep")
    assert "unrecognized arguments: --nope" in err


@pytest.mark.unit
def test_prep_cli_main__help_exits_0(monkeypatch, tmp_path):
    """argparse's own help goes to stdout and exits 0."""
    code, out, err = entry(monkeypatch, tmp_path, prep_cli.main, ["--help"])
    assert code == 0
    assert err == ""
    assert "--debug-file PATH" in out.decode("utf-8")


# --------------------------------------------------------------------------------------
# the API surface only this layer reaches (DESIGN-PYTHON.md 2.3, 3.12.6)
# --------------------------------------------------------------------------------------


@pytest.mark.unit
def test_render__fresh_default_context_and_options(monkeypatch, tmp_path):
    """section 2.3: ``ctx`` and ``options`` default to fresh ones, so a call
    that passes them cannot disagree with a call that does not."""
    once = render(DIAGRAM, Mode.GRAFFLE)
    explicit = render(DIAGRAM, Mode.GRAFFLE, ctx=RunContext(), options=RenderOptions())
    assert once == explicit


@pytest.mark.unit
def test_render__mode_that_is_not_one_of_the_output_modes_throws():
    """section 2.3: bad input raises a CallplotError and returns no output."""
    with pytest.raises(CallplotError, match="unknown output mode"):
        render(DIAGRAM, Mode.MERMAID | Mode.TEXT)


@pytest.mark.unit
def test_parse_table_style__tmltable_is_the_htmltable_alias():
    """DESIGN.md section 1.3: lib/tmltable.xsl is a byte copy of htmltable.xsl."""
    assert parse_table_style("tmltable") is TableStyle.HTMLTABLE
    assert parse_table_style("tmltable").value == "htmltable"


@pytest.mark.unit
@pytest.mark.parametrize("name", TABLE_STYLES)
def test_parse_table_style__every_spelling(name):
    """The seven spellings of DESIGN.md section 3.13.2 map to their style."""
    want = "htmltable" if name == "tmltable" else name
    assert parse_table_style(name).value == want


@pytest.mark.unit
def test_parse_table_style__unknown_name_raises_illegal_argument():
    """section 2.3: an unknown name raises, with the name it was given."""
    with pytest.raises(IllegalArgumentError, match="unknown table style: bogus"):
        parse_table_style("bogus")


@pytest.mark.unit
def test_parse_html_layout__maps_both_names_and_rejects_others():
    """DESIGN.md section 3.12.6 lists exactly the two layout names."""
    assert parse_html_layout("topbottom") is HtmlLayout.TOPBOTTOM
    assert parse_html_layout(HtmlLayout.SIDEBYSIDE) is HtmlLayout.SIDEBYSIDE
    with pytest.raises(IllegalArgumentError, match="unknown html layout: bogus"):
        parse_html_layout("bogus")


@pytest.mark.unit
def test_page_on__opt_line_picks_the_layout_when_the_api_does_not_force():
    """DESIGN.md section 3.12.6 order: no API force -> validate the opt line."""
    forced = render(DIAGRAM, Mode.HTML, options=RenderOptions(html_layout=HtmlLayout.SIDEBYSIDE))
    assert render(LAYOUT_OPT, Mode.HTML) == forced


@pytest.mark.unit
def test_page_on__api_option_clears_an_earlier_opt_line():
    """The API option forces a layout, like the JS port's undefined."""
    plain = render(DIAGRAM, Mode.HTML)
    assert (
        render(LAYOUT_OPT, Mode.HTML, options=RenderOptions(html_layout=HtmlLayout.TOPBOTTOM))
        == plain
    )


@pytest.mark.unit
def test_page_on__bad_opt_line_throws_before_any_byte():
    """The page picks the layout before it prints (section 3.12.6)."""
    with pytest.raises(IllegalArgumentError, match="unknown html layout: bogus"):
        render(BAD_LAYOUT_OPT, Mode.HTML)
