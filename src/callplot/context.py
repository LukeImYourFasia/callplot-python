"""Process-wide static counters (DESIGN.md section 3.6).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

The CLI keeps one RunContext for the whole process and passes it to every
render() call, so Graffle IDs and the stagger alternation carry across
files, like the Java statics.
"""

from .out import Err


class RunContext:
    def __init__(self):
        self.playerId = 1000000  # Player.id
        self.messageId = 1  # Message.id
        self.mynum = 0  # Player.mynum
        self.err = Err()  # java's System.err, shared for the whole process
