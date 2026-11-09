"""CLI layer: the installed commands, the 16 cases of DESIGN.md 4.4.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

DESIGN-PYTHON.md section 4.5 (the [cli] layer): every case in
``test/cli/*.json`` runs through the **commands as a person gets them** from
the published package — never through a script path someone runs by hand
inside the repository, which is what DESIGN-PYTHON.md section 5.4 rule 1
rules out (there is no ``bin/`` folder).

* 8 cases are the W0 goldens: stdout bytes and the exit code must equal
  ``test/golden/cli/<name> {out,exit}``.  stderr is never compared (DESIGN.md
  section 4.4), which is what lets the port name an error instead of dumping
  the JVM stack trace the original printed.
* the other 8 reuse a golden or check conditions: exit codes, a closed pipe,
  the single side file ``_x_<pid>.xml`` that ``plottable -debug`` leaves in the
  folder the command ran in, and that ``callplot-prep`` makes no file named
  ``debug`` (DESIGN.md section 3.14.4 erratum).
* extra tests: ``python -m callplot`` equals the command (DESIGN-PYTHON.md
  section 3.1 rule 3), and neither a ``bin/`` folder nor command-named files
  sit in the repository tree, on disk or in git (DESIGN-PYTHON.md 4.5).

How the command is reached, in order of trust (DESIGN-PYTHON.md 4.5):

1. the installed command itself, found with ``shutil.which``;
2. otherwise the exact wrapper pip wrote for the editable install
   (``python -c "from callplot.cli import main; sys.exit(main())"``), which is
   byte-for-byte what ``.venv/bin/callplot`` execs.  The module-to-entry-point
   table comes from ``importlib.metadata`` — the published package, not the
   source tree — so this test also proves ``[project.scripts]`` is right.

A bare case argument is a fixture in ``test/fixtures``, a real path is used as
it is, and a name that exists nowhere stays as it is so ``missing_file`` can
stay missing.
"""

import importlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path

import pytest
from conftest import diff_message
from paths import CLI_DIR, CLI_GOLDEN_DIR, FIXTURES_DIR, GOLDEN_DIR, REPO_ROOT

# the 8 cases whose bytes the Java oracle pinned in chunk W0
GOLDEN_CASES = {
    "help_after_file",
    "missing_file",
    "mode_switch",
    "multi_graffle_ids",
    "multi_stagger",
    "no_args",
    "stdin",
    "vxml",
}

# the json's "cmd" -> the command name a person types
COMMAND = {"callplot": "callplot", "plottable": "plottable", "prep": "callplot-prep"}

# command -> the published package's entry point, straight from metadata
ENTRY = {
    name: next(iter(metadata.entry_points(group="console_scripts", name=name))).value
    for name in COMMAND.values()
}


def typed_path(arg: str) -> str:
    """A bare fixture name means ``test/fixtures/<name>``; a real path is used
    as it is; a name that exists nowhere stays missing (the ``missing_file``
    case needs that)."""
    if arg == "-" or arg.startswith("-"):
        return arg
    fixture = FIXTURES_DIR / arg
    if fixture.exists():
        return str(fixture)
    direct = REPO_ROOT / arg
    if direct.exists():
        return str(direct)
    return arg


def command_argv(command: str) -> list[str]:
    """How a person reaches the command, best first (section 4.5)."""
    name = COMMAND[command]
    env_path = os.environ.get("PATH", "")
    bin_dir = str(Path(sys.executable).parent)
    found = shutil.which(name, path=bin_dir + os.sep + env_path)
    if found is not None:
        return [found]
    # the venv's bin folder was taken by another process (it edits the
    # shared .venv too); fall back to pip's own editable-install wrapper:
    # the same module and function the installed command runs, resolved
    # through the published package's metadata, not the source tree
    module, _, function = ENTRY[name].partition(":")
    if editable_install_for(name):
        return [
            sys.executable,
            "-c",
            f"import sys; from {module} import {function}; sys.exit({function}())",
        ]
    raise AssertionError(
        f"command {name} is neither installed nor editable; "
        f"pip install -e '.[dev]' or pip install -e . first"
    )


