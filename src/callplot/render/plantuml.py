"""Section 3.11: PlantUML from the IR.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Lines carry no indent; caption lines are joined with a literal \\n (backslash
+ n) which PlantUML draws as a line break; media arrows are teal with two
heads (DESIGN.md section 3.11 table).  notes and comments land as ' source
comments, hence the -slim companion rule (they are not drawn).
"""

from ..escape import escPlantuml


def eventText(event):
    """{text}: numbering prefix + escaped caption lines joined with \\n."""
    prefix = "" if event["num"] is None else "(" + str(event["num"]) + ") "
    parts = []
    for line in event["caption"]:
        parts.append(escPlantuml(line))
    return prefix + "\\n".join(parts)


def plantumlOn(model, out):
    out.println("@startuml")
    if model["title"] is not None:
        out.println("title " + escPlantuml(model["title"]))
    out.println("hide footbox")

    for i in range(len(model["participants"])):
        labels = []
        for line in model["participants"][i]["label"]:
            labels.append(escPlantuml(line))
        joined = "\\n".join(labels)
        if joined == "":
            # the pinned jar rejects participant "" as pN; declare it bare
            out.println("participant p" + str(i + 1))
        else:
            out.println("participant \"" + joined + "\" as p" + str(i + 1))

    for e in model["events"]:
        a = "p" + str(e["from"] + 1)
        b = "p" + str(e["to"] + 1)
        if e["kind"] == "note":
            out.println("note right of " + a + " : " + eventText(e))
        else:
            if e["kind"] == "reply":
                arrow = "-->"  # dashed (section 3.11)
            elif e["kind"] == "media" or e["kind"] == "mediaRepeat":
                arrow = "<-[#008080]->"  # teal, 2 heads (section 3.11)
            else:
                arrow = "->"  # message and self (section 3.11)
            out.println(a + " " + arrow + " " + b + " : " + eventText(e))
        for note in e["notes"]:
            out.println("' " + e["id"] + " note: " + escPlantuml(note))
        for comment in e["comments"]:
            out.println("' " + e["id"] + " comment: " + escPlantuml(comment))

    out.println("@enduml")
