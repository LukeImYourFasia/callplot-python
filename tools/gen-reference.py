#!/usr/bin/env python3
"""Regenerate samples/reference (DESIGN.md 4.10, the refs gate).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Compatible outputs come from the oracle: one JVM per run (the JS repo's
tools/jref.sh invocation inlined; this repo has no jref script) for the
7 core modes, and the plottable pipeline for the 6 legacy table styles
(jref -xml, then Xalan over the archive's .xsl files) exactly as the
gen-golden-extra pipeline builds goldens.  New outputs are byte copies
of the approved snapshots under test/snapshots.  trace_sip has no
fixture and no snapshot: its .msd comes from the archive's prep.awk
(fresh temp dir: the 0.2 awk drops a debug file in the cwd), its 4 new
outputs are rendered by the port from that msd, and the raw .trace is
copied next to it.  Never touches goldens, snapshots, or the oracle's
Java.
"""

import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, "src")

from callplot import plotFlow
from callplot.constants import MODES
from callplot.context import RunContext
from callplot.out import Out

ROOT = os.getcwd()
LIBDIR = "reference/callplotwithextra/callplot/lib"
XALAN_CP = ":".join(os.path.join(LIBDIR, jar)
                   for jar in ("xalan.jar", "xml-apis.jar", "xercesImpl.jar"))

# 7 core outputs: extension -> jref args.  Text mode gets no flag (3.7).
CORE_MODES = [
    ["txt", []],
    ["pic", ["-pic"]],
    ["xml", ["-xml"]],
    ["vml.html", ["-vml"]],
    ["vxml.html", ["-vxml"]],
    ["svg", ["-svg"]],
    ["graffle", ["-graffle"]],
]
# the port's htmltable is the archive's tmltable.xsl (3.13.2)
TABLE_STYLES = ["archtable", "htmltable", "htmltable2", "htmltable3",
                "nolinks", "wordtable"]
NEW_MODES = [
    ["mmd", MODES["MERMAID"], {}],
    ["puml", MODES["PLANTUML"], {}],
    ["html-topbottom.html", MODES["HTML"], {"htmlLayout": "topbottom"}],
    ["html-sidebyside.html", MODES["HTML"], {"htmlLayout": "sidebyside"}],
]

# sample -> callplot input; fixture -> approved snapshots to copy from
SAMPLES = [
    {"name": "fred", "fixture": "s_fred", "input": "samples/fred"},
    {"name": "fred2", "fixture": "s_fred2", "input": "samples/fred2"},
    {"name": "fred_annot", "fixture": "s_fred_annot",
     "input": "samples/fred_annot"},
    {"name": "sip_annot", "fixture": "s_sip_annot", "input": "samples/sip_annot"},
    # trace_sip: the .msd is made from this .trace by the archive's prep.awk
    {"name": "trace_sip", "fixture": None, "input": None,
     "trace": "samples/trace_sip.trace"},
]

# the same encoding env as the oracle tooling
ENV = dict(os.environ)
ENV["LC_ALL"] = "en_US.UTF-8"
ENV["JAVA_TOOL_OPTIONS"] = "-Dfile.encoding=UTF-8"


def exec(name, args, cwd=None):
    """Run to completion; returns (code, stdout, stderr)."""
    r = subprocess.run([name] + args, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, cwd=cwd, env=ENV)
    return r.returncode, r.stdout, r.stderr


def execOk(name, args, what, cwd=None):
    """exec plus a loud failure on a non-zero exit; returns stdout bytes."""
    code, out, err = exec(name, args, cwd=cwd)
    if code != 0:
        raise SystemExit("%s: exit %s; stderr: %s"
                         % (what, code, err.decode("utf-8", "replace")))
    return out


def jrefOk(flagArgs, inputPath, what):
    """one JVM per run: the JS repo's tools/jref.sh invocation, inlined"""
    return execOk("java", ["-cp", "reference/build",
                           "com.dynamicsoft.callplot.Main"] + list(flagArgs)
                  + [inputPath], what)