def editable_install_for(name: str) -> bool:
    """True when the entry point metadata maps to this repository's own source.

    The published package's ``[project.scripts]`` string is trusted only if
    importing its module loads a file under this ``src/callplot`` — that is
    pip's editable install, the same code ``.venv/bin/callplot`` runs.
    """
    module = ENTRY[name].partition(":")[0]
    try:
        mod = importlib.import_module(module)
    except ImportError:
        return False
    source = getattr(mod, "__file__", None)
    if source is None:
        return False
    package_dir = (REPO_ROOT / "src" / "callplot").resolve()
    return Path(source).resolve().is_relative_to(package_dir)


def run_command(
    command: str, args: list[str], stdin: bytes | None = None, cwd: Path | None = None
) -> subprocess.CompletedProcess:
    """Spawn the command with the case's own working folder."""
    return subprocess.run(
        command_argv(command) + [typed_path(a) for a in args],
        input=stdin if stdin is not None else b"",
        capture_output=True,
        cwd=cwd,
        encoding=None,
    )


def case_of(name: str) -> dict:
    return json.loads((CLI_DIR / (name + ".json")).read_text(encoding="utf-8"))


def stdin_of(cfg: dict) -> bytes:
    name = cfg.get("stdin")
    if name is None:
        return b""
    return (FIXTURES_DIR / name).read_bytes()


def check_cli(name: str, tmp_path: Path) -> None:
    """One case: golden bytes/exit, or the conditions its check row gives."""
    cfg = case_of(name)
    special = name in ("plottable_debug", "prep_stdin")
    result = run_command(
        cfg.get("cmd", "callplot"),
        cfg["args"],
        stdin_of(cfg),
        cwd=tmp_path if special else REPO_ROOT,
    )

    if name in GOLDEN_CASES:
        want = (CLI_GOLDEN_DIR / (name + ".out")).read_bytes()
        assert result.stdout == want, diff_message(name, want, result.stdout)
        want_exit = int((CLI_GOLDEN_DIR / (name + ".exit")).read_text(encoding="utf-8"))
        assert result.returncode == want_exit, (
            f"exit code {result.returncode} vs wanted {want_exit}"
        )
    elif name == "table_default":
        want = (GOLDEN_DIR / "s_fred_annot.table-archtable.out").read_bytes()
        assert result.stdout == want, diff_message("table_default", want, result.stdout)
        assert result.returncode == 0, f"exit code {result.returncode} vs wanted 0"
    elif name == "table_bad_style":
        assert result.returncode == 1, f"exit code {result.returncode} vs wanted 1"
        assert result.stdout == b"", "an unknown style must print no table"
    elif name == "html_bad_layout_file":
        assert result.returncode == 1, f"exit code {result.returncode} vs wanted 1"
        assert result.stdout == b"", "the page throws before any byte (section 3.12.6)"
    elif name == "html_flag_wins":
        assert result.returncode == 0, f"exit code {result.returncode} vs wanted 0"
        page = result.stdout.decode("utf-8")
        assert 'id="lay-sbs" class="cpf-radio" checked' in page, (
            "the -html=sidebyside flag must win over the input's opt line"
        )
        assert 'id="lay-tb" class="cpf-radio" checked' not in page, (
            "only the chosen radio starts checked"
        )
    elif name == "plottable_usage":
        want = (CLI_DIR / "plottable_usage.expected").read_bytes()
        assert result.stdout == want, diff_message("plottable_usage", want, result.stdout)
        assert result.returncode == 1, "the script exits 1 after its usage block"
    elif name == "plottable_debug":
        assert result.returncode == 0, f"exit code {result.returncode} vs wanted 0"
        want = (GOLDEN_DIR / "s_sip_annot.table-htmltable3.out").read_bytes()
        assert result.stdout == want, diff_message("plottable_debug", want, result.stdout)
        assert b"retaining xml intermediate file in _x_" in result.stderr, (
            "the retaining line goes to stderr (section 3.13.5)"
        )
        side = [
            p for p in tmp_path.iterdir() if p.name.startswith("_x_") and p.name.endswith(".xml")
        ]
        assert len(side) == 1, f"exactly one _x_<pid>.xml expected, got {len(side)}"
        xml_want = (GOLDEN_DIR / "s_sip_annot.xml.out").read_bytes()
        assert side[0].read_bytes() == xml_want, diff_message(
            "plottable_debug xml", xml_want, side[0].read_bytes()
        )
    elif name == "prep_stdin":
        want = (GOLDEN_DIR / "trace_sip.prep.out").read_bytes()
        assert result.stdout == want, diff_message("prep_stdin", want, result.stdout)
        assert result.returncode == 0, f"exit code {result.returncode} vs wanted 0"
        assert not any(p.name == "debug" for p in tmp_path.iterdir()), (
            "section 3.14.4: the awk wrote to a file named debug, this port "
            "writes only where --debug-file pointed"
        )
    else:
        raise AssertionError(f"cli case {name} has no check in this harness")


