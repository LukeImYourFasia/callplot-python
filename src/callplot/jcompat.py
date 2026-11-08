"""Java-semantics helpers (DESIGN.md section 3.5).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Every renderer must format numbers through fmtI/fmtD and index buffers
through CharBuf.  No standard-library I/O here: this file is part of the
pure core (DESIGN.md section 4.6, criterion 5).

Text is a Python str.  Java indexes UTF-16 code units; Python indexes
code points.  The oracle corpus (fixtures, goldens, snapshots) contains
no astral characters, so the two agree for everything the tool is ever
asked to render; that caveat is pinned in test/unit/test_corpus.py.
"""

import math
import re

# --- Error model: names after the Java exceptions -------------------------


class CallplotError(Exception):
    """Base of every expected (operational) failure."""


class NumberFormatError(CallplotError):
    pass


class IllegalArgumentError(CallplotError):
    pass


class IndexError(CallplotError):
    pass


class NullPointerError(CallplotError):
    pass


class ArithmeticError(CallplotError):
    pass


class NegativeArraySizeError(CallplotError):
    pass


class JavaRuntimeException(Exception):
    """Flow.java throws a bare java RuntimeException (JS used bare Error).
    Not a CallplotError: the same exit-1 path in bin/, and stderr is never
    compared against a golden.  Kept distinct so catch sites match Java."""


# --- Number formatting ----------------------------------------------------


def fmtI(n):
    """Java String concatenation of an int ("" + int)."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise CallplotError("not a Java int: " + str(n))
    return str(n)


def _java_double_digits_exp(x):
    """Shortest decimal digits + decimal-point index for a finite double.

    Returns (digits, n): value == int(digits) * 10 ** (n - len(digits)),
    digits has no leading or trailing zeros.  Repr is the shortest string
    that round-trips, like Java 8's Double.toString (Ryu/Grisu shortest).
    """
    s = repr(abs(x))
    # Python repr is plain decimal or %e style; parse both into digits/n.
    if "e" in s or "E" in s:
        m = re.match(r"^(\d+)(?:\.(\d+))?[eE]([-+]?\d+)$", s)
        intpart, frac, exp = m.group(1), m.group(2) or "", int(m.group(3))
    else:
        m = re.match(r"^(\d+)(?:\.(\d+))?$", s)
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


def fmtD(x):
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


def idiv(a, b):
    """Java int / int: truncating toward zero."""
    if b == 0:
        raise ArithmeticError("/ by zero")
    q = abs(a) // abs(b)
    return -q if (a < 0) != (b < 0) else q


def parseJavaInt(s):
    """Integer.parseInt (strict). Java 8 accepts a leading + or -."""
    if not re.match(r"^[+-]?[0-9]+$", s):
        raise NumberFormatError('For input string: "' + s + '"')
    v = int(s)
    if v < -2147483648 or v > 2147483647:
        raise NumberFormatError('value out of int range: "' + s + '"')
    return v


# --- JS number printing (the -html geometry is JS arithmetic) -------------


def jsNum(v):
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


def jsRound(v):
    """Math.round: half toward +Infinity (Python round() is half-to-even)."""
    return math.floor(v + 0.5)


def arrAt(a, i):
    """Java array/[] access: out-of-bounds throws."""
    if i < 0 or i >= len(a):
        raise IndexError("Index out of range")
    return a[i]


def javaTrim(s):
    """String.trim: strips leading/trailing chars with code <= U+0020.
    NOT the same as str.strip(), which also strips Unicode spaces."""
    i = 0
    j = len(s)
    while i < j and ord(s[i]) <= 0x20:
        i += 1
    while j > i and ord(s[j - 1]) <= 0x20:
        j -= 1
    return s[i:j]


def javaSplit(s, re_):
    """String.split(regex) on Java:
      - no match anywhere       -> [s]
      - otherwise               -> segments, with trailing empty strings dropped
      - all segments empty      -> [] (confirmed on OpenJDK 1.8.0_504:
                                    "//".split("/") has length 0)

    re_ is a compiled pattern (str pattern accepted).  Java Regex and
    Python re agree for the patterns this port uses: the parser's slash
    rule (Parser.java:75) is a fixed-width lookbehind, which Python re
    supports natively, so no hand-rolled scanner is needed.
    """
    compiled = re.compile(re_) if isinstance(re_, str) else re_
    if not compiled.search(s):
        return [s]
    segs = compiled.split(s)
    while len(segs) > 0 and segs[-1] == "":
        segs.pop()
    return segs


def tokenize(s, delim="^"):
    """java.util.StringTokenizer(s, delim): split on each delim char, drop empties."""
    return [t for t in s.split(delim) if len(t) > 0]


# --- char[] buffer --------------------------------------------------------


class CharBuf:
    """Java char[]: indexed by UTF-16 code unit. Cells start as NUL, the
    Java char[] initializer, not spaces: nothing in the port may rely on
    pre-filled blanks (the text renderer writes every cell each line)."""

    def __init__(self, width):
        if width < 0:
            raise NegativeArraySizeError(str(width))
        self.a = ["\u0000"] * width

    def get(self, i):
        if i < 0 or i >= len(self.a):
            raise IndexError("Index out of range")
        return self.a[i]

    def set(self, i, ch):
        if i < 0 or i >= len(self.a):
            raise IndexError("Index out of range")
        self.a[i] = ch

    def copyIn(self, src, at, n):
        """System.arraycopy(src, 0, buf, at, n): bounds of the whole range
        are checked before any write happens."""
        if n < 0 or at < 0 or at + n > len(self.a):
            raise IndexError("Index out of range")
        for k in range(n):
            self.a[at + k] = src[k]

    def sliceString(self, at, n):
        """new String(char[], offset, length): read n cells as a string."""
        out = []
        for k in range(n):
            out.append(self.get(at + k))
        return "".join(out)