def main():
    tmpRoot = tempfile.mkdtemp(prefix="gen-ref-", dir="/tmp/opencode")
    written = 0

    for sample in SAMPLES:
        dir = os.path.join("samples/reference", sample["name"])
        os.makedirs(dir, exist_ok=True)
        name = sample["name"]
        input = sample["input"]

        if sample.get("trace"):
            # .msd from awk: fresh temp dir (the 0.2 awk drops a debug file
            # in the cwd), then compare against the awk prep golden
            tmpd = tempfile.mkdtemp(prefix="awk-", dir=tmpRoot)
            code, msd, err = exec("/usr/bin/awk", ["-f", os.path.join(
                ROOT, LIBDIR, "prep.awk"), os.path.join(ROOT, sample["trace"])],
                cwd=tmpd)
            shutil.rmtree(tmpd, ignore_errors=True)
            if code != 0:
                raise SystemExit("prep awk %s: exit %s" % (name, code))
            golden = open("test/golden/trace_sip.prep.out", "rb").read()
            if msd != golden:
                raise SystemExit("prep drift: awk msd differs from "
                                 "test/golden/trace_sip.prep.out")
            with open(os.path.join(dir, "trace_sip.msd"), "wb") as fh:
                fh.write(msd)
            with open(os.path.join(dir, "trace_sip.trace"), "wb") as fh:
                fh.write(open(sample["trace"], "rb").read())
            input = os.path.join(dir, "trace_sip.msd")

        for ext, flagArgs in CORE_MODES:
            stdout = jrefOk(flagArgs, input, "jref %s %s" % (name, ext))
            with open(os.path.join(dir, "%s.%s" % (name, ext)), "wb") as fh:
                fh.write(stdout)
            written += 1

        # table styles: the plottable pipeline (jref -xml, then Xalan per
        # style; htmltable -> tmltable.xsl per 3.13.2)
        xmlPath = os.path.join(tmpRoot, "%s.xml" % name)
        xml = jrefOk(["-xml"], input, "jref -xml %s" % name)
        with open(xmlPath, "wb") as fh:
            fh.write(xml)
        for style in TABLE_STYLES:
            xsl = "tmltable.xsl" if style == "htmltable" else "%s.xsl" % style
            outPath = os.path.join(dir, "%s.table-%s.html" % (name, style))
            execOk("java", ["-cp", XALAN_CP, "org.apache.xalan.xslt.Process",
                            "-IN", xmlPath, "-XSL", os.path.join(ROOT, LIBDIR,
                                                                  xsl),
                            "-OUT", outPath],
                   "xalan %s %s" % (name, style))
            if not os.path.exists(outPath):
                open(outPath, "wb").close()
            written += 1
        os.remove(xmlPath)

        for ext, flag, opts in NEW_MODES:
            if sample["fixture"] is not None:
                src = os.path.join("test/snapshots",
                                   "%s.%s" % (sample["fixture"], ext))
                if not os.path.exists(src):
                    raise SystemExit("approved snapshot missing: " + src)
                with open(src, "rb") as fh:
                    data = fh.read()
            else:
                # trace_sip has no snapshot: render the new outputs here
                out = Out()
                plotFlow(open(input, encoding="utf-8").read(), out, flag,
                         RunContext(), opts)
                data = out.toString().encode("utf-8")
            with open(os.path.join(dir, "%s.%s" % (name, ext)), "wb") as fh:
                fh.write(data)
            written += 1

    if written != 85:
        raise SystemExit("expected 5 x 17 = 85 outputs, wrote %d" % written)

    # index.html: one row per sample, one column per output (4.10 rule 3);
    # fred and fred2 have no numbering, so their legacy-table cells say so
    # (4.10 rule 5)
    COLUMNS = ([c[0] for c in CORE_MODES]
                + ["table-%s.html" % s for s in TABLE_STYLES]
                + [m[0] for m in NEW_MODES])
    lines = []
    lines.append("<!doctype html>")
    lines.append('<html lang="en">')
    lines.append("<head><title>callplot reference samples</title></head>")
    lines.append("<body>")
    lines.append("<h1>callplot reference samples</h1>")
    lines.append("<p>Every output for every sample (section 4.10): "
                 "5 samples, 17 outputs each.</p>")
    lines.append("<table>")
    lines.append("<tr><th>Sample</th>" + "".join(
        "<th>%s</th>" % c for c in COLUMNS) + "</tr>")
    for sample in SAMPLES:
        name = sample["name"]
        noRows = name == "fred" or name == "fred2"
        cells = []
        for col in COLUMNS:
            file = "%s/%s.%s" % (name, name, col)
            cell = "<a href=\"%s\">%s.%s</a>" % (file, name, col)
            if noRows and col.startswith("table-"):
                cell += " (no numbered messages)"
            cells.append("<td>%s</td>" % cell)
        lines.append("<tr><td>%s</td>" % name + "".join(cells) + "</tr>")
    lines.append("</table>")
    lines.append("</body>")
    lines.append("</html>")
    with open("samples/reference/index.html", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    shutil.rmtree(tmpRoot, ignore_errors=True)
    print("wrote 85 outputs + trace_sip.trace + trace_sip.msd + "
          "index.html under samples/reference")
    return 0


if __name__ == "__main__":
    sys.exit(main())
