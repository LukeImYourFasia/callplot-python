"""Section 3.12.3 + 3.12.4: the inline SVG of the -html page.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Colors come from the --cpf-* CSS tokens with fallbacks so the SVG also
paints on its own.  Reply lines are dashed, media lines are teal without
arrowheads (DESIGN.md section 3.12.4 table).  All geometry comes from
layout.computeLayout so widths and drawing cannot drift apart.  Numbers
print through jsNum: the JS port interpolated JS numbers.
"""

from ...escape import escHtml
from ...jcompat import jsNum
from .layout import computeLayout


def kindClass(kind):
    """section 3.12.3: kind classes are ev-{kind}; mediaRepeat -> ev-media."""
    if kind == "mediaRepeat":
        return "media"
    return kind


def svgOn(model, out, prefix=""):
    L = computeLayout(model)
    bottom = L["H"] - L["HL_BOT"]
    out.println('<svg class="cpf-svg" xmlns="http://www.w3.org/2000/svg" '
                'width="' + jsNum(L["W"]) + '" height="' + jsNum(L["H"]) +
                '" viewBox="0 0 ' + jsNum(L["W"]) + " " + jsNum(L["H"]) +
                '" role="img" aria-label="Call flow diagram">')

    # lifelines: from just under the boxes down to the last band's bottom
    for xi in L["x"]:
        out.println('<line class="lf" x1="' + jsNum(xi) + '" x2="' + jsNum(xi) +
                    '" y1="' + jsNum(L["TOP"] + L["boxH"]) + '" y2="' +
                    jsNum(bottom) + '" stroke="var(--cpf-line, #b7c2cc)" '
                    'stroke-dasharray="1 3"/>')

    # participant boxes with their labels
    for i in range(len(model["participants"])):
        p = model["participants"][i]
        xi = L["x"][i]
        maxLen = 0
        for line in p["label"]:
            if len(line) > maxLen:
                maxLen = len(line)
        bw = maxLen * L["LABW"] + 16
        bh = len(p["label"]) * L["LH"] + 14
        out.println('<g class="pf">')
        out.println('<rect class="pf-box" x="' + jsNum(xi - bw / 2) + '" y="' +
                    jsNum(L["TOP"]) + '" width="' + jsNum(bw) + '" height="' +
                    jsNum(bh) + '" rx="4" fill="var(--cpf-head, #e8eef4)" '
                    'stroke="var(--cpf-line, #b7c2cc)"/>')
        for j in range(len(p["label"])):
            out.println('<text class="lb" x="' + jsNum(xi) + '" y="' +
                        jsNum(L["TOP"] + 11 + j * L["LH"]) +
                        '" fill="var(--cpf-ink, #17232e)" '
                        'font-family="ui-sans-serif, system-ui, sans-serif" '
                        'font-size="13" text-anchor="middle">' +
                        escHtml(p["label"][j]) + "</text>")
        out.println("</g>")

    # events, one group each (section 3.12.3 link contract + 3.12.4 hl rect)
    for i in range(len(model["events"])):
        e = model["events"][i]
        band = L["events"][i]
        y = band["top"]
        h = band["h"]
        out.println('<g class="ev ev-' + kindClass(e["kind"]) + '" id="' +
                    prefix + "flow-" + e["id"] + '">')
        out.println('<rect class="hl" x="0" y="' + jsNum(y - L["HL_DY"]) +
                    '" width="100%" height="' + jsNum(h) + '" fill="none"/>')

        lines = len(e["caption"])
        ay = y + lines * L["LH"] + 15  # the line sits inside the bottom 30px

        if e["kind"] != "note" and e["kind"] != "self":
            x1 = L["x"][e["from"]]
            x2 = L["x"][e["to"]]
            direction = 1 if x2 >= x1 else -1
            dash = ""
            color = "var(--cpf-ink, #17232e)"
            if e["kind"] == "reply":
                dash = ' stroke-dasharray="6 4"'
            elif e["kind"] == "media":
                color = "#008080"
                dash = ' stroke-dasharray="5 4"'
            elif e["kind"] == "mediaRepeat":
                color = "#008080"
                dash = ' stroke-dasharray="2 3"'
            out.println('<line class="ln" x1="' + jsNum(x1) + '" y1="' +
                        jsNum(ay) + '" x2="' + jsNum(x2 - direction * 9) +
                        '" y2="' + jsNum(ay) + '" stroke="' + color + '"' +
                        dash + "/>")
            if e["kind"] == "message" or e["kind"] == "reply":
                out.println('<polygon class="ah" points="' + jsNum(x2) + "," +
                            jsNum(ay) + " " + jsNum(x2 - direction * 9) + "," +
                            jsNum(ay - 4) + " " + jsNum(x2 - direction * 9) +
                            "," + jsNum(ay + 4) + '" fill="' + color + '"/>')
        elif e["kind"] == "self":
            x1 = L["x"][e["from"]]
            out.println('<polyline class="ln" points="' +
                        jsNum(x1) + "," + jsNum(ay - L["SELF_H"] / 2) + " " +
                        jsNum(x1 + L["SELF_W"]) + "," +
                        jsNum(ay - L["SELF_H"] / 2) + " " +
                        jsNum(x1 + L["SELF_W"]) + "," +
                        jsNum(ay + L["SELF_H"] / 2) + " " +
                        jsNum(x1) + "," + jsNum(ay + L["SELF_H"] / 2) +
                        '" stroke="var(--cpf-ink, #17232e)" fill="none"/>')
            out.println('<polygon class="ah" points="' + jsNum(x1) + "," +
                        jsNum(ay + L["SELF_H"] / 2) + " " + jsNum(x1 + 9) +
                        "," + jsNum(ay + L["SELF_H"] / 2 - 4) + " " +
                        jsNum(x1 + 9) + "," + jsNum(ay + L["SELF_H"] / 2 + 4) +
                        '" fill="var(--cpf-ink, #17232e)"/>')
        else:  # note
            x1 = L["x"][e["from"]]
            boxW = L["capLens"][i] * L["CW"] + L["NOTE_PAD"]
            out.println('<rect class="nt" x="' + jsNum(x1 + L["NOTE_DX"]) +
                        '" y="' + jsNum(y + L["NOTE_DY"]) + '" width="' +
                        jsNum(boxW) + '" height="' +
                        jsNum(lines * L["LH"] + 12) + '" rx="4" '
                        'fill="var(--cpf-note-fill, #fff8dd)" '
                        'stroke="var(--cpf-note-line, #c8b45f)"/>')

        # caption lines
        if e["kind"] == "self":
            tx = L["x"][e["from"]] + L["SELF_DX"]
            anchor = "start"
            mono = ""
        elif e["kind"] == "note":
            tx = (L["x"][e["from"]] + L["NOTE_DX"] +
                  (L["capLens"][i] * L["CW"] + L["NOTE_PAD"]) / 2)
            anchor = "middle"
            mono = ' font-family="ui-monospace, Menlo, Consolas, monospace"'
        else:
            tx = (L["x"][e["from"]] + L["x"][e["to"]]) / 2
            anchor = "middle"
            mono = ' font-family="ui-monospace, Menlo, Consolas, monospace"'
        for j in range(lines):
            out.println('<text class="cap" x="' + jsNum(tx) + '" y="' +
                        jsNum(y + 12 + j * L["LH"]) + '" text-anchor="' +
                        anchor + '" fill="var(--cpf-ink, #17232e)"' + mono +
                        ' font-size="12.5">' + escHtml(e["caption"][j]) +
                        "</text>")

        # badge: numbered events show (N) over a circle r=10, others a dot
        # r=5; the whole group links to the row (section 3.12.3)
        if e["kind"] == "note" or e["kind"] == "self":
            bx = L["x"][e["from"]]
            by = y + h / 2
        else:
            bx = (L["x"][e["from"]] + L["x"][e["to"]]) / 2
            by = ay
        out.println('<a class="badge" href="#' + prefix + "detail-" + e["id"] +
                    '">')
        if e["num"] is not None:
            out.println('<circle class="bdg" cx="' + jsNum(bx) + '" cy="' +
                        jsNum(by) + '" r="10" fill="var(--cpf-accent, '
                        '#2f6b8f)"/>')
            out.println('<text class="bn" x="' + jsNum(bx) + '" y="' +
                        jsNum(by + 4) + '" font-size="12" text-anchor="middle" '
                        'fill="var(--cpf-page, #ffffff)">' + str(e["num"]) +
                        "</text>")
        else:
            out.println('<circle class="bdg" cx="' + jsNum(bx) + '" cy="' +
                        jsNum(by) + '" r="5" fill="var(--cpf-accent, '
                        '#2f6b8f)"/>')
        out.println("</a>")
        out.println("</g>")

    out.println("</svg>")
