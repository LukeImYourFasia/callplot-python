#!/usr/bin/env python3
"""Differential fuzz runner (DESIGN.md section 4.5 rules 1-6, 4.5.1-4.5.3;
DESIGN-PYTHON.md section 4.6 rules 1-8).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Seeded cases (4.6 rule 1: random.Random(seed); the cases differ from the
JS fuzz because the generator differs, and that is fine) built with the
grammar of DESIGN.md section 4.5, steps 1-3.  Each case runs through the
oracle harness (oracle_client.run_tasks, 4.6 rule 3: ThreadPoolExecutor
8, one client per worker thread) and through the in-process render() for
the 7 core modes (4.6 rule 5): normal return is exit 0, CallplotError is
exit 1, and any other exception is a DIFF and is never swallowed.  The
port's render returns a str; byte comparison uses encode("utf-8",
"replace") (DESIGN-PYTHON.md section 3.2).  If both exits are 0 compare
bytes; when the oracle exits non-zero compare only the exit codes (4.5
rule 5).  Save the first 50 diffs as test/fixtures/fuzz/pyseedS_caseK
(4.6 rule 7: the py prefix is the ONE allowed addition to shared data;
never touch goldens here, they come from the gen-golden tooling, one
process per run, never from the harness).

Usage: tools/fuzz.py --seed <n> --count <n>
Exit: 0 when no diff, 1 when any diff was found, 2 on a usage error.
"""

import os
import random
import sys
import time

sys.path.insert(0, os.path.abspath("src"))
sys.path.insert(0, os.path.abspath("tools"))

from oracle_client import run_tasks

from callplot.api import render
from callplot.constants import Mode
from callplot.context import RunContext
from callplot.errors import CallplotError

# the 7 core modes: (name, oracle mode flag, port mode) (DESIGN.md 4.5
# step 4 and 4.5.1: the mode flag on the CASE frame)
CORE_MODES = [
    ("text", "text", Mode.TEXT),  # the CASE frame says text (4.5.1 table)
    ("pic", "-pic", Mode.PIC),
    ("xml", "-xml", Mode.XML),
    ("svg", "-svg", Mode.SVG),
    ("vml", "-vml", Mode.VML),
    ("vxml", "-vxml", Mode.VXML),
    ("graffle", "-graffle", Mode.GRAFFLE),
]

# option names from DESIGN.md section 3.3, split by value type
INT_OPTIONS = ["startLine", "startColumn", "linePitch", "columnPitch", "vmlBoxWidthPercentage"]
BOOL_OPTIONS = [
    "stagger",
    "crunch",
    "links",
    "topLabel",
    "bottomLabel",
    "messageNumbering",
    "noteNumbering",
]
STRING_OPTIONS = [
    "picXSize",
    "picYSize",
    "vmlStyle",
    "vmlFont",
    "vmlTextSize",
    "vmlArrowStyle",
    "vmlDottedStyle",
    "vmlBoxStyle",
    "vmlTextStyle",
    "vmlBoxTextStyle",
]

BAD_INTS = ["", "x", " 3", "3x", "99999999999", "- 7"]
BAD_BOOLS = ["maybe", "1", "on2"]
STRING_VALUES = [" ", "-", "9pt", "bold", "fillcolor='blue'", "EndArrow='Open'", "DashStyle='dot'"]
CHARS = "abcxyz01 ()<>!#&*.;:-^\\/=,%"


def caption(rng):
    """One caption: 0-80 characters built from the DESIGN.md 4.5 step 3
    pieces: ^ \\/ (n) < & space and random characters."""
    target = rng.randint(0, 80)
    s = []
    n = 0
    while n < target:
        k = rng.random()
        if k < 0.15:
            piece = "^"
        elif k < 0.25:
            piece = "\\/"
        elif k < 0.35:
            piece = "(" + str(rng.randrange(99)) + ")"
        elif k < 0.45:
            piece = "<"
        elif k < 0.55:
            piece = "&"
        elif k < 0.65:
            piece = " "
        else:
            piece = CHARS[rng.randrange(len(CHARS))]
        s.append(piece)
        n += len(piece)
    return "".join(s)


