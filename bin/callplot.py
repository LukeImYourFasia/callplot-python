#!/usr/bin/env python3
"""The callplot command (DESIGN.md section 3.7, Main.java:37-160).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Args are read left to right; a mode flag affects only the files after it.
Each file's output goes to stdout as soon as that file is done, through the
8192-byte PrintWriter model (section 4.4): a crashed run never reaches the
final flush, so only whole buffer loads escape.  On any error the port
prints `callplot: <ErrorName>: <message>` to stderr and exits 1 (the real
JVM dumps a stack trace; section 3.7 allows naming the error instead, and
the tests never compare stderr).  A closed pipe exits 0 silently (section
4.4 epipe case).
"""

import errno
import os
import sys

# The pure package: bin/ holds only entry points (DESIGN.md section 2.5).
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "src"))

from callplot import plotFlow
from callplot.constants import MODES
from callplot.index import RendererNotPortedError
from callplot.context import RunContext
from callplot.out import Out, Err
from callplot.render.table.index import TABLE_STYLES

# Section 3.7: the usage text is the exact text of Main.java:79-159 (wrong
# defaults and tabs included), then one block listing the new flags.  The
# list below is the verbatim transcription; tests do not compare stderr.
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
  " -table=<style>: pick the style: archtable htmltable tmltable htmltable2 htmltable3 nolinks wordtable.",
  " -mermaid: format output as Mermaid sequence-diagram text.",
  " -plantuml: format output as PlantUML sequence-diagram text.",
  " -html: format output as a self-contained HTML page (layout from opt/htmlLayout, else topbottom).",
  " -html=<layout>: force the page layout: topbottom or sidebyside.",
]


class EpipeError(Exception):
    """the write sentinel: the reader hung up the pipe (section 4.4)"""


def writeAll(fd, data):
    """Synchronous fd writes: the exit code must not race pending writes,
    and a closed pipe unwinds the run with the sentinel (JS used fs.writeSync
    for the same reason)."""
    off = 0
    try:
        while off < len(data):
            off += os.write(fd, data[off:])
    except OSError as err:
        if err.errno == errno.EPIPE:
            raise EpipeError("pipe closed")
        raise


def usage():
    writeAll(2, ("".join(line + "\n" for line in USAGE)).encode("utf-8"))


def errLine(text):
    writeAll(2, text.encode("utf-8"))


# Java: PrintWriter out over a BufferedWriter with an 8192-byte buffer
# (Main.java:72); only whole buffer loads leave before out.flush()
# (Main.java:74), and a crashed run never reaches that flush.
FLUSH_BYTES = 8192


def emit(out, crashed):
    data = out.toString().encode("utf-8")
    if crashed:
        data = data[0:(len(data) // FLUSH_BYTES) * FLUSH_BYTES]
    writeAll(1, data)


def main():
    args = sys.argv[1:]
    if len(args) == 0:
        usage()  # Main.java:41-44
        return 1

    mode = MODES["TEXT"]
    ctx = RunContext()  # section 3.6: statics persist across files
    opts = {}  # one per run; flags write the values when read
    errWritten = 0  # ctx.err is System.err: flushed after each file

    for arg in args:
        if arg == "-pic":
            mode = MODES["PIC"]
            continue
        elif arg == "-xml":
            mode = MODES["XML"]
            continue
        elif arg == "-vml":
            mode = MODES["VML"]
            continue
        elif arg == "-svg":
            mode = MODES["SVG"]
            continue
        elif arg == "-vxml":
            mode = MODES["VML"] | MODES["XML"]
            continue
        elif arg == "-graffle":
            mode = MODES["GRAFFLE"]
            continue
        elif arg == "-table":
            mode = MODES["TABLE"]
            opts["tableStyle"] = "archtable"
            continue
        elif arg.startswith("-table="):
            mode = MODES["TABLE"]
            style = arg[len("-table="):]
            if style not in TABLE_STYLES:
                # section 3.7: an unknown style is a CLI error, exit 1
                errLine("callplot: unknown table style: %s\n" % style)
                return 1
            opts["tableStyle"] = style
            continue
        elif arg == "-mermaid":
            mode = MODES["MERMAID"]
            continue
        elif arg == "-plantuml":
            mode = MODES["PLANTUML"]
            continue
        elif arg == "-html":
            mode = MODES["HTML"]
            opts["htmlLayout"] = None  # layout comes from the input file
            continue
        elif arg.startswith("-html="):
            mode = MODES["HTML"]
            layout = arg[len("-html="):]
            if layout != "topbottom" and layout != "sidebyside":
                errLine("callplot: unknown html layout: %s\n" % layout)
                return 1
            opts["htmlLayout"] = layout  # the flag forces it (3.12.6)
            continue
        elif arg == "-?" or arg == "--help":
            usage()  # Main.java:64-66: exits 0 at this point
            return 0

        if arg == "-":
            text = sys.stdin.buffer.read().decode("utf-8")  # Main.java:67-68
        else:
            try:
                with open(arg, "rb") as fh:
                    text = fh.read().decode("utf-8")  # Main.java:69-70
            except OSError as err:
                # section 3.7: an unreadable file also gives exit 1
                errLine("callplot: Error: %s\n" % err)
                return 1

        out = Out()  # Main.java:72: a fresh PrintWriter per file
        crashed = False
        try:
            plotFlow(text, out, mode, ctx, opts)
        except RendererNotPortedError:
            raise  # a renderer that has not landed is a programmer error
        except Exception as err:
            crashed = True  # Main has no catch: the JVM would exit 1
            # section 3.7: name the error instead of dumping a stack trace
            errLine("callplot: %s: %s\n" % (type(err).__name__, err))
        emit(out, crashed)  # Main.java:74: out.flush()

        # section 3.7: graffle `--` debug lines go to stderr (they live in
        # ctx.err, the shared System.err buffer; flush what is new since the
        # last file)
        pending = ctx.err.toString()
        writeAll(2, pending[errWritten:].encode("utf-8"))
        errWritten = len(pending)

        if crashed:
            return 1
    return 0


try:
    rc = main()
except EpipeError:
    rc = 0  # the pipe reader hung up: silent exit 0, empty stderr
sys.exit(rc)
