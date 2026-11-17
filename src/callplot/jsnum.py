"""JS number text for the new outputs (DESIGN-PYTHON.md section 3.9).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

The new outputs have no Java oracle: their oracle is the JS-approved
snapshot, so their numbers must print as JS prints them (String(n),
n.toFixed(k), Math.round), not as Java or Python does.  Only the
renderers under renderers/html/ use these helpers.  Matched Node 24 on
the section 3.9 tables (2026-11-15).
"""

import math
from decimal import ROUND_HALF_UP, Decimal

from callplot.errors import CallplotError


def js_num(x: float) -> str:
    """JS String(x). Valid for 1e-6 <= |x| < 1e21, which covers every
    layout number (page pixels and pitches)."""
    if isinstance(x, bool):
        raise CallplotError("jsNum: not a number")
    if math.isnan(x):
        return "NaN"
    if math.isinf(x):
        return "Infinity" if x > 0 else "-Infinity"
    if x == 0:
        return "0"  # JS prints -0 as "0"
    if not 1e-6 <= abs(x) < 1e21:
        raise CallplotError(f"js_num out of range: {x!r}")
    return format(Decimal(repr(x)).normalize(), "f")


def js_to_fixed(x: float, k: int) -> str:
    """JS x.toFixed(k): Decimal(x) is the exact binary value; JS rounds an
    exact tie away from zero (up for positives)."""
    return str(Decimal(x).quantize(Decimal(1).scaleb(-k), rounding=ROUND_HALF_UP))


def js_round(x: float) -> int:
    """JS Math.round(x): toward +Infinity, not floor(x + 0.5) (which gives
    1 for 0.49999999999999994 while JS gives 0)."""
    f = math.floor(x)
    return f + 1 if x - f >= 0.5 else f
