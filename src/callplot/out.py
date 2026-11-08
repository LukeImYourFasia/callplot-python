"""In-memory stand-in for the Java PrintWriter (DESIGN.md sections 2.2, 3.5).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

The core does no I/O; renderers write into an Out and the CLI prints it.
"""


class Out:
    def __init__(self):
        self.parts = []

    def print(self, s):
        self.parts.append(s)

    def println(self, s=""):
        self.parts.append(s)
        self.parts.append("\n")

    def write(self, ch):
        self.parts.append(ch)

    def toString(self):
        return "".join(self.parts)


class Err:
    """Java's System.err (section 3.7): process-wide, like the RunContext
    that carries it. Graffle's repeatLabel debug lines land here (section
    3.8 #7)."""

    def __init__(self):
        self.parts = []

    def print(self, s):
        self.parts.append(s)

    def println(self, s=""):
        self.parts.append(s)
        self.parts.append("\n")

    def toString(self):
        return "".join(self.parts)
