"""The ``callplot`` command (DESIGN.md section 3.7, DESIGN-PYTHON.md sections
2.1, 3.1 and 3.6; Main.java:37-160).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

The command is an entry point (``[project.scripts] callplot = "callplot.cli:main"``),
not a file a person runs by path: there is no ``bin/`` folder (DESIGN-PYTHON.md
section 5.4 rule 1).  ``main()`` returns the exit code, and the small wrapper
``pip`` writes calls ``sys.exit(main())`` (DESIGN-PYTHON.md section 2.1).

Args are read left to right by a hand-written loop, never with argparse
(section 3.6 rule 1): a mode flag affects only the files after it, a ``--help``
after a file must keep the earlier output, and ``-table=style`` is one token.
One ``RunContext`` is made for the run and passed to every ``render()`` call,
so the Graffle ids and the stagger alternation carry across files like the
Java statics (section 3.6 rule 2).  Bytes in, bytes out (section 3.2): read
with ``read_bytes`` plus ``decode("utf-8", "replace")``, write to
``sys.stdout.buffer``.

DESIGN-PYTHON.md replaces the JS port's PrintWriter model here: ``render()``
builds the whole output in memory and returns it, or raises before returning
anything, so the 8192-byte partial-flush rule of DESIGN.md section 4.4 cannot
apply (logged in docs/appendix-b.md).
"""

import os
import pathlib
import sys
import traceback
from collections.abc import Sequence

from callplot.api import render
from callplot.constants import Mode
from callplot.context import RunContext
from callplot.errors import CallplotError
from callplot.options import HtmlLayout, RenderOptions, parse_table_style

# Section 3.6 rule 5: the usage text is the verbatim text of Main.java:79-159
# (wrong defaults and tabs kept as they are), then the block for the new
# flags.  Tests never compare stderr (DESIGN.md section 4.4), but the text is
# pinned here so a person reading --help sees what the tool accepts.
USAGE = [
    "Usage: callplot [-?|--help] [-pic|-vml|-svg|-xml|-graffle] {-|file}",
    "",
    " -? --help: print this help",
    " -pic: format output for pic(1), not as ASCII-art.",
    " -svg: format output as Scalable Vector Graphics",
    " -vml: format output as Vector Markup Language for IE and MS Office.",
    " -xml: format output as XML.",
    " -vxml: format output as XML, but with a VML plot.",
    " -graffle: format output as OmniGraffle v5 XML.",
    "",
    "File Format:",
    "opt/name/value          // set option 'name' to value 'value'",
    "",
    "guy/alias/label         // declare an entity with nickname 'alias' and label 'label'",
    "",
    "x->y/Caption            // declare a message from the entity with nickname 'x' to ",
    "                        // the entity with nickname 'y' with the label 'caption'",
    "                        // to include forward slashes, escape them (e.g. '\\/')",
    "",
    "x->y/cap1/cap2          // declare a message from the entity with nickname 'x' to ",
    "                        // the entity with nickname 'y' with the label 'cap1'",
    "                        // followed by a response in the reverse direction with",
    "                        // caption 'cap2'",
    "",
    "x..y/Caption            // draw an undirected dotted line from the entity with ",
    "                        // nickname 'x' to the entity with nickname 'y' with ",
    "                        // the label 'caption'",
    "",
    "x--y/Caption            // draw an undirected dotted line from the entity with ",
    "                        // nickname 'x' to the entity with nickname 'y' with ",
    "                        // the label 'caption' shown for each entity line in graffle format",
    "",
    "note/x/Text             // Draw the text to the right of the line for entity 'x'",
    "",
    "The captions and note test can be broken across lines with ^",
    "(caret). In this case, the last line is drawn above the arrow, the",
    "next to last line above that, and so on.",
    "",
    "These are the options that exist now:",
    "",
    "opt/startLine/{integer}            // initial line # for messages",
    "",
    "opt/startColumn/{integer}          // leftmost column for entities",
    "",
    "opt/linePitch/{integer}            // # of lines between messages",
    "",
    "opt/columnPitch/{integer}          // # of cols between entities",
    "",
    "opt/topLabel/{boolean}             // label entities at top?",
    "",
    "opt/bottomLabel/{boolean}          // label entities at bottom?",
    "",
    "opt/messageNumbering/{boolean}     // number messages in '(#) text' format?",
    "",
    "opt/noteNumbering/{boolean}        // number notes as well as messages?",
    "",
    "opt/crunch/{boolean}               // elide lines that would have been just space and ",
    "\t\t\t\t   // vertical bars (ascii-art only)",
    "opt/stagger/{boolean}               // stagger the boxes to allow longer labels ",
    "",
    "opt/vmlStyle/{string}\t\t   // re-define the line style for VML output",
    "default:: Weight='2pt'",
    "",
    "opt/vmlArrowStyle/{string}         // re-define the arrow style for VML output",
    "default: EndArrow='Open'",
    "",
    "opt/vmlDottedStyle/{string}\t   // re-define the dotted line style for VML output",
    "default: DashStyle='dot'",
    "",
    "opt/vmlTextStyle/{string}\t   // re-define the text style for VML output",
    "default: style='font:normal normal normal 9pt Courier'",
    "",
    "opt/vmlBoxStyle/{string}\t   // re-define the style applied to the rectangle",
    "default: fillcolor='red'\t   // at the top of each column ",
    "",
    "opt/vmlBoxWidthPercentage/{integer} // re-define the %-age of the column filled by ",
    "default: 85\t\t\t    // the rectangle at the top of a column",
    "",
    "boolean options accept 'on', 'true' and 'yes' as meaning true, and their opposites as false.",
    "",
    "New flags in this port:",
    "",
    " -table: format output as one of the legacy plottable tables.",
    " -table=<style>: pick the style: archtable htmltable tmltable "
    "htmltable2 htmltable3 nolinks wordtable.",
    " -mermaid: format output as Mermaid sequence-diagram text.",
    " -plantuml: format output as PlantUML sequence-diagram text.",
    " -html: format output as a self-contained HTML page "
    "(layout from opt/htmlLayout, else topbottom).",
    " -html=<layout>: force the page layout: topbottom or sidebyside.",
]


