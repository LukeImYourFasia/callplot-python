"""Data model for players and messages (DESIGN.md section 3.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Port of Player.java:35-97 (fields, ctor, digest) and Message.java:35-124
(fields, ctors, digest, addComment/addNote) plus the derived predicates of
DESIGN.md section 3.2.  DESIGN-PYTHON.md section 2.5: fixed shapes are
``@dataclass(slots=True)`` classes with plain fields; the Java field
``from`` is ``from_`` (a Python keyword clash).  Captions are unit strings
(jcompat section 3.2): len() counts UTF-16 code units like Java.
"""

from dataclasses import dataclass, field

from callplot.jcompat import tokenize


def digest(caption_raw: str) -> tuple[list[str], str]:
    """Shared caption digest (Player.java:74-90, Message.java:72-88).

    StringTokenizer on "^" drops empty tokens; PIC wants caption lines
    joined with quote-space-quote.  Returns (lines, caption_string).
    """
    caption = tokenize(caption_raw, "^")
    return caption, '" "'.join(caption)


@dataclass(slots=True)
class Player:
    """Flow.java:255-263 assigns column via setColumn; it defaults to 10."""

    name: str = ""
    caption_raw: str = ""  # ctor input: the raw "a^b" caption (Player.java:74-90)
    caption: list[str] = field(default_factory=list)
    caption_string: str = ""
    column: int = 10

    def __post_init__(self) -> None:
        self.caption, self.caption_string = digest(self.caption_raw)

    def get_caption_lines(self) -> int:
        return len(self.caption)  # Player.java:66-68


@dataclass(slots=True)
class Message:
    """Message.java:103-119 ctor; repeat_label defaults false (99-101)."""

    from_: str = ""
    to: str = ""
    caption_raw: str = ""  # ctor input: the raw "a^b" caption
    filler: str = "-"
    arrow_from: bool = False
    arrow_to: bool = True
    repeat_label: bool = False
    line: int = 0  # set by layout (setLine)
    my_number: int = 0  # Java int default (Message.java:57)
    notes: list[str] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)
    # New fields for the IR (DESIGN.md sections 3.1/3.2): 1-based input
    # line that created this message, and the alternating reply flag.
    # Compatible outputs never read them, so they cannot change those
    # outputs.
    src_line: int = 0
    is_reply: bool = False
    caption: list[str] = field(default_factory=list)
    caption_string: str = ""

    def __post_init__(self) -> None:
        self.caption, self.caption_string = digest(self.caption_raw)

    def get_length(self) -> int:
        return len(self.caption)

    def add_note(self, note: str) -> None:
        self.notes.append(note)

    def add_comment(self, comment: str) -> None:
        self.comments.append(comment)


def is_self(m: Message) -> bool:
    return m.from_ == m.to


def is_undirected(m: Message) -> bool:
    return not m.arrow_from and not m.arrow_to


def is_note(m: Message) -> bool:
    return is_self(m) and is_undirected(m)  # made by note/... lines
