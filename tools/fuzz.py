#!/usr/bin/env python3
"""Fuzz runner (DESIGN.md section 4.5).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Seeded cases through the oracle harness pool (4.5.1) and through the
Python port, in the 7 core modes.  Compare stdout bytes and exit codes;
when java exits non-zero, compare only the exit code (4.5 rule 5).  Save
the first 50 diffs as fixtures (4.5 rule 6); their goldens come later from
the gen-golden tooling, one process per run, never from the harness.
Timeout: no RESULT in 5 s -> the harness process is SIGKILLed, the case
records exit 124, and a new process starts (pool.py, 5.3.1 W19e).

Usage: tools/fuzz.py --seed <n> --count <n>
Exit: 2 on a usage error, 1 when any diff was found, 0 otherwise.
"""

import os
import sys
import time

sys.path.insert(0, os.path.join("tools", "oracle"))
sys.path.insert(0, "src")

from cases import genCases
from pool import runHarnessTasks

from callplot import plotFlow
from callplot.constants import MODES
from callplot.context import RunContext
from callplot.index import RendererNotPortedError
from callplot.out import Out

CORE_MODES = [
    ["text", "text", MODES["TEXT"]],
    ["pic", "-pic", MODES["PIC"]],
    ["xml", "-xml", MODES["XML"]],
    ["svg", "-svg", MODES["SVG"]],
    ["vml", "-vml", MODES["VML"]],
    ["vxml", "-vxml", MODES["VML"] | MODES["XML"]],
    ["graffle", "-graffle", MODES["GRAFFLE"]],
]


def pyRender(bit, text):
    """Run one case through the Python port.  A throw models exit 1 (3.7)."""
    out = Out()
    try:
        plotFlow(text, out, bit, RunContext(), {})
        return {"exitCode": 0, "stdout": out.toString().encode("utf-8")}
    except RendererNotPortedError:
        raise  # a renderer that has not landed is a programmer error
    except Exception:
        return {"exitCode": 1, "stdout": b""}


def main():
    seed = None
    count = None
    argv = sys.argv[1:]
    for i in range(len(argv) - 1):
        if argv[i] == "--seed":
            try:
                seed = int(argv[i + 1])
            except ValueError:
                seed = None
        elif argv[i] == "--count":
            try:
                count = int(argv[i + 1])
            except ValueError:
                count = None
    if seed is None or count is None or count < 1:
        sys.stderr.write("usage: tools/fuzz.py --seed <n> --count <n>\n")
        return 2

    t0 = time.monotonic()
    print("fuzz: seed %d, count %d, modes %d" % (seed, count, len(CORE_MODES)))

    cases = genCases(seed, count)
    tasks = []
    for c, case in enumerate(cases):
        for mode, flag, _bit in CORE_MODES:
            tasks.append({"key": "%d.%s" % (c, mode), "flag": flag,
                          "input": case})
    harness = runHarnessTasks("reference/build",
                              "com.dynamicsoft.callplot.Main", tasks,
                              clients=8, timeoutSec=5.0)

    # Compare each case x mode: harness oracle vs Python port.
    diffs = []
    groups = {}
    for c, case in enumerate(cases):
        text = case.decode("utf-8", "replace")  # JS Buffer.toString("utf8")
        for mode, flag, bit in CORE_MODES:
            h = harness.get("%d.%s" % (c, mode))
            if h is None:
                diffs.append({"c": c, "mode": mode, "why": "no harness result"})
                continue
            j = pyRender(bit, text)
            why = None
            if h["exitCode"] != j["exitCode"]:
                why = "exit %d vs py %d" % (h["exitCode"], j["exitCode"])
            elif h["exitCode"] == 0 and h["stdout"] != j["stdout"]:
                n = min(len(h["stdout"]), len(j["stdout"]))
                b = 0
                while b < n and h["stdout"][b] == j["stdout"][b]:
                    b += 1
                head = h["stdout"][0:b].decode("latin1")
                line = head.count("\n") + 1  # JS head.split("\n").length
                why = ("byte diff at %d (line %d, %d vs %d bytes)"
                       % (b, line, len(h["stdout"]), len(j["stdout"])))
            if why is not None:
                diffs.append({"c": c, "mode": mode, "why": why})
                group = "%s|%s" % (mode, why.split("(")[0].strip())
                groups[group] = groups.get(group, 0) + 1

    # 4.5 rule 6: save the first 50 diffs as fixtures.
    saved = 0
    if diffs:
        os.makedirs("test/fixtures/fuzz", exist_ok=True)
        for d in diffs:
            if saved >= 50:
                break
            path = "test/fixtures/fuzz/seed%d_case%d" % (seed, d["c"])
            if not os.path.exists(path):
                with open(path, "wb") as fh:
                    fh.write(cases[d["c"]])
                saved += 1

    secs = time.monotonic() - t0
    print("cases: %d, runs: %d, diffs: %d, fixtures saved: %d"
          % (count, len(tasks), len(diffs), saved))
    print("time: %.1f s" % secs)
    if diffs:
        print("diff groups (mode | first cause | count):")
        top = sorted(groups.items(), key=lambda kv: -kv[1])[:20]
        for g, n in top:
            print("  %s = %d" % (g, n))
        print("first diff cases:")
        for d in diffs[:20]:
            print("  case %d %s: %s" % (d["c"], d["mode"], d["why"]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
