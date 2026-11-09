"""Parser.java:37-166, ported step by step (DESIGN.md section 3.1).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Do not "clean it up": the quirks in DESIGN.md section 3.8 are intentional.
"""

import re

from callplot.errors import CallplotIndexError, NullPointerError
from callplot.flow import Flow
from callplot.jcompat import java_split, java_trim, read_lines
from callplot.model import Message, Player

# Parser.java:75 regex: split on every / whose preceding char is not \.
# The lookbehind is fixed-width, so Python re compiles it as is; position
# 0 never splits (there is no preceding char).
SLASH_RE = re.compile(r"(?<=[^\\])/")


def at(parts: list[str], k: int) -> str:
    """Java array indexing on the split parts: a missing field throws
    IndexError (CallplotIndexError, DESIGN-PYTHON.md section 3.5: a field
    missing from a line raises through this helper, never a bare built-in)."""
    if k < 0 or k >= len(parts):
        raise CallplotIndexError("Index out of range")
    return parts[k]


def parse(text: str) -> Flow:
    """DESIGN-PYTHON.md section 2.2: ``parse(lines) -> Flow``: the lines
    come from read_lines (jcompat), not str.splitlines."""
    players: list[Player] = []
    messages: list[Message] = []
    opts: dict[str, str] = {}
    f = Flow(players, messages, opts)

    last_msg = None
    dummy = False
    new_dummy = False

    # section 3.1: 1-based line number of the current raw line (new, for
    # the IR)
    line_no = 0

    for line0 in read_lines(text):
        line = line0
        line_no += 1
        t_line = java_trim(line)  # Parser.java:54

        # Parser.java:56
        if t_line.startswith("#") or len(t_line) == 0:
            continue

        # Parser.java:60-66
        if t_line.startswith("!!"):
            if last_msg is None:
                raise NullPointerError()
            last_msg.add_note(t_line[2:])
            continue
        if t_line.startswith("!"):
            if last_msg is None:
                raise NullPointerError()
            last_msg.add_comment(t_line[1:])
            continue

        # Parser.java:69-72: slices the RAW line, not the trimmed line
        if t_line.startswith("-"):
            new_dummy = True
            line = line[1:]

        # Parser.java:75
        split_line_escaped = java_split(line, SLASH_RE)
        # Parser.java:78-83: unescape \/ for all fields except the command
        parts = [p if i == 0 else p.replace("\\/", "/") for i, p in enumerate(split_line_escaped)]

        # Parser.java:85: command = splitLine[tkn++]
        command = at(parts, 0)
        tkn = [1]  # mutable index like Java's tkn++

        if command == "guy":
            # Parser.java:86-89
            name = at(parts, tkn[0])
            tkn[0] += 1
            caption = at(parts, tkn[0])
            tkn[0] += 1
            players.append(Player(name, caption))
        elif command == "note":
            # Parser.java:90-100
            from_ = at(parts, tkn[0])
            tkn[0] += 1
            if not dummy and last_msg is not None:
                messages.append(last_msg)
            dummy = new_dummy
            new_dummy = False
            last_msg = Message(from_, from_, at(parts, tkn[0]), " ", False, False)
            tkn[0] += 1
            last_msg.src_line = line_no
        elif command == "opt":
            # Parser.java:101-106: values are not trimmed; later put wins
            name = at(parts, tkn[0])
            tkn[0] += 1
            value = at(parts, tkn[0])
            tkn[0] += 1
            opts[name] = value
        elif "->" in command:
            # Parser.java:107-132
            arrow_idx = command.index("->")
            from_ = java_trim(command[:arrow_idx])
            to = java_trim(command[arrow_idx + 2 :])
            reply = False
            while tkn[0] < len(parts):
                if not dummy and last_msg is not None:
                    messages.append(last_msg)
                dummy = new_dummy
                new_dummy = False
                if reply:
                    last_msg = Message(to, from_, at(parts, tkn[0]), "-", False, True)
                else:
                    last_msg = Message(from_, to, at(parts, tkn[0]), "-", False, True)
                tkn[0] += 1
                last_msg.src_line = line_no
                last_msg.is_reply = reply  # set before flipping (section 3.1)
                reply = not reply
        elif ".." in command:
            # Parser.java:133-145: filler '.', no arrows; extra fields
            # ignored
            dot_idx = command.index("..")
            from_ = java_trim(command[:dot_idx])
            to = java_trim(command[dot_idx + 2 :])
            if not dummy and last_msg is not None:
                messages.append(last_msg)
            dummy = new_dummy
            new_dummy = False
            last_msg = Message(from_, to, at(parts, tkn[0]), ".", False, False)
            tkn[0] += 1
            last_msg.src_line = line_no
        elif "--" in command:
            # Parser.java:146-159: like .. but repeat_label=true (filler
            # '.' too)
            dot_idx = command.index("--")
            from_ = java_trim(command[:dot_idx])
            to = java_trim(command[dot_idx + 2 :])
            if not dummy and last_msg is not None:
                messages.append(last_msg)
            dummy = new_dummy
            new_dummy = False
            last_msg = Message(from_, to, at(parts, tkn[0]), ".", False, False, True)
            tkn[0] += 1
            last_msg.src_line = line_no
        # Parser.java:159: anything else: ignore the line, no error

    # Parser.java:161-164
    if not dummy and last_msg is not None:
        messages.append(last_msg)
    return f
