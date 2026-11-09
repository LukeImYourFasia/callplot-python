"""Java-semantics helpers (DESIGN.md section 3.5).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

DESIGN-PYTHON.md section 3.3: this file holds the Python way of every
helper.  Text inside the port is held as unit strings (section 3.2): to_units
runs first in render()/prep(), from_units last.  No standard-library I/O
here: this file is part of the pure core (DESIGN-PYTHON.md PD7).
"""

import math
import re
from collections.abc import Sequence

from callplot.errors import (
    CallplotArithmeticError,
    CallplotError,
    CallplotIndexError,
    NegativeArraySizeError,
    NumberFormatError,
)


def to_units(s: str) -> str:
    """First step of render()/prep(): replace every character above U+FFFF
    with its two surrogate code units, as Java stores a char[].

    If no such character exists the text is returned unchanged (the common
    case; the whole corpus is like this).
    """
    if all(ord(c) < 0x10000 for c in s):
        return s
    res: list[str] = []
    for c in s:
        cp = ord(c)
        if cp > 0xFFFF:
            cp -= 0x10000
            res.append(chr(0xD800 + (cp >> 10)) + chr(0xDC00 + (cp & 0x3FF)))
        else:
            res.append(c)
    return "".join(res)


def from_units(s: str) -> str:
    """Last step of render()/prep(): join each valid surrogate pair back
    into one character.  A lone surrogate stays as it is (it encodes to
    '?' through the command writer, like Java writes it)."""
    if not any(0xD800 <= ord(c) <= 0xDFFF for c in s):
        return s
    res: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        code = ord(s[i])
        if 0xD800 <= code <= 0xDBFF and i + 1 < n and 0xDC00 <= ord(s[i + 1]) <= 0xDFFF:
            hi = code - 0xD800
            lo = ord(s[i + 1]) - 0xDC00
            res.append(chr(0x10000 + (hi << 10) + lo))
            i += 2
        else:
            res.append(s[i])
            i += 1
    return "".join(res)


def read_lines(text: str) -> list[str]:
    """Java BufferedReader.readLine (DESIGN-PYTHON.md section 3.2): split on
    \\r\\n, \\r or \\n only; "" and a text ending in a line end drop the last
    (empty) item.  NEVER use str.splitlines(): it also splits on \\x0b,
    \\x0c, \\x1c-\\x1e, \\x85 and the Unicode line separators."""
    if text == "":
        return []
    lines: list[str] = []
    n = len(text)
    start = 0
    i = 0
    while i < n:
        ch = text[i]
        if ch == "\n":
            lines.append(text[start:i])
            i += 1
            start = i
        elif ch == "\r":
            lines.append(text[start:i])
            i += 2 if i + 1 < n and text[i + 1] == "\n" else 1
            start = i
        else:
            i += 1
    if start < n:
        lines.append(text[start:])
    return lines


# --- Number formatting ----------------------------------------------------


def fmt_i(n: int) -> str:
    """Java String concatenation of an int ("" + int)."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise CallplotError("not a Java int: " + str(n))
    return str(n)


def _java_double_digits_exp(x: float) -> tuple[str, int]:
    """Shortest decimal digits + decimal-point index for a finite double.

    Returns (digits, n): value == int(digits) * 10 ** (n - len(digits)),
    digits has no leading or trailing zeros.  Repr is the shortest string
    that round-trips, like Java 8's Double.toString (Ryu/Grisu shortest).
    """
    s = repr(abs(x))
    # Python repr is plain decimal or %e style; parse both into digits/n.
    if "e" in s or "E" in s:
        m = re.match(r"^(\d+)(?:\.(\d+))?[eE]([-+]?\d+)$", s)
        if m is None:
            raise AssertionError  # repr of a double always matches this shape
        intpart, frac, exp = m.group(1), m.group(2) or "", int(m.group(3))
    else:
        m = re.match(r"^(\d+)(?:\.(\d+))?$", s)
        if m is None:
            raise AssertionError  # repr of a double always matches this shape
        intpart, frac, exp = m.group(1), m.group(2) or "", 0
    digits = intpart + frac
    n = len(intpart) + exp
    lead = len(digits) - len(digits.lstrip("0"))
    digits = digits.lstrip("0")
    n -= lead
    digits = digits.rstrip("0")
    if digits == "":  # x == 0, handled by the caller
        digits, n = "0", 1
    return digits, n


def fmt_d(x: float) -> str:
    """Java Double.toString on OpenJDK 1.8.0_504 (section 3.5 table).

    Python's repr is the same shortest round-trip form, so the plain and
    scientific branches below reproduce the pinned rows (44.800000000000004,
    1.0E7, 1.0E-4, -0.0, ...).
    """
    if x != x:
        return "NaN"
    if x == float("inf"):
        return "Infinity"
    if x == float("-inf"):
        return "-Infinity"
    if x == 0:
        # Java prints "0.0" and "-0.0"; distinguish via the sign bit.
        return "-0.0" if str(x)[0] == "-" else "0.0"
    digits, n = _java_double_digits_exp(x)
    sign = "-" if x < 0 else ""
    # Java switches to E-notation outside [1e-3, 1e7).
    if -2 <= n <= 7:
        if n <= 0:
            return sign + "0." + "0" * (-n) + digits
        if n >= len(digits):
            return sign + digits + "0" * (n - len(digits)) + ".0"
        return sign + digits[:n] + "." + digits[n:]
    mantissa = digits[0] + "." + (digits[1:] or "0")
    return sign + mantissa + "E" + str(n - 1)


# --- Java int arithmetic --------------------------------------------------


def idiv(a: int, b: int) -> int:
    """Java int / int: truncating toward zero."""
    if b == 0:
        raise CallplotArithmeticError("/ by zero")
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def fdiv(a: float, b: float) -> float:
    """Java double / double (DESIGN-PYTHON.md section 3.3): division by
    +-0.0 follows IEEE 754 (inf/NaN, sign = sign of a times the sign of
    the zero), it does NOT raise like Python's a / b."""
    if b == 0.0:
        if math.isnan(a) or a == 0.0:
            return math.nan
        neg = (a < 0.0) ^ (math.copysign(1.0, b) < 0.0)
        return -math.inf if neg else math.inf
    return a / b


