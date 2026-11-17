"""Process-wide static counters (DESIGN.md section 3.6, DESIGN-PYTHON.md
section 3.5).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

The three Java ``static`` counters live here.  The CLI keeps one
RunContext for the whole run and passes it to every render() call, so
Graffle IDs and the stagger alternation carry across files like the
Java statics.  No module keeps state of its own.

Errata (logged in docs/appendix-b.md): DESIGN-PYTHON.md section 3.5 says
RunContext has 3 fields, but section 3.6 rule 11 ("Graffle ``--`` debug
lines go to stderr") needs a transport from the renderer to the command,
and the core may do no I/O.  ``err`` is that buffer: an io.StringIO the
command drains to stderr.  It carries no counters of its own.
"""

import io
from dataclasses import dataclass, field


@dataclass
class RunContext:
    """The three Java statics: Player.id, Message.id, Player.mynum."""

    player_id: int = 1_000_000
    message_id: int = 1
    mynum: int = 0
    err: io.StringIO = field(default_factory=io.StringIO)
