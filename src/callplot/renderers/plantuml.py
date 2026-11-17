"""Section 3.11: PlantUML from the IR (DESIGN.md section 3.11).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Lines carry no indent; caption lines are joined with a literal \\n (backslash
+ n) which PlantUML draws as a line break; media arrows are teal with two
heads (DESIGN.md section 3.11 table).  notes and comments land as ' source
comments, hence the -slim companion rule (they are not drawn).

DESIGN-PYTHON.md section 2.5: the renderer entry ``plantuml_on`` reads the
IR dataclasses of callplot.ir and returns the whole page as one str.
"""

from callplot.escape import esc_plantuml
from callplot.ir import Event, Kind, Model, Participant


def event_text(event: Event) -> str:
    """{text}: numbering prefix + escaped caption lines joined with \\n."""
    prefix = "" if event.num is None else "(" + str(event.num) + ") "
    parts = []
    for line in event.caption:
        parts.append(esc_plantuml(line))
    return prefix + "\\n".join(parts)


def plantuml_on(model: Model) -> str:
    lines: list[str] = ["@startuml"]
    if model.title is not None:
        lines.append("title " + esc_plantuml(model.title))
    lines.append("hide footbox")

    for i in range(len(model.participants)):
        participant: Participant = model.participants[i]
        labels = []
        for line in participant.label:
            labels.append(esc_plantuml(line))
        joined = "\\n".join(labels)
        if joined == "":
            # the pinned jar rejects participant "" as pN; declare it bare
            lines.append("participant p" + str(i + 1))
        else:
            lines.append('participant "' + joined + '" as p' + str(i + 1))

    for e in model.events:
        a = "p" + str(e.from_ + 1)
        b = "p" + str(e.to + 1)
        if e.kind == Kind.NOTE:
            lines.append("note right of " + a + " : " + event_text(e))
        else:
            if e.kind == Kind.REPLY:
                arrow = "-->"  # dashed (section 3.11)
            elif e.kind == Kind.MEDIA or e.kind == Kind.MEDIA_REPEAT:
                arrow = "<-[#008080]->"  # teal, 2 heads (section 3.11)
            else:
                arrow = "->"  # message and self (section 3.11)
            lines.append(a + " " + arrow + " " + b + " : " + event_text(e))
        for note in e.notes:
            lines.append("' " + e.id + " note: " + esc_plantuml(note))
        for comment in e.comments:
            lines.append("' " + e.id + " comment: " + esc_plantuml(comment))

    lines.append("@enduml")
    return "".join(line + "\n" for line in lines)