def parse_java_int(s: str) -> int:
    """Integer.parseInt (strict). Java 8 accepts a leading + or -."""
    if not re.fullmatch(r"[+-]?[0-9]+", s, re.ASCII):
        raise NumberFormatError('For input string: "' + s + '"')
    v = int(s)
    if v < -2147483648 or v > 2147483647:
        raise NumberFormatError('value out of int range: "' + s + '"')
    return v


# --- JS number printing (the -html geometry is JS arithmetic) -------------


def js_num(v: float) -> str:
    """Number -> string the way JavaScript template literals do it: an
    integral double prints without a decimal point ("75", "116"), and a
    non-integral one prints with the shortest round-trip decimal, same
    rule as repr on Python floats.  Magnitudes here are page pixels, so
    the JS exponent forms (>=1e21, <1e-7) never occur."""
    if isinstance(v, bool):
        raise CallplotError("jsNum: not a number")
    if isinstance(v, int):
        return str(v)
    if v == int(v):
        return str(int(v))
    return repr(v)


def js_round(v: float) -> int:
    """Math.round: half toward +Infinity (Python round() is half-to-even)."""
    return math.floor(v + 0.5)


def arr_at(a: list[str], i: int) -> str:
    """Java array/[] access: out-of-bounds throws."""
    if i < 0 or i >= len(a):
        raise CallplotIndexError("Index out of range")
    return a[i]


def java_trim(s: str) -> str:
    """String.trim: strips leading/trailing chars with code <= U+0020.
    NOT the same as str.strip(), which also strips Unicode spaces."""
    i = 0
    j = len(s)
    while i < j and ord(s[i]) <= 0x20:
        i += 1
    while j > i and ord(s[j - 1]) <= 0x20:
        j -= 1
    return s[i:j]


def java_split(s: str, pattern: re.Pattern[str]) -> list[str]:
    """String.split(regex) on Java:
      - no match anywhere       -> [s]
      - otherwise               -> segments, with trailing empty strings dropped
      - all segments empty      -> [] (confirmed on OpenJDK 1.8.0_504:
                                    "//".split("/") has length 0)

    ``pattern`` is a compiled pattern with no capturing groups (DESIGN-PYTHON.md
    section 3.3).  Java Regex and Python re agree for the patterns this
    port uses: the parser's slash rule (Parser.java:75) is a fixed-width
    lookbehind, which Python re supports natively, so no hand-rolled
    scanner is needed.
    """
    compiled = pattern
    if not compiled.search(s):
        return [s]
    segs = compiled.split(s)
    while len(segs) > 0 and segs[-1] == "":
        segs.pop()
    return segs


def tokenize(s: str, delim: str = "^") -> list[str]:
    """java.util.StringTokenizer(s, delim): split on each delim char, drop empties."""
    return [t for t in s.split(delim) if len(t) > 0]


# --- char[] buffer --------------------------------------------------------


class CharBuf:
    """Java char[]: indexed by UTF-16 code unit. Cells start as NUL, the
    Java char[] initializer, not spaces: nothing in the port may rely on
    pre-filled blanks (the text renderer writes every cell each line)."""

    def __init__(self, width: int) -> None:
        if width < 0:
            raise NegativeArraySizeError(str(width))
        self.a: list[str] = ["\u0000"] * width

    def get(self, i: int) -> str:
        if i < 0 or i >= len(self.a):
            raise CallplotIndexError("Index out of range")
        return self.a[i]

    def set(self, i: int, ch: str) -> None:
        if i < 0 or i >= len(self.a):
            raise CallplotIndexError("Index out of range")
        self.a[i] = ch

    def copy_in(self, src: Sequence[str], at: int, n: int) -> None:
        """System.arraycopy(src, 0, buf, at, n): bounds of the whole range
        are checked before any write happens."""
        if n < 0 or at < 0 or at + n > len(self.a):
            raise CallplotIndexError("Index out of range")
        for k in range(n):
            self.a[at + k] = src[k]

    def slice_string(self, at: int, n: int) -> str:
        """new String(char[], offset, length): read n cells as a string."""
        out = []
        for k in range(n):
            out.append(self.get(at + k))
        return "".join(out)
