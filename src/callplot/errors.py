"""The error model (DESIGN-PYTHON.md section 3.5).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Every expected (operational) failure subclasses CallplotError.  Each class
carries a class attribute ``name``: the command prints
``callplot: {err.name}: {err}`` (section 3.6), which is the Java exception
name the original tool shows in its stack trace.

Do NOT name a class ``IndexError`` or ``ArithmeticError``: those are Python
built-ins (section 3.5 rule).  A missing line field raises CallplotIndexError
through the ``at``/``arr_at`` helpers, never a bare built-in IndexError.
"""


class CallplotError(Exception):
    """Base of every expected failure."""

    name: str


class NumberFormatError(CallplotError):
    """Integer.parseInt rejected the text (NumberFormatException)."""

    name = "NumberFormatError"


class IllegalArgumentError(CallplotError):
    """IllegalArgumentException."""

    name = "IllegalArgumentError"


class CallplotIndexError(CallplotError):
    """IndexOutOfBoundsException."""

    name = "IndexError"


class NullPointerError(CallplotError):
    """NullPointerException."""

    name = "NullPointerError"


class CallplotArithmeticError(CallplotError):
    """ArithmeticException ("/ by zero")."""

    name = "ArithmeticError"


class NegativeArraySizeError(CallplotError):
    """NegativeArraySizeException."""

    name = "NegativeArraySizeError"


class TableInputError(CallplotError):
    """Xalan would reject this input (DESIGN.md section 3.13.4): a raw '<'
    or a bare '&' in an annotation makes the oracle exit 255."""

    name = "TableInputError"


class JavaRuntimeError(CallplotError):
    """The Java source throws a bare ``RuntimeException`` (DESIGN.md section
    3.3: a bad value for a boolean opt line).  DESIGN-PYTHON.md section 3.5
    lists no class for it; kept as a CallplotError subclass with the Java
    name so it exits 1 like the oracle instead of reading as a programmer
    error.  Logged as an errata in docs/appendix-b.md."""

    name = "RuntimeException"