def gen_case(rng):
    """One case per the grammar of DESIGN.md 4.5, steps 1-3: 0-6 guy lines,
    0-4 opt lines (about 10% invalid values), 0-30 message/note/comment/
    dummy lines; aliases come from the declared set with 5% unknown."""
    lines = []
    declared = []
    guys = rng.randint(0, 6)
    for i in range(guys):
        alias = chr(97 + (i % 26))
        declared.append(alias)
        lines.append("guy/" + alias + "/" + caption(rng))
    opts = rng.randint(0, 4)
    for _i in range(opts):
        kind = rng.randrange(3)
        if kind == 0:
            name = rng.choice(INT_OPTIONS)
            value = str(rng.randrange(40)) if rng.random() < 0.9 else rng.choice(BAD_INTS)
        elif kind == 1:
            name = rng.choice(BOOL_OPTIONS)
            if rng.random() < 0.9:
                value = "on" if rng.random() < 0.5 else "off"
            else:
                value = rng.choice(BAD_BOOLS)
        else:
            name = rng.choice(STRING_OPTIONS)
            value = rng.choice(STRING_VALUES)
        lines.append("opt/" + name + "/" + value)
    body = rng.randint(0, 30)

    def pick():
        pool = declared if len(declared) > 0 else ["a", "b"]
        if rng.random() < 0.05:
            return "z"  # unknown alias, about 5% (4.5 step 3)
        return pool[rng.randrange(len(pool))]

    for _i in range(body):
        kind = rng.random()
        if kind < 0.45:
            caps = rng.randint(0, 3)
            line = pick() + "->" + pick()
            for _k in range(caps):
                line += "/" + caption(rng)
            lines.append("-" + line if rng.random() < 0.1 else line)
        elif kind < 0.55:
            pre = "-" if rng.random() < 0.1 else ""
            lines.append(pre + pick() + ".." + pick() + "/" + caption(rng))
        elif kind < 0.65:
            pre = "-" if rng.random() < 0.1 else ""
            lines.append(pre + pick() + "--" + pick() + "/" + caption(rng))
        elif kind < 0.75:
            pre = "-" if rng.random() < 0.1 else ""
            lines.append(pre + "note/" + pick() + "/" + caption(rng))
        elif kind < 0.85:
            lines.append(("!!" if rng.random() < 0.5 else "!") + caption(rng))
        else:
            lines.append(caption(rng))
    # shuffle: guy, opt and body lines interleave (DESIGN.md 3.1)
    for i in range(len(lines) - 1, 0, -1):
        j = rng.randrange(i + 1)
        lines[i], lines[j] = lines[j], lines[i]
    a1 = rng.random()
    end = "\r" if a1 < 0.05 else "\r\n" if rng.random() < 0.1 else "\n"
    text = end.join(lines)
    if rng.random() < 0.9:
        text += end
    return text.encode("utf-8")


def port_run(text, mode):
    """One case through the in-process port (4.6 rule 5): normal return is
    exit 0, CallplotError models exit 1.  Any other exception is NOT caught:
    it is a diff in the port and must never be swallowed here."""
    try:
        out = render(text, mode, ctx=RunContext(), options=None)
    except CallplotError:
        return 1, b""
    return 0, out.encode("utf-8", "replace")  # DESIGN-PYTHON.md 3.2


def main():
    seed = None
    count = None
    argv = sys.argv[1:]
    i = 0
    while i < len(argv) - 1:
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
        i += 1
    if seed is None or count is None or count < 1:
        sys.stderr.write("usage: tools/fuzz.py --seed <n> --count <n>\n")
        return 2

    t0 = time.monotonic()
    print(f"fuzz: seed {seed}, count {count}, modes {len(CORE_MODES)}")

    rng = random.Random(seed)  # 4.6 rule 1: cases differ from the JS fuzz
    cases = [gen_case(rng) for _c in range(count)]
    tasks = []
    for c, case in enumerate(cases):
        for mode, flag, _bit in CORE_MODES:
            tasks.append({"key": f"{c}.{mode}", "flag": flag, "input": case})
    # oracle leg: one client per worker thread inside (4.6 rules 3/4)
    harness = run_tasks(tasks, workers=8, timeout=5.0)

    # Compare each case x mode: harness oracle vs Python port.
    diffs = []
    groups = {}
    for c, case in enumerate(cases):
        text = case.decode("utf-8", "replace")
        for mode, _flag, bit in CORE_MODES:
            key = f"{c}.{mode}"
            if key not in harness:
                diffs.append({"c": c, "mode": mode, "why": "no harness result"})
                continue
            jexit, jout = harness[key]
            pexit, pout = port_run(text, bit)
            why = None
            if jexit != pexit:
                why = f"exit {jexit} vs port {pexit}"
            elif jexit == 0 and jout != pout:
                # both exited 0: compare bytes (4.5 rule 5)
                n = min(len(jout), len(pout))
                b = 0
                while b < n and jout[b] == pout[b]:
                    b += 1
                head = jout[0:b].decode("latin1")
                line = head.count("\n") + 1
                why = f"byte diff at {b} (line {line}, {len(jout)} vs {len(pout)} bytes)"
            if why is not None:
                diffs.append({"c": c, "mode": mode, "why": why})
                group = f"{mode}|{why.split('(')[0].strip()}"
                groups[group] = groups.get(group, 0) + 1

    # 4.6 rule 7 / 4.5 rule 6: the first 50 diffs become fixtures.  The py
    # prefix marks them as the Python port's own additions (the one
    # allowed exception to "never edit shared data").  Goldens are never
    # touched here.
    saved = 0
    if diffs:
        os.makedirs(os.path.join("test", "fixtures", "fuzz"), exist_ok=True)
        seen = set()
        for d in diffs:
            if saved >= 50:
                break
            fc = d["c"]  # the case number
            path = os.path.join("test", "fixtures", "fuzz", f"pyseed{seed}_case{fc}")
            if fc in seen or os.path.exists(path):
                continue
            with open(path, "wb") as fh:
                fh.write(cases[d["c"]])
            seen.add(d["c"])
            saved += 1

    secs = time.monotonic() - t0
    print(f"cases: {count}, runs: {len(tasks)}, diffs: {len(diffs)}, fixtures saved: {saved}")
    print(f"time: {secs:.1f} s")  # 4.6 rule 8: report the run time
    if diffs:
        print("diff groups (mode | first cause | count):")
        top = sorted(groups.items(), key=lambda kv: -kv[1])[:20]
        for g, n in top:
            print(f"  {g} = {n}")
        print("first diff cases:")
        for d in diffs[:20]:
            print(f"  case {d['c']} {d['mode']}: {d['why']}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
