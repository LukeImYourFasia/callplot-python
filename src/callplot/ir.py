"""DESIGN.md section 3.9: the IR model for the new outputs.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

buildModel(flow) runs after flow.layout() and never changes Flow.

Participant: {alias, label (copy of caption lines), index}
Event: {id 'e1'.., kind, from/to participant indexes, caption lines,
        num (display number or None), notes, comments, srcLine}
Model: {title, participants, events, options}
"""

from .jcompat import IllegalArgumentError
from .model import isNote, isSelf, isUndirected


def buildModel(f):
    # Step 1: participants, one per player, in order (labels copied).
    participants = []
    aliasIndex = {}  # alias -> index of the FIRST player (step 3)
    for i in range(len(f.players)):
        p = f.players[i]
        participants.append({"alias": p.name, "label": p.caption[:], "index": i})
        if p.name not in aliasIndex:
            aliasIndex[p.name] = i

    # Step 3: same first-match rule and same error as Flow.columnOf.
    def indexOf(alias):
        idx = aliasIndex.get(alias)
        if idx is None:
            raise IllegalArgumentError("no player named " + alias)
        return idx

    messageNumbering = f.getDoNumbering()
    noteNumbering = f.getDoNoteNumbering()

    events = []
    n = 1  # step 5 counter
    for i in range(len(f.messages)):
        m = f.messages[i]
        from_ = indexOf(m.from_)
        to = indexOf(m.to)

        # Step 4: kind, first matching rule wins.
        if isNote(m):
            kind = "note"
        elif isSelf(m):
            kind = "self"
        elif isUndirected(m) and m.repeatLabel:
            kind = "mediaRepeat"
        elif isUndirected(m):
            kind = "media"
        elif m.isReply:
            kind = "reply"
        else:
            kind = "message"

        # Step 5: num; step 6: id depends only on event order, never options.
        num = None
        if messageNumbering and (from_ != to or noteNumbering):
            num = n
            n += 1

        events.append({
            "id": "e" + str(i + 1),
            "kind": kind,
            "from": from_,
            "to": to,
            "caption": m.caption[:],
            "num": num,
            "notes": m.notes[:],
            "comments": m.comments[:],
            "srcLine": m.srcLine,
        })

    # Step 7: title and htmlLayout come from the input options (section 3.3).
    return {
        "title": f.opts.get("title"),
        "participants": participants,
        "events": events,
        "options": {
            "messageNumbering": messageNumbering,
            "noteNumbering": noteNumbering,
            "htmlLayout": f.opts.get("htmlLayout"),
        },
    }
