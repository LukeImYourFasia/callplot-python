"""DESIGN.md section 3.9: the IR model for the new outputs.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

build_model(flow) runs after flow.layout() and never changes Flow
(DESIGN.md section 3.9).  DESIGN-PYTHON.md section 2.5: the fixed shapes
Participant/Event/Model/Options are dataclasses, and the event kind is a
StrEnum whose values keep the DESIGN.md spelling (they are internal only).

Participant: alias, label (copy of caption lines), index
Event: id "e1"..., kind, from/to participant indexes, caption lines,
       num (display number or None), notes, comments, src_line
Model: title, participants, events, options
"""

from dataclasses import dataclass
from enum import StrEnum

from callplot.errors import IllegalArgumentError
from callplot.flow import Flow
from callplot.model import Message, is_note, is_self, is_undirected


class Kind(StrEnum):
    """IR event kinds (DESIGN.md section 3.9 step 4, first match wins)."""

    NOTE = "note"
    SELF = "self"
    MEDIA_REPEAT = "mediaRepeat"
    MEDIA = "media"
    REPLY = "reply"
    MESSAGE = "message"


@dataclass
class Participant:
    alias: str
    label: list[str]
    index: int


@dataclass
class Event:
    id: str
    kind: Kind
    from_: int
    to: int
    caption: list[str]
    num: int | None
    notes: list[str]
    comments: list[str]
    src_line: int


@dataclass
class Options:
    """Model options for the new outputs (section 3.9 step 7)."""

    message_numbering: bool
    note_numbering: bool
    html_layout: str | None  # raw opt/htmlLayout value; pick_layout validates


@dataclass
class Model:
    title: str | None
    participants: list[Participant]
    events: list[Event]
    options: Options


def build_model(f: Flow) -> Model:
    """Steps 1-7 of DESIGN.md section 3.9."""
    participants: list[Participant] = []
    alias_index: dict[str, int] = {}  # alias -> index of the FIRST player (step 3)
    for i in range(len(f.players)):
        p = f.players[i]
        participants.append(Participant(p.name, p.caption[:], i))
        if p.name not in alias_index:
            alias_index[p.name] = i

    # Step 3: same first-match rule and same error as Flow.column_of.
    def index_of(alias: str) -> int:
        idx = alias_index.get(alias)
        if idx is None:
            raise IllegalArgumentError("no player named " + alias)
        return idx

    message_numbering = f.get_do_numbering()
    note_numbering = f.get_do_note_numbering()

    events: list[Event] = []
    n = 1  # step 5 counter
    for i in range(len(f.messages)):
        m: Message = f.messages[i]
        from_ = index_of(m.from_)
        to = index_of(m.to)

        # Step 4: kind, first matching rule wins.
        if is_note(m):
            kind = Kind.NOTE
        elif is_self(m):
            kind = Kind.SELF
        elif is_undirected(m) and m.repeat_label:
            kind = Kind.MEDIA_REPEAT
        elif is_undirected(m):
            kind = Kind.MEDIA
        elif m.is_reply:
            kind = Kind.REPLY
        else:
            kind = Kind.MESSAGE

        # Step 5: num; step 6: id depends only on event order, never
        # options.
        num = None
        if message_numbering and (from_ != to or note_numbering):
            num = n
            n += 1

        events.append(
            Event(
                "e" + str(i + 1),
                kind,
                from_,
                to,
                m.caption[:],
                num,
                m.notes[:],
                m.comments[:],
                m.src_line,
            )
        )

    # Step 7: title and htmlLayout come from the input options (section 3.3).
    return Model(
        f.opts.get("title"),
        participants,
        events,
        Options(message_numbering, note_numbering, f.opts.get("htmlLayout")),
    )
