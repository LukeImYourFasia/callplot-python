#!/usr/bin/env python3
"""The plottable command (DESIGN.md section 3.13: the 2008 plottable.sh).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

plottable [-debug] [-style style] {input_file}

The script ran java -jar callplot.jar -xml, then Xalan with ${style}.xsl.
This port runs the same pipeline without a shell: -xml into memory, then
the matching table style's own bytes (section 3.13 D8: the Xalan step is
folded into the style).  -debug keeps the XML intermediate as _x_<pid>.xml
in the current folder, like the script's _x_<$$>.xml.  Unknown style: the
script died inside Xalan finding no ${style}.xsl; here it is an error plus
exit 1 (section 3.13.5).
"""

import errno
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from callplot import plotFlow
from callplot.constants import MODES
from callplot.context import RunContext
from callplot.out import Out
from callplot.render.table.index import TABLE_STYLES

# The script's usage block: the 12 echo lines of plottable.sh, $0 replaced
# by "plottable"; line 5 ends with one space (section 4.4, the hand-pinned
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


def usage():
    # echo, so stdout
    writeAll(1, "".join(line + "\n" for line in USAGE).encode("utf-8"))


def main():
    # the script's positional checks: -debug first if used, then -style
    args = sys.argv[1:]
    doingDebug = False
    if len(args) > 0 and args[0] == "-debug":
        doingDebug = True
        args = args[1:]
    style = "archtable"
    if len(args) > 0 and args[0] == "-style":
        args = args[1:]
        style = args[0] if len(args) > 0 else ""
        args = args[1:]

    if len(args) != 1:
        usage()
        return 1  # the script's exit 1 after the usage block
    file = args[0]

    if style not in TABLE_STYLES:
        # section 3.13.5: unknown style: the script died inside Xalan,
        # finding no ${style}.xsl; here: an error plus exit 1
        writeAll(2, ("plottable: unknown table style: %s\n" % style).encode("utf-8"))
        return 1

    try:
        with open(file, "rb") as fh:
            text = fh.read().decode("utf-8")
    except OSError as err:
        writeAll(2, ("plottable: Error: %s\n" % err).encode("utf-8"))
        return 1

    if doingDebug:
        # _x_<pid>.xml in the current folder: the script used the shell's
        # $$, here it is the process pid (same side-output role)
        xmlOut = Out()
        try:
            plotFlow(text, xmlOut, MODES["XML"])
        except Exception as err:
            writeAll(2, ("plottable: %s: %s\n" % (type(err).__name__, err)).encode("utf-8"))
            return 1
        xname = "_x_%d.xml" % os.getpid()
        with open(xname, "w", encoding="utf-8") as fh:
            fh.write(xmlOut.toString())
        writeAll(2, ("retaining xml intermediate file in %s\n" % xname).encode("utf-8"))

    out = Out()
    try:
        plotFlow(text, out, MODES["TABLE"], RunContext(), {"tableStyle": style})
    except Exception as err:
        writeAll(2, ("plottable: %s: %s\n" % (type(err).__name__, err)).encode("utf-8"))
        return 1
    writeAll(1, out.toString().encode("utf-8"))  # cat ${TMP}
    return 0


try:
    rc = main()
except EpipeError:
    rc = 0
sys.exit(rc)