def write_out(data: bytes) -> None:
    """Section 3.2 and DESIGN.md Main.java:74: bytes to stdout, flushed."""
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def write_err(text: str) -> None:
    """Section 3.6 rule 7 and 11: stderr lines, flushed as they are written."""
    sys.stderr.write(text)
    sys.stderr.flush()


def usage() -> None:
    """The usage text goes to stderr (section 3.6 rule 5)."""
    write_err("\n".join(USAGE) + "\n")


def drain_err(ctx: RunContext, written: int) -> int:
    """Section 3.6 rule 11: the Graffle ``--`` debug lines live in ``ctx.err``
    (the shared System.err buffer); print what is new since the last file and
    return the new mark."""
    pending = ctx.err.getvalue()
    if len(pending) > written:
        write_err(pending[written:])
    return len(pending)


def main(argv: Sequence[str] | None = None) -> int:
    """The ``callplot`` command; returns the exit code (section 2.1)."""
    args = list(sys.argv[1:]) if argv is None else list(argv)
    if len(args) == 0:
        usage()  # Main.java:41-44: no arguments, usage, exit 1
        return 1

    mode = Mode.TEXT
    ctx = RunContext()  # one for the whole run (section 3.6 rule 2)
    options = RenderOptions()  # flags fill table_style and html_layout
    err_mark = 0  # what ctx.err has already been printed

    # section 3.6 rule 8: one try for the command; the core catches nothing
    try:
        for arg in args:
            if arg == "-pic":
                mode = Mode.PIC
                continue
            if arg == "-svg":
                mode = Mode.SVG
                continue
            if arg == "-vml":
                mode = Mode.VML
                continue
            if arg == "-xml":
                mode = Mode.XML
                continue
            if arg == "-vxml":
                mode = Mode.VXML
                continue
            if arg == "-graffle":
                mode = Mode.GRAFFLE
                continue
            if arg == "-mermaid":
                mode = Mode.MERMAID
                continue
            if arg == "-plantuml":
                mode = Mode.PLANTUML
                continue
            if arg == "-table":
                mode = Mode.TABLE
                options = RenderOptions(table_style=parse_table_style("archtable"))
                continue
            if arg.startswith("-table="):
                mode = Mode.TABLE
                name = arg[len("-table=") :]
                try:
                    style = parse_table_style(name)
                except CallplotError:
                    # section 3.13.5: an unknown style is a CLI error, exit 1
                    write_err(f"callplot: unknown table style: {name}\n")
                    return 1
                options = RenderOptions(table_style=style)
                continue
            if arg == "-html":
                mode = Mode.HTML
                # the flag alone clears any earlier force: the layout comes
                # from the input file (DESIGN.md section 3.12.6)
                options = RenderOptions()
                continue
            if arg.startswith("-html="):
                mode = Mode.HTML
                name = arg[len("-html=") :]
                if name == HtmlLayout.TOPBOTTOM.value:
                    options = RenderOptions(html_layout=HtmlLayout.TOPBOTTOM)
                elif name == HtmlLayout.SIDEBYSIDE.value:
                    options = RenderOptions(html_layout=HtmlLayout.SIDEBYSIDE)
                else:
                    write_err(f"callplot: unknown html layout: {name}\n")
                    return 1
                continue
            if arg == "-?" or arg == "--help":
                usage()  # Main.java:64-66: the run stops here, exit 0
                return 0

            if arg == "-":
                text = sys.stdin.buffer.read().decode("utf-8", "replace")
            else:
                text = pathlib.Path(arg).read_bytes().decode("utf-8", "replace")

            out = render(text, mode, ctx=ctx, options=options)
            write_out(out.encode("utf-8", "replace"))
            err_mark = drain_err(ctx, err_mark)
        return 0
    except KeyboardInterrupt:
        return 130  # section 3.6 rule 9: no traceback
    except BrokenPipeError:
        # section 3.6 rule 10: the reader hung up the pipe (callplot big |
        # head).  Point stdout at os.devnull so Python's own exit flush stays
        # quiet, and exit 0 with nothing on stderr.
        with open(os.devnull, "w") as sink:
            os.dup2(sink.fileno(), sys.stdout.fileno())
        return 0
    except OSError as err:
        # section 3.6 rule 7: a file that cannot be read prints and exits 1
        write_err(f"callplot: {arg}: {err.strerror}\n")
        drain_err(ctx, err_mark)
        return 1
    except CallplotError as err:
        # section 3.6 rules 7 and 11: name the error instead of dumping the
        # JVM stack trace the original would have printed
        write_err(f"callplot: {err.name}: {err}\n")
        drain_err(ctx, err_mark)
        return 1
    except Exception:  # section 3.6 rule 8: programmer error
        traceback.print_exc()
        write_err("callplot: internal error, please report it\n")
        return 1
