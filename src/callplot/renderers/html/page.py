"""Section 3.12.2 + 3.12.6: the whole -html page as one self-contained file.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

No JavaScript, nothing loaded from the network.  The page structure is the
contract in section 3.12.2; the two layouts come from a hidden radio
switch, and the chosen option only decides which radio starts checked.
A bad htmlLayout value from either source throws before any byte is out.

DESIGN-PYTHON.md section 2.2: this file holds JS's ``html/page.js`` and
``html/table.js`` merged (the detail table belongs to the page, so the
package holds no table.py); the entry ``page_on`` returns the whole page
as one ``str`` built in an ``io.StringIO`` (section 3.7 rule 1).  Fixed
page text copied from JS ``page.js`` and ``table.js`` byte for byte.
"""

import io

from callplot.escape import esc_html
from callplot.ir import Event, Kind, Model, Participant
from callplot.options import HtmlLayout, RenderOptions, parse_html_layout
from callplot.renderers.html.style import CSS
from callplot.renderers.html.svg import svg_on


def pick_layout(model: Model, options: RenderOptions) -> HtmlLayout:
    """Layout choice, section 3.12.6 order: the API option forces a layout
    (it clears any earlier opt line, like JS's undefined); otherwise the
    input's opt line is validated; otherwise topbottom.  A bad value from
    either source throws before any byte is out."""
    if options.html_layout is not None:
        return options.html_layout
    raw = model.options.html_layout
    if raw is None:
        return HtmlLayout.TOPBOTTOM
    return parse_html_layout(raw)


def label_one(p: Participant) -> str:
    """label lines joined with a space (column 3)."""
    return esc_html(" ".join(p.label))


def kind_word(kind: Kind) -> str:
    """kind word for the pill: mediaRepeat prints as "repeat"."""
    return "repeat" if kind == Kind.MEDIA_REPEAT else kind


def back_link(e: Event, prefix: str) -> str:
    """the back link text + aria-label (section 3.12.3)."""
    if e.num is not None:
        text = "\u2191 " + str(e.num)
        aria = "Back to message " + str(e.num) + " in the diagram"
    else:
        text = "\u2191 \u00b7"
        aria = "Back to this event in the diagram"
    return (
        '<a class="back" href="#'
        + prefix
        + "flow-"
        + e.id
        + '" aria-label="'
        + esc_html(aria)
        + '">'
        + esc_html(text)
        + "</a>"
    )


def detail_table(out: io.StringIO, model: Model, prefix: str) -> None:
    """One row per event, INCLUDING events without a number (the legacy
    tables only had numbered ones).  Column 1 holds the back link and stays
    pinned (sticky per section 3.12.3); the header row is sticky; kinds
    print as pills; col2 keeps the htmltable3 meaning (caption lines + !!
    notes), col3 its ! comments.  (JS's html/table.js, folded in here.)"""

    def line(s: str) -> None:
        out.write(s + "\n")

    line('<table class="cpf-table">')
    line(
        "<thead><tr><th>#</th><th>Kind</th><th>From \u2192 To</th>"
        "<th>Message and details</th><th>Notes</th><th>Line</th></tr></thead>"
    )
    line("<tbody>")
    for e in model.events:
        line('<tr id="' + prefix + "detail-" + e.id + '">')

        # column 1: the back link, a row-header cell pinned at the left edge
        line('<th class="k" scope="row">' + back_link(e, prefix) + "</th>")

        # column 2: kind pill
        line('<td><span class="pill">' + kind_word(e.kind) + "</span></td>")

        # column 3: From -> To; media uses an ellipsis, a note shows
        # "note on A"
        a = label_one(model.participants[e.from_])
        b = label_one(model.participants[e.to])
        if e.kind == Kind.NOTE:
            who = "note on " + a
        elif e.kind == Kind.MEDIA or e.kind == Kind.MEDIA_REPEAT:
            who = a + " \u22ef " + b
        else:
            who = a + " \u2192 " + b
        line("<td>" + who + "</td>")

        # column 4: caption lines bold, then !! notes in mono, one per line
        parts = []
        for cap_line in e.caption:
            parts.append("<strong>" + esc_html(cap_line) + "</strong>")
        for note in e.notes:
            parts.append("<code>" + esc_html(note) + "</code>")
        line("<td>" + "<br>".join(parts) + "</td>")

        # column 5: ! comments as a list, an em-dash when there are none
        if len(e.comments) == 0:
            line("<td>\u2014</td>")
        else:
            items = []
            for c in e.comments:
                items.append("<li>" + esc_html(c) + "</li>")
            line("<td><ul>" + "".join(items) + "</ul></td>")

        # column 6: source line, right-aligned by CSS with tabular digits
        line("<td>" + str(e.src_line) + "</td>")
        line("</tr>")
    line("</tbody>")
    line("</table>")


def page_on(model: Model, options: RenderOptions) -> str:
    """The whole -html document (section 3.12.2 contract + 3.12.6)."""
    layout = pick_layout(model, options)
    prefix = options.id_prefix
    title = model.title if model.title is not None else "Call flow"
    esc_title = esc_html(title)
    out = io.StringIO()

    def line(s: str) -> None:
        out.write(s + "\n")

    line("<!doctype html>")
    line('<html lang="en">')
    line("<head>")
    line('<meta charset="utf-8">')
    line('<meta name="viewport" content="width=device-width, initial-scale=1">')
    line("<title>" + esc_title + "</title>")
    line("<style>")
    line(CSS)
    line("</style>")
    line("</head>")
    line("<body>")
    line('<div class="cpf">')

    # the layout switch (section 3.12.6): both radios always present, the
    # chosen one starts checked; hidden visually but keyboard-reachable
    tb = " checked" if layout == HtmlLayout.TOPBOTTOM else ""
    sbs = " checked" if layout == HtmlLayout.SIDEBYSIDE else ""
    line(
        '<input type="radio" name="'
        + prefix
        + 'layout" id="'
        + prefix
        + 'lay-tb" class="cpf-radio"'
        + tb
        + ">"
    )
    line(
        '<input type="radio" name="'
        + prefix
        + 'layout" id="'
        + prefix
        + 'lay-sbs" class="cpf-radio"'
        + sbs
        + ">"
    )

    line('<header class="cpf-head">')
    line("<h1>" + esc_title + "</h1>")
    line(
        "<p>"
        + str(len(model.participants))
        + " participants \u00b7 "
        + str(len(model.events))
        + " events</p>"
    )
    line('<div class="cpf-switch" role="group" aria-label="Layout">')
    line('<label for="' + prefix + 'lay-tb">Top and bottom</label>')
    line('<label for="' + prefix + 'lay-sbs">Side by side</label>')
    line("</div>")
    line("</header>")

    line('<div class="cpf-main">')
    line('<section class="cpf-flow" aria-label="Diagram"><div class="cpf-scroll">')
    svg_on(model, out, prefix)
    line("</div></section>")
    line('<section class="cpf-detail" aria-label="Details"><div class="cpf-tscroll">')
    detail_table(out, model, prefix)
    line("</div></section>")
    line("</div>")

    line("</div>")
    line("</body>")
    line("</html>")
    return out.getvalue()
