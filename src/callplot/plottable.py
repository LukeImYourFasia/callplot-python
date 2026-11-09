"""The ``plottable`` command (DESIGN.md sections 3.13 and 3.13.5; the 2008
plottable.sh shell script).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

plottable [-debug] [-style style] {input_file}

The script ran ``java -jar callplot.jar -xml`` and then Xalan with
``${style}.xsl``.  This port runs the same pipeline without a shell: the XML
step in memory, then the matching table style's own bytes (DESIGN.md section
3.13 D8: the Xalan step is folded into the style, so the table comes
straight from ``render(text, Mode.TABLE, options=...)``).  ``-debug`` keeps the
XML intermediate as ``_x_<pid>.xml`` in the current folder, like the script's
``_x_<$$>.xml``.  An unknown style: the script died inside Xalan finding no
``${style}.xsl``; here it is an error plus exit 1 (section 3.13.5).

DESIGN-PYTHON.md section 3.6: the command is an entry point, ``main()``
returns the exit code, and the option scan is a hand-written loop because the
script's own order matters (``-debug`` first, then ``-style``, then exactly one
file).
"""

import os
import pathlib
import sys
import traceback
from collections.abc import Sequence

from callplot.api import render
from callplot.constants import Mode
from callplot.errors import CallplotError
from callplot.options import RenderOptions, parse_table_style

# The script's usage block: the 12 echo lines of plottable.sh, $0 replaced by
# "plottable"; line 5 ends with one space (DESIGN.md section 4.4, the hand-pinned
# test/cli/plottable_usage.expected).
USAGE = [
    "usage: plottable [-debug] [-style style] {input_file}",
    "",
    "-debug retains the intermediate files for debugging",
    "",
    "The annotations can be added by putting ",
    "one or more lines beginning with ! after the message",
    "",
    "examples:",
    "a->b/MESSAGE",
    "!This is a very interesting message",
    "!Since it's going from a to b",
    "",
]


def write_out(text: str) -> None:
    """Bytes to stdout, flushed (section 3.2; the script's ``cat ${TMP}``)."""
    sys.stdout.buffer.write(text.encode("utf-8", "replace"))
    sys.stdout.buffer.flush()


def write_err(text: str) -> None:
    sys.stderr.write(text)
    sys.stderr.flush()


def usage() -> None:
    """The script echoed the usage, so it goes to stdout (section 3.13.5)."""
    write_out("\n".join(USAGE) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    """The ``plottable`` command; returns the exit code (DESIGN-PYTHON.md 2.1)."""
    args = list(sys.argv[1:]) if argv is None else list(argv)

    # the script's positional checks in order: -debug first if used, then
    # -style NAME, then exactly one file
    doing_debug = False
    if len(args) > 0 and args[0] == "-debug":
        doing_debug = True
        args = args[1:]
    style_name = "archtable"
    if len(args) > 0 and args[0] == "-style":
        args = args[1:]
        style_name = args[0] if len(args) > 0 else ""
        args = args[1:]

    if len(args) != 1:
        usage()
        return 1  # the script's exit 1 after the usage block
    file = args[0]

    try:
        style = parse_table_style(style_name)
    except CallplotError:
        # section 3.13.5: the script died in Xalan finding no ${style}.xsl
        write_err(f"plottable: unknown table style: {style_name}\n")
        return 1

    try:
        text = pathlib.Path(file).read_bytes().decode("utf-8", "replace")
    except OSError as err:
        write_err(f"plottable: {file}: {err.strerror}\n")
        return 1

    # section 3.6 rule 8: one handler for the command
    try:
        if doing_debug:
            # _x_<pid>.xml: the script used the shell's $$, this port the
            # process pid (same side-output role)
            xml = render(text, Mode.XML)
            name = f"_x_{os.getpid()}.xml"
            try:
                pathlib.Path(name).write_bytes(xml.encode("utf-8", "replace"))
            except OSError as err:
                write_err(f"plottable: {name}: {err.strerror}\n")
                return 1
            write_err(f"retaining xml intermediate file in {name}\n")

        table = render(
            text,
            Mode.TABLE,
            options=RenderOptions(table_style=style),
        )
        write_out(table)
        return 0
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:
        # the reader hung up the pipe: quiet exit 0 (DESIGN.md section 4.4)
        with open(os.devnull, "w") as sink:
            os.dup2(sink.fileno(), sys.stdout.fileno())
        return 0
    except CallplotError as err:
        write_err(f"plottable: {err.name}: {err}\n")
        return 1
    except OSError as err:
        # a side file or stdout that cannot be written (a closed pipe is
        # handled above)
        write_err(f"plottable: {err.strerror}\n")
        return 1
    except Exception:  # section 3.6 rule 8: programmer error
        traceback.print_exc()
        write_err("plottable: internal error, please report it\n")
        return 1
