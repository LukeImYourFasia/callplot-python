"""Parser.java:37-166, ported step by step (DESIGN.md section 3.1).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Do not "clean it up": the quirks in DESIGN.md section 3.8 are intentional.
"""

import re

from .jcompat import javaTrim, javaSplit, IndexError, NullPointerError
from .model import Player, Message
from .flow import Flow


def splitLines(text):
    """BufferedReader.readLine (section 3.1): a line ends at \\n, \\r or
    \\r\\n.  A final unterminated line still counts; a trailing terminator
    adds no extra empty line."""
    lines = []
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


# Parser.java:75 regex: split on every / whose preceding char is not \.
# The lookbehind is fixed-width, so Python re compiles it as is; position
# 0 never splits (there is no preceding char).
SLASH_RE = re.compile(r"(?<=[^\\])/")


def at(parts, k):
    """Java array indexing on the split parts: a missing field throws IndexError."""
    if k < 0 or k >= len(parts):
        raise IndexError("Index out of range")
    return parts[k]


def parse(text):
    players = []
    messages = []
    opts = {}
    f = Flow(players, messages, opts)

    lastMsg = None
    dummy = False
    newDummy = False

    # section 3.1: 1-based line number of the current raw line (new, for the IR)
    lineNo = 0

    for line0 in splitLines(text):
        line = line0
        lineNo += 1
        tLine = javaTrim(line)  # Parser.java:54

        # Parser.java:56
        if tLine.startswith("#") or len(tLine) == 0:
            continue

        # Parser.java:60-66
        if tLine.startswith("!!"):
            if lastMsg is None:
                raise NullPointerError()
            lastMsg.addNote(tLine[2:])
            continue
        elif tLine.startswith("!"):
            if lastMsg is None:
                raise NullPointerError()
            lastMsg.addComment(tLine[1:])
            continue

        # Parser.java:69-72: slices the RAW line, not the trimmed line
        if tLine.startswith("-"):
            newDummy = True
            line = line[1:]

        # Parser.java:75
        splitLineEscaped = javaSplit(line, SLASH_RE)
        # Parser.java:78-83: unescape \/ for all fields except the command
        parts = [p if i == 0 else p.replace("\\/", "/")
                 for i, p in enumerate(splitLineEscaped)]

        # Parser.java:85: command = splitLine[tkn++]
        command = at(parts, 0)
        tkn = [1]  # mutable index like Java's tkn++

        def next():
            return at(parts, tkn[0])
            # incremented by the call sites, exactly like the Java tkn++

        if command == "guy":
            # Parser.java:86-89
            name = next()
            tkn[0] += 1
            caption = next()
            tkn[0] += 1
            players.append(Player(name, caption))
        elif command == "note":
            # Parser.java:90-100
            from_ = next()
            tkn[0] += 1
            if not dummy and lastMsg is not None:
                messages.append(lastMsg)
            dummy = newDummy
            newDummy = False
            lastMsg = Message(from_, from_, next(), " ", False, False)
            tkn[0] += 1
            lastMsg.srcLine = lineNo
        elif command == "opt":
            # Parser.java:101-106: values are not trimmed; later put wins
            name = next()
            tkn[0] += 1
            value = next()
            tkn[0] += 1
            opts[name] = value
        elif "->" in command:
            # Parser.java:107-132
            arrowIdx = command.index("->")
            from_ = javaTrim(command[:arrowIdx])
            to = javaTrim(command[arrowIdx + 2:])
            reply = False
            while tkn[0] < len(parts):
                if not dummy and lastMsg is not None:
                    messages.append(lastMsg)
                dummy = newDummy
                newDummy = False
                if reply:
                    lastMsg = Message(to, from_, next(), "-", False, True)
                else:
                    lastMsg = Message(from_, to, next(), "-", False, True)
                tkn[0] += 1
                lastMsg.srcLine = lineNo
                lastMsg.isReply = reply  # set before flipping (section 3.1)
                reply = not reply
        elif ".." in command:
            # Parser.java:133-145: filler '.', no arrows; extra fields ignored
            dotIdx = command.index("..")
            from_ = javaTrim(command[:dotIdx])
            to = javaTrim(command[dotIdx + 2:])
            if not dummy and lastMsg is not None:
                messages.append(lastMsg)
            dummy = newDummy
            newDummy = False
            lastMsg = Message(from_, to, next(), ".", False, False)
            tkn[0] += 1
            lastMsg.srcLine = lineNo
        elif "--" in command:
            # Parser.java:146-159: like .. but repeatLabel=true (filler '.' too)
            dotIdx = command.index("--")
            from_ = javaTrim(command[:dotIdx])
            to = javaTrim(command[dotIdx + 2:])
            if not dummy and lastMsg is not None:
                messages.append(lastMsg)
            dummy = newDummy
            newDummy = False
            lastMsg = Message(from_, to, next(), ".", False, False, True)
            tkn[0] += 1
            lastMsg.srcLine = lineNo
        # Parser.java:159: anything else: ignore the line, no error

    # Parser.java:161-164
    if not dummy and lastMsg is not None:
        messages.append(lastMsg)
    return f
