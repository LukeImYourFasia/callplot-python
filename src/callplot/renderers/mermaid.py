"""Section 3.10: Mermaid sequenceDiagram from the IR (DESIGN.md section 3.10).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Every line except the front matter is indented by 4 spaces; the output ends
with one \\n (section 3.10).  No Mermaid autonumber: it cannot number notes
(section 3.10).  notes and comments land as %% source comments next to the
event, which is exactly why the format-fit rule emits a -slim companion for
inputs that use them (they are not drawn).

DESIGN-PYTHON.md section 2.5: the renderer entry ``mermaid_on`` reads the
IR dataclasses of callplot.ir and returns the whole page as one str; the
api writes it into the run's io.StringIO.
"""

from callplot.escape import esc_mermaid
from callplot.ir import Event, Kind, Model, Participant


def event_text(event: Event) -> str:
    """{text}: numbering prefix, then escaped caption lines joined with
    <br/>.  An empty caption becomes #nbsp; (section 3.10)."""
    prefix = "" if event.num is None else "(" + str(event.num) + ") "
    if len(event.caption) == 0:
        return prefix + "#nbsp;"
    parts = []
    for line in event.caption:
        parts.append(esc_mermaid(line))
    return prefix + "<br/>".join(parts)


def mermaid_on(model: Model) -> str:
    lines: list[str] = []
    if model.title is not None:
        lines.append("---")
        lines.append("title: " + esc_mermaid(model.title))
        lines.append("---")
    lines.append("sequenceDiagram")

    for i in range(len(model.participants)):
        participant: Participant = model.participants[i]
        labels = []
        for line in participant.label:
            labels.append(esc_mermaid(line))
        lines.append("    participant p" + str(i + 1) + " as " + "<br/>".join(labels))

    for e in model.events:
        a = "p" + str(e.from_ + 1)
        b = "p" + str(e.to + 1)
        if e.kind == Kind.NOTE:
            lines.append("    Note right of " + a + ": " + event_text(e))
        else:
            if e.kind == Kind.REPLY:
                arrow = "-->>"  # dashed with arrowhead (section 3.10)
            elif e.kind == Kind.MEDIA or e.kind == Kind.MEDIA_REPEAT:
                arrow = "-->"  # dotted, no arrowhead (section 3.10)
            else:
                arrow = "->>"  # message and self (section 3.10)
            lines.append("    " + a + arrow + b + ": " + event_text(e))
        for note in e.notes:
            lines.append("    %% " + e.id + " note: " + esc_mermaid(note))
        for comment in e.comments:
            lines.append("    %% " + e.id + " comment: " + esc_mermaid(comment))

    # ends with one \n (section 3.10)
    return "".join(line + "\n" for line in lines)
