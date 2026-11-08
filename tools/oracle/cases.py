# Fuzz case generator (DESIGN.md section 4.5, rules 1-3): a port of
# tools/oracle/cases.js.  The same seed and count always give the same
# cases in the same order, so re-runs reproduce the same diffs.
#
# Copyright (C) 2004 dynamicsoft, Inc.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or (at
# your option) any later version.  A copy of the license is in LICENSE.
#
# mulberry32 is a byte-for-byte port of the JS generator: JS multiplies
# the two signed int32 operands as IEEE DOUBLES (so the low bits of
# products above 2^53 are the double's, not the exact integer's), and
# XORs coerce doubles back through mod-2^32.  Python floats are the same
# IEEE doubles, so the port computes the same bit patterns and, crucially,
# the same r() CALL COUNT per case: every generated number must consume
# generator calls in the same order as the JS generator.

import math

MASK32 = 0xFFFFFFFF


def _signed32(bits):
    """JS bitwise ops coerce to SIGNED int32 before arithmetic."""
    return bits - (1 << 32) if bits >= (1 << 31) else bits


def _bits_of_double(x):
    """JS ^ coerces a double with ToInt32: mathematically mod 2^32 of the
    double's exact value; two's-complement bits equal int(x) mod 2^32."""
    if math.isnan(x):
        return 0
    return int(x) & MASK32  # int() of a finite double is its exact value


def mulberry32(seed):
    """A generator yielding [0,1) doubles, identical to the JS one."""
    state = [seed & MASK32]

    def r():
        state[0] = (state[0] + 0x6D2B79F5) & MASK32  # a = (a + K) >>> 0
        t = state[0]
        # t = (t ^ (t >>> 15)) * (t | 1): operands as signed int32 numbers,
        # product as an IEEE double
        sx = _signed32((t & MASK32) ^ (t >> 15))
        sy = _signed32((t | 1) & MASK32)
        p = float(sx) * float(sy)
        # t ^= t + t * 7: both sides coerced back through mod 2^32; t*7
        # rounds first, then the addition rounds (same order as JS)
        ti = _bits_of_double(p)
        q = p + (p * 7.0)
        qi = _bits_of_double(q)
        tb = ti ^ qi  # 32-bit pattern (JS keeps a signed int32 Number)
        # ((t ^ (t >>> 4)) >>> 0) / 4294967296
        return ((tb ^ (tb >> 4)) & MASK32) / 4294967296.0

    return r


# Option names from section 3.3, split by value type.
INT_OPTIONS = ["startLine", "startColumn", "linePitch", "columnPitch",
               "vmlBoxWidthPercentage"]
BOOL_OPTIONS = ["stagger", "crunch", "links", "topLabel", "bottomLabel",
                "messageNumbering", "noteNumbering"]
STRING_OPTIONS = ["picXSize", "picYSize", "vmlStyle", "vmlFont", "vmlTextSize",
                  "vmlArrowStyle", "vmlDottedStyle", "vmlBoxStyle",
                  "vmlTextStyle", "vmlBoxTextStyle"]

BAD_INTS = ["", "x", " 3", "3x", "99999999999", "- 7"]
BAD_BOOLS = ["maybe", "1", "on2"]
STRING_VALUES = [" ", "-", "9pt", "bold", "fillcolor='blue'",
                 "EndArrow='Open'", "DashStyle='dot'"]
CHARS = "abcxyz01 ()<>!#&*.;:-^\\/=,%"


def caption(r):
    """One caption: 0-80 characters built from the section 4.5 parts."""
    target = math.floor(r() * 80)
    s = []
    n = 0
    while n < target:
        k = r()
        if k < 0.15:
            piece = "^"
        elif k < 0.25:
            piece = "\\/"
        elif k < 0.35:
            piece = "(" + str(math.floor(r() * 99)) + ")"
        elif k < 0.45:
            piece = "<"
        elif k < 0.55:
            piece = "&"
        elif k < 0.65:
            piece = " "
        else:
            piece = CHARS[math.floor(r() * len(CHARS))]
        s.append(piece)
        n += len(piece)
    return "".join(s)


def genCases(seed, count):
    """Generate the fuzz cases: list of UTF-8 byte strings."""
    r = mulberry32(seed)
    cases = []
    for _c in range(count):
        lines = []
        declared = []
        guys = math.floor(r() * 7)
        for i in range(guys):
            alias = chr(97 + (i % 26))
            declared.append(alias)
            lines.append("guy/" + alias + "/" + caption(r))
        opts = math.floor(r() * 5)
        for _i in range(opts):
            kind = math.floor(r() * 3)
            if kind == 0:
                name = INT_OPTIONS[math.floor(r() * len(INT_OPTIONS))]
                if r() < 0.9:
                    value = str(math.floor(r() * 40))
                else:
                    value = BAD_INTS[math.floor(r() * len(BAD_INTS))]
            elif kind == 1:
                name = BOOL_OPTIONS[math.floor(r() * len(BOOL_OPTIONS))]
                if r() < 0.9:
                    value = "on" if r() < 0.5 else "off"
                else:
                    value = BAD_BOOLS[math.floor(r() * len(BAD_BOOLS))]
            else:
                name = STRING_OPTIONS[math.floor(r() * len(STRING_OPTIONS))]
                value = STRING_VALUES[math.floor(r() * len(STRING_VALUES))]
            lines.append("opt/" + name + "/" + value)
        body = math.floor(r() * 31)
        for _i in range(body):
            pool = declared if len(declared) > 0 else ["a", "b"]

            def pick():
                if r() < 0.05:
                    return "z"
                return pool[math.floor(r() * len(pool))]

            kind = r()
            if kind < 0.45:
                caps = math.floor(r() * 4)
                line = pick() + "->" + pick()
                for _k in range(caps):
                    line += "/" + caption(r)
                lines.append("-" + line if r() < 0.1 else line)
            elif kind < 0.55:
                pre = "-" if r() < 0.1 else ""
                lines.append(pre + pick() + ".." + pick() + "/" + caption(r))
            elif kind < 0.65:
                pre = "-" if r() < 0.1 else ""
                lines.append(pre + pick() + "--" + pick() + "/" + caption(r))
            elif kind < 0.75:
                pre = "-" if r() < 0.1 else ""
                lines.append(pre + "note/" + pick() + "/" + caption(r))
            elif kind < 0.85:
                lines.append(("!!" if r() < 0.5 else "!") + caption(r))
            else:
                lines.append(caption(r))
        # shuffle: guy, opt and body lines interleave (section 3.1)
        for i in range(len(lines) - 1, 0, -1):
            j = math.floor(r() * (i + 1))
            lines[i], lines[j] = lines[j], lines[i]
        a1 = r()
        if a1 < 0.05:
            end = "\r"
        else:
            a2 = r()
            end = "\r\n" if a2 < 0.1 else "\n"
        # JS: lines.join(end) + (r() < 0.9 ? end : "")
        text = end.join(lines)
        if r() < 0.9:
            text += end
        cases.append(text.encode("utf-8"))
    return cases