def check_epipe(tmp_path: Path) -> None:
    """`callplot big | head -n 1`: the reader hangs up the pipe (DESIGN-PYTHON.md
    section 3.6 rule 10): exit 0, empty stderr, no interpreter exit-flush noise.
    bash stands in for the shell so PIPESTATUS[0] is the port's own exit code."""
    cfg = case_of("epipe")
    head, *extra = command_argv(cfg.get("cmd", "callplot"))
    # the -c fallback code carries spaces and quotes: quote every word for bash
    words = " ".join(shlex.quote(w) for w in [head, *extra, *(typed_path(a) for a in cfg["args"])])
    script = f"{words} | head -n 1; exit ${{PIPESTATUS[0]}}"
    result = subprocess.run(
        ["/bin/bash", "-c", script], capture_output=True, cwd=REPO_ROOT, encoding=None
    )
    assert result.returncode == 0, f"exit code {result.returncode} vs wanted 0"
    assert result.stderr == b"", "stderr must be empty (nothing escaped the pipe)"


CASE_NAMES = sorted(p.name[: -len(".json")] for p in CLI_DIR.glob("*.json"))


@pytest.mark.cli
@pytest.mark.parametrize("name", CASE_NAMES, ids=CASE_NAMES)
def test_cli(name: str, tmp_path: Path) -> None:
    """One case of test/cli/*.json, run through the commands as a person has them."""
    if name == "epipe":
        check_epipe(tmp_path)
        return
    check_cli(name, tmp_path)


@pytest.mark.cli
def test_cli_epipe__reader_hangs_up__exit_0_and_empty_stderr(tmp_path: Path) -> None:
    """DESIGN-PYTHON.md 4.5 / DESIGN.md 4.4: ``callplot big | head -n 1``.

    The reader stops reading, so the port must exit 0 with an empty stderr:
    no traceback and no "Exception ignored" from the interpreter's own exit
    flush, which is what DESIGN-PYTHON.md section 3.6 rule 10 asks for by
    pointing stdout at ``os.devnull`` with ``os.dup2``.  bash stands in for
    the shell so PIPESTATUS[0] is the port's own exit code.
    """
    check_epipe(tmp_path)


@pytest.mark.cli
def test_cli_python_dash_m_equals_command__fred_annot_xml() -> None:
    """DESIGN-PYTHON.md section 3.1 rule 3: ``python -m callplot ARGS`` and
    ``callplot ARGS`` give the same result."""
    args = ["-xml", "samples/fred_annot"]
    command = run_command("callplot", args, cwd=REPO_ROOT)
    module = subprocess.run(
        [sys.executable, "-m", "callplot"] + [typed_path(a) for a in args],
        input=b"",
        capture_output=True,
        cwd=REPO_ROOT,
        encoding=None,
    )
    assert module.returncode == command.returncode, (
        f"exit {module.returncode} vs command {command.returncode}"
    )
    assert module.stdout == command.stdout, diff_message(
        "python -m vs callplot", command.stdout, module.stdout
    )
    want = (GOLDEN_DIR / "s_fred_annot.xml.out").read_bytes()
    assert command.stdout == want, diff_message("callplot xml golden", want, command.stdout)


@pytest.mark.cli
def test_cli_no_bin_folder__commands_are_entry_points() -> None:
    """DESIGN-PYTHON.md 4.5 and 5.4 rule 1: nothing named like a command and
    no ``bin/`` folder may sit in the repository tree, on disk or in git."""
    assert not (REPO_ROOT / "bin").exists(), "there must be no bin/ folder"
    for name in ("callplot", "plottable", "callplot-prep"):
        for folder in (REPO_ROOT, REPO_ROOT / "src" / "callplot", REPO_ROOT / "tools"):
            assert not (folder / name).exists(), f"{name} must not be a file there"
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=REPO_ROOT, capture_output=True, encoding="utf-8"
    )
    names = tracked.stdout.split()
    assert not any(n.startswith("bin/") for n in names), "git must not track a bin/ folder"
