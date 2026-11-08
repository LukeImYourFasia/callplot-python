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
"""

from ...jcompat import IllegalArgumentError
from ...escape import escHtml
from ...out import Out
from .style import CSS
from .svg import svgOn
from .table import tableOn


def pickLayout(model, opts):
    """Layout choice, section 3.12.6 order: API option, then input opt line,
    then topbottom; a bad value throws before any output."""
    # a missing/None option does not force: the flag -html clears any earlier
    # force (JS's undefined), so the file's opt/htmlLayout then decides
    raw = opts.get("htmlLayout")
    if raw is None:
        raw = model["options"]["htmlLayout"]
    if raw is None:
        return "topbottom"
    if raw == "topbottom" or raw == "sidebyside":
        return raw
    raise IllegalArgumentError("Bad value for htmlLayout option")


def pageOn(model, out, opts=None):
    if opts is None:
        opts = {}
    layout = pickLayout(model, opts)
    prefix = opts["idPrefix"] if "idPrefix" in opts else ""
    titleRaw = opts["title"] if "title" in opts else model["title"]
    title = titleRaw if titleRaw is not None else "Call flow"
    escTitle = escHtml(title)

    out.println("<!doctype html>")
    out.println('<html lang="en">')
    out.println("<head>")
    out.println('<meta charset="utf-8">')
    out.println('<meta name="viewport" content="width=device-width, initial-scale=1">')
    out.println("<title>" + escTitle + "</title>")
    out.println("<style>")
    out.println(CSS)
    out.println("</style>")
    out.println("</head>")
    out.println("<body>")
    out.println('<div class="cpf">')

    # the layout switch (section 3.12.6): both radios always present, the
    # chosen one starts checked; hidden visually but keyboard-reachable
    tb = " checked" if layout == "topbottom" else ""
    sbs = " checked" if layout == "sidebyside" else ""
    out.println('<input type="radio" name="' + prefix + 'layout" id="' +
                prefix + 'lay-tb" class="cpf-radio"' + tb + ">")
    out.println('<input type="radio" name="' + prefix + 'layout" id="' +
                prefix + 'lay-sbs" class="cpf-radio"' + sbs + ">")

    out.println('<header class="cpf-head">')
    out.println("<h1>" + escTitle + "</h1>")
    out.println("<p>" + str(len(model["participants"])) +
                " participants \u00b7 " + str(len(model["events"])) +
                " events</p>")
    out.println('<div class="cpf-switch" role="group" aria-label="Layout">')
    out.println('<label for="' + prefix + 'lay-tb">Top and bottom</label>')
    out.println('<label for="' + prefix + 'lay-sbs">Side by side</label>')
    out.println("</div>")
    out.println("</header>")

    out.println('<div class="cpf-main">')
    out.println('<section class="cpf-flow" aria-label="Diagram">'
                '<div class="cpf-scroll">')
    svgOn(model, out, prefix)
    out.println("</div></section>")
    out.println('<section class="cpf-detail" aria-label="Details">'
                '<div class="cpf-tscroll">')
    tableOn(model, out, prefix)
    out.println("</div></section>")
    out.println("</div>")

    out.println("</div>")
    out.println("</body>")
    out.println("</html>")


def page(model, opts=None):
    """the page for the API: same pageOn, string result."""
    out = Out()
    pageOn(model, out, opts)
    return out.toString()
