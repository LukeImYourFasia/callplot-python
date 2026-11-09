"""The ``callplot-prep`` command (DESIGN.md section 3.14; awk -f prep.awk).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

callplot-prep [--links] [--debug-file PATH] [file | -]

The flags are ordinary options, so this command uses argparse (DESIGN-PYTHON.md
section 3.6): ``--links`` is the awk's ``LINKS=y``, ``--debug-file`` is where
the awk's ``>> debug`` lines land, and one optional file argument defaults to
``-`` (stdin).  The awk script appended those lines to a file literally named
"debug"; this port writes them only where ``--debug-file`` pointed (DESIGN.md
section 3.14.4, an Appendix B erratum of the original).

Deliberate difference, already in Appendix B: a bad option makes argparse exit
2, where the JS ``callplot-prep`` exited 1.
"""

import argparse
import os
import pathlib
import sys
import traceback
from collections.abc import Sequence

from callplot.errors import CallplotError
from callplot.trace_prep import prep, prep_debug


def write_out(text: str) -> None:
    """Section 3.2: bytes to stdout, flushed (the awk's own print order)."""
    sys.stdout.buffer.write(text.encode("utf-8", "replace"))
    sys.stdout.buffer.flush()


def write_err(text: str) -> None:
    sys.stderr.write(text)
    sys.stderr.flush()


def main(argv: Sequence[str] | None = None) -> int:
    """The ``callplot-prep`` command; returns the exit code (section 2.1)."""
    parser = argparse.ArgumentParser(prog="callplot-prep")
    parser.add_argument(
        "--links",
        action="store_true",
        help="keep the trace's links (the awk's LINKS=y)",
    )
    parser.add_argument(
        "--debug-file",
        metavar="PATH",
        default=None,
        help="write the converter's debug lines here (the awk wrote them to a file named debug)",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default="-",
        help="the packet trace to read, or - for stdin (the default)",
    )
    args = parser.parse_args(list(argv) if argv is not None else sys.argv[1:])

    # section 2.5: one try for the command; the core catches nothing
    try:
        if args.file == "-":
            text = sys.stdin.buffer.read().decode("utf-8", "replace")
        else:
            text = pathlib.Path(args.file).read_bytes().decode("utf-8", "replace")

        debug: list[str] = []
        if args.debug_file is None:
            out = prep(text, links=args.links)
        else:
            # the command, not the core, decides where the debug lines go
            # (section 3.8 rule 6)
            out, debug = prep_debug(text, links=args.links)

        write_out(out)

        if args.debug_file is not None:
            # append, like the awk's ">> debug": repeated runs add lines
            with open(args.debug_file, "a", encoding="utf-8") as sink:
                sink.writelines(line + "\n" for line in debug)
        return 0
    except KeyboardInterrupt:
        return 130
    except BrokenPipeError:
        # the reader hung up: quiet exit 0 (DESIGN.md section 4.4)
        with open(os.devnull, "w") as sink:
            os.dup2(sink.fileno(), sys.stdout.fileno())
        return 0
    except OSError as err:
        write_err(f"callplot-prep: {args.file}: {err.strerror}\n")
        return 1
    except CallplotError as err:
        write_err(f"callplot-prep: {err.name}: {err}\n")
        return 1
    except Exception:  # section 3.6 rule 8: programmer error
        traceback.print_exc()
        write_err("callplot-prep: internal error, please report it\n")
        return 1
