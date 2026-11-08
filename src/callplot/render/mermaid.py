"""Section 3.10: Mermaid sequenceDiagram from the IR.

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
"""

from ..escape import escMermaid


def eventText(event):
    """{text}: numbering prefix, then escaped caption lines joined with
    <br/>.  An empty caption becomes #nbsp; (section 3.10)."""
    prefix = "" if event["num"] is None else "(" + str(event["num"]) + ") "
    if len(event["caption"]) == 0:
        return prefix + "#nbsp;"
    parts = []
    for line in event["caption"]:
        parts.append(escMermaid(line))
    return prefix + "<br/>".join(parts)


def mermaidOn(model, out):
    lines = []
    if model["title"] is not None:
        lines.append("---")
        lines.append("title: " + escMermaid(model["title"]))
        lines.append("---")
    lines.append("sequenceDiagram")

    for i in range(len(model["participants"])):
        labels = []
        for line in model["participants"][i]["label"]:
            labels.append(escMermaid(line))
        lines.append("    participant p" + str(i + 1) + " as " +
                     "<br/>".join(labels))

    for e in model["events"]:
        a = "p" + str(e["from"] + 1)
        b = "p" + str(e["to"] + 1)
        if e["kind"] == "note":
            lines.append("    Note right of " + a + ": " + eventText(e))
        else:
            if e["kind"] == "reply":
                arrow = "-->>"  # dashed with arrowhead (section 3.10)
            elif e["kind"] == "media" or e["kind"] == "mediaRepeat":
                arrow = "-->"  # dotted, no arrowhead (section 3.10)
            else:
                arrow = "->>"  # message and self (section 3.10)
            lines.append("    " + a + arrow + b + ": " + eventText(e))
        for note in e["notes"]:
            lines.append("    %% " + e["id"] + " note: " + escMermaid(note))
        for comment in e["comments"]:
            lines.append("    %% " + e["id"] + " comment: " +
                         escMermaid(comment))

    for l in lines:
        out.println(l)  # ends with one \n (section 3.10)
