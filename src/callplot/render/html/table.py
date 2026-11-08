"""Section 3.12.5: the detail table of the -html page.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

One row per event, INCLUDING events without a number (the legacy tables
only had numbered ones).  Column 1 holds the back link and stays pinned
(sticky per section 3.12.3); the header row is sticky; kinds print as
pills; col2 keeps the htmltable3 meaning (caption lines + !! notes),
col3 its ! comments.
"""

from ...escape import escHtml


def labelOne(p):
    """label lines joined with a space (column 3)."""
    return escHtml(" ".join(p["label"]))


def kindWord(kind):
    """kind word for the pill: mediaRepeat prints as "repeat"."""
    return "repeat" if kind == "mediaRepeat" else kind


def backLink(event, prefix):
    """the back link text + aria-label (section 3.12.3)."""
    if event["num"] is not None:
        text = "\u2191 " + str(event["num"])
        aria = "Back to message " + str(event["num"]) + " in the diagram"
    else:
        text = "\u2191 \u00b7"
        aria = "Back to this event in the diagram"
    return ('<a class="back" href="#' + prefix + "flow-" + event["id"] +
            '" aria-label="' + escHtml(aria) + '">' + escHtml(text) + "</a>")


def tableOn(model, out, prefix):
    out.println('<table class="cpf-table">')
    out.println("<thead><tr><th>#</th><th>Kind</th><th>From \u2192 To</th>"
                "<th>Message and details</th><th>Notes</th><th>Line</th></tr></thead>")
    out.println("<tbody>")
    for e in model["events"]:
        out.println('<tr id="' + prefix + "detail-" + e["id"] + '">')

        # column 1: the back link, a row-header cell pinned at the left edge
        out.println('<th class="k" scope="row">' + backLink(e, prefix) + "</th>")

        # column 2: kind pill
        out.println('<td><span class="pill">' + kindWord(e["kind"]) + "</span></td>")

        # column 3: From -> To; media uses an ellipsis, a note shows
        # "note on A"
        a = labelOne(model["participants"][e["from"]])
        b = labelOne(model["participants"][e["to"]])
        if e["kind"] == "note":
            who = "note on " + a
        elif e["kind"] == "media" or e["kind"] == "mediaRepeat":
            who = a + " \u22ef " + b
        else:
            who = a + " \u2192 " + b
        out.println("<td>" + who + "</td>")

        # column 4: caption lines bold, then !! notes in mono, one per line
        parts = []
        for line in e["caption"]:
            parts.append("<strong>" + escHtml(line) + "</strong>")
        for note in e["notes"]:
            parts.append("<code>" + escHtml(note) + "</code>")
        out.println("<td>" + "<br>".join(parts) + "</td>")

        # column 5: ! comments as a list, an em-dash when there are none
        if len(e["comments"]) == 0:
            out.println("<td>\u2014</td>")
        else:
            items = []
            for c in e["comments"]:
                items.append("<li>" + escHtml(c) + "</li>")
            out.println("<td><ul>" + "".join(items) + "</ul></td>")

        # column 6: source line, right-aligned by CSS with tabular digits
        out.println("<td>" + str(e["srcLine"]) + "</td>")
        out.println("</tr>")
    out.println("</tbody>")
    out.println("</table>")
