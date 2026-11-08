#!/usr/bin/env python3
"""The callplot-prep command (DESIGN.md section 3.14: awk -f prep.awk).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

callplot-prep [--links] [--debug-file path] [file | -]

--links is the awk's LINKS=y; with no file or with -, it reads stdin.  The
awk script appends its debug lines to a file literally named "debug"; this
port writes them only where --debug-file pointed (section 3.14.4, an
Appendix B erratum of the original).
"""

import errno
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from callplot.prep import prep


class EpipeError(Exception):
    """the write sentinel: the pipe reader hung up (section 4.4)"""


def writeAll(fd, data):
    off = 0
    try:
        while off < len(data):
            off += os.write(fd, data[off:])
    except OSError as err:
        if err.errno == errno.EPIPE:
            raise EpipeError("pipe closed")
        raise


def main():
    links = False
    debugFile = None
    input = None  # file argument; "-" or absent means stdin

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--links":
            links = True
        elif arg == "--debug-file":
            i += 1
            if i >= len(args):
                writeAll(2, b"callplot-prep: --debug-file needs a path\n")
                return 1
            debugFile = args[i]
        elif input is None:
            input = arg
        else:
            writeAll(2, ("callplot-prep: too many arguments: %s\n" % arg).encode("utf-8"))
            return 1
        i += 1

    if input is None or input == "-":
        text = sys.stdin.buffer.read().decode("utf-8")
    else:
        try:
            with open(input, "rb") as fh:
                text = fh.read().decode("utf-8")
        except OSError as err:
            writeAll(2, ("callplot-prep: Error: %s\n" % err).encode("utf-8"))
            return 1

    r = prep(text, {"links": links})
    writeAll(1, r["out"].encode("utf-8"))

    if debugFile is not None:
        # section 3.14.4: only here do the awk debug lines go to a file
        with open(debugFile, "a", encoding="utf-8") as fh:
            fh.write("".join(line + "\n" for line in r["debug"]))
    return 0


try:
    rc = main()
except EpipeError:
    rc = 0
sys.exit(rc)
