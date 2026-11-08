"""Data model for players and messages.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Port of Player.java:35-97 (fields, ctor, digest) and Message.java:35-124
(fields, ctors, digest, addComment/addNote) plus the derived predicates of
DESIGN.md section 3.2.
Captions are stored as Python str indexed by code point, like Java char[]
indexed by code unit: the oracle corpus has no astral characters.
"""

from .jcompat import tokenize


def digest(captionRaw):
    """Shared caption digest (Player.java:74-90, Message.java:72-88).

    StringTokenizer on "^" drops empty tokens; PIC wants caption lines
    joined with quote-space-quote.  Returns (lines, captionString).
    """
    caption = tokenize(captionRaw, "^")
    captionString = ""
    for i in range(len(caption)):
        if i != 0:
            captionString += '" "'
        captionString += caption[i]
    return caption, captionString


class Player:
    """Flow.java:255-263 assigns column via setColumn; it defaults to 10."""

    def __init__(self, name, captionRaw):
        caption, captionString = digest(captionRaw)
        self.name = name  # alias is NOT trimmed (Parser.java:88)
        self.caption = caption
        self.captionString = captionString
        self.column = 10

    def getCaptionLines(self):
        return len(self.caption)  # Player.java:66-68


class Message:
    """Message.java:103-119 ctor; repeatLabel defaults false (99-101)."""

    def __init__(self, from_, to, captionRaw, filler, arrowFrom, arrowTo,
                 repeatLabel=False):
        caption, captionString = digest(captionRaw)
        self.from_ = from_  # Python keyword clash: Java's "from" is from_
        self.to = to
        # mutable: Graffle mutates caption[0] (section 3.8 #6)
        self.caption = caption
        self.captionString = captionString
        self.filler = filler  # '-', '.' or ' '
        self.arrowFrom = arrowFrom
        self.arrowTo = arrowTo
        self.repeatLabel = repeatLabel
        self.line = 0  # set by layout (setLine)
        self.myNumber = 0  # Java int default (Message.java:57)
        self.notes = []
        self.comments = []
        # New fields for the IR (section 3.1/3.2): 1-based input line that
        # created this message, and the alternating reply flag.  Compatible
        # outputs never read them, so they cannot change those outputs.
        self.srcLine = 0
        self.isReply = False

    def getLength(self):
        return len(self.caption)

    def addNote(self, note):
        self.notes.append(note)

    def addComment(self, comment):
        self.comments.append(comment)


def isSelf(m):
    return m.from_ == m.to


def isUndirected(m):
    return not m.arrowFrom and not m.arrowTo


def isNote(m):
    return isSelf(m) and isUndirected(m)  # made by note/... lines
