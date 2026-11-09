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

import io

from callplot.escape import esc_html
from callplot.ir import Kind, Model
from callplot.jcompat import js_num
from callplot.renderers.html.layout import compute_layout


def kind_class(kind: Kind) -> str:
    """section 3.12.3: kind classes are ev-{kind}; mediaRepeat -> ev-media."""
    if kind == "mediaRepeat":
        return "media"
    return kind


def svg_on(model: Model, out: io.StringIO, prefix: str = "") -> None:
    lay = compute_layout(model)
    bottom = lay["H"] - lay["HL_BOT"]
    out.write(
        (
            '<svg class="cpf-svg" xmlns="http://www.w3.org/2000/svg" '
            'width="'
            + js_num(lay["W"])
            + '" height="'
            + js_num(lay["H"])
            + '" viewBox="0 0 '
            + js_num(lay["W"])
            + " "
            + js_num(lay["H"])
            + '" role="img" aria-label="Call flow diagram">'
        )
        + "\n"
    )

    # lifelines: from just under the boxes down to the last band's bottom
    for xi in lay["x"]:
        out.write(
            (
                '<line class="lf" x1="'
                + js_num(xi)
                + '" x2="'
                + js_num(xi)
                + '" y1="'
                + js_num(lay["TOP"] + lay["boxH"])
                + '" y2="'
                + js_num(bottom)
                + '" stroke="var(--cpf-line, #b7c2cc)" '
                'stroke-dasharray="1 3"/>'
            )
            + "\n"
        )

    # participant boxes with their labels
    for i in range(len(model.participants)):
        p = model.participants[i]
        xi = lay["x"][i]
        max_len = 0
        for line in p.label:
            if len(line) > max_len:
                max_len = len(line)
        bw = max_len * lay["LABW"] + 16
        bh = len(p.label) * lay["LH"] + 14
        out.write(('<g class="pf">') + "\n")
        out.write(
            (
                '<rect class="pf-box" x="'
                + js_num(xi - bw / 2)
                + '" y="'
                + js_num(lay["TOP"])
                + '" width="'
                + js_num(bw)
                + '" height="'
                + js_num(bh)
                + '" rx="4" fill="var(--cpf-head, #e8eef4)" '
                'stroke="var(--cpf-line, #b7c2cc)"/>'
            )
            + "\n"
        )
        for j in range(len(p.label)):
            out.write(
                (
                    '<text class="lb" x="'
                    + js_num(xi)
                    + '" y="'
                    + js_num(lay["TOP"] + 11 + j * lay["LH"])
                    + '" fill="var(--cpf-ink, #17232e)" '
                    'font-family="ui-sans-serif, system-ui, sans-serif" '
                    'font-size="13" text-anchor="middle">' + esc_html(p.label[j]) + "</text>"
                )
                + "\n"
            )
        out.write(("</g>") + "\n")

    # events, one group each (section 3.12.3 link contract + 3.12.4 hl rect)
    for i in range(len(model.events)):
        e = model.events[i]
        band = lay["events"][i]
        y = band["top"]
        h = band["h"]
        out.write(
            ('<g class="ev ev-' + kind_class(e.kind) + '" id="' + prefix + "flow-" + e.id + '">')
            + "\n"
        )
        out.write(
            (
                '<rect class="hl" x="0" y="'
                + js_num(y - lay["HL_DY"])
                + '" width="100%" height="'
                + js_num(h)
                + '" fill="none"/>'
            )
            + "\n"
        )

        lines = len(e.caption)
        ay = y + lines * lay["LH"] + 15  # the line sits inside the bottom 30px

        if e.kind != "note" and e.kind != "self":
            x1 = lay["x"][e.from_]
            x2 = lay["x"][e.to]
            direction = 1 if x2 >= x1 else -1
            dash = ""
            color = "var(--cpf-ink, #17232e)"
            if e.kind == Kind.REPLY:
                dash = ' stroke-dasharray="6 4"'
            elif e.kind == Kind.MEDIA:
                color = "#008080"
                dash = ' stroke-dasharray="5 4"'
            elif e.kind == Kind.MEDIA_REPEAT:
                color = "#008080"
                dash = ' stroke-dasharray="2 3"'
            out.write(
                (
                    '<line class="ln" x1="'
                    + js_num(x1)
                    + '" y1="'
                    + js_num(ay)
                    + '" x2="'
                    + js_num(x2 - direction * 9)
                    + '" y2="'
                    + js_num(ay)
                    + '" stroke="'
                    + color
                    + '"'
                    + dash
                    + "/>"
                )
                + "\n"
            )
            if e.kind == Kind.MESSAGE or e.kind == Kind.REPLY:
                out.write(
                    (
                        '<polygon class="ah" points="'
                        + js_num(x2)
                        + ","
                        + js_num(ay)
                        + " "
                        + js_num(x2 - direction * 9)
                        + ","
                        + js_num(ay - 4)
                        + " "
                        + js_num(x2 - direction * 9)
                        + ","
                        + js_num(ay + 4)
                        + '" fill="'
                        + color
                        + '"/>'
                    )
                    + "\n"
                )
        elif e.kind == Kind.SELF:
            x1 = lay["x"][e.from_]
            out.write(
                (
                    '<polyline class="ln" points="'
                    + js_num(x1)
                    + ","
                    + js_num(ay - lay["SELF_H"] / 2)
                    + " "
                    + js_num(x1 + lay["SELF_W"])
                    + ","
                    + js_num(ay - lay["SELF_H"] / 2)
                    + " "
                    + js_num(x1 + lay["SELF_W"])
                    + ","
                    + js_num(ay + lay["SELF_H"] / 2)
                    + " "
                    + js_num(x1)
                    + ","
                    + js_num(ay + lay["SELF_H"] / 2)
                    + '" stroke="var(--cpf-ink, #17232e)" fill="none"/>'
                )
                + "\n"
            )
            out.write(
                (
                    '<polygon class="ah" points="'
                    + js_num(x1)
                    + ","
                    + js_num(ay + lay["SELF_H"] / 2)
                    + " "
                    + js_num(x1 + 9)
                    + ","
                    + js_num(ay + lay["SELF_H"] / 2 - 4)
                    + " "
                    + js_num(x1 + 9)
                    + ","
                    + js_num(ay + lay["SELF_H"] / 2 + 4)
                    + '" fill="var(--cpf-ink, #17232e)"/>'
                )
                + "\n"
            )
        else:  # note
            x1 = lay["x"][e.from_]
            box_w = lay["capLens"][i] * lay["CW"] + lay["NOTE_PAD"]
            out.write(
                (
                    '<rect class="nt" x="'
                    + js_num(x1 + lay["NOTE_DX"])
                    + '" y="'
                    + js_num(y + lay["NOTE_DY"])
                    + '" width="'
                    + js_num(box_w)
                    + '" height="'
                    + js_num(lines * lay["LH"] + 12)
                    + '" rx="4" '
                    'fill="var(--cpf-note-fill, #fff8dd)" '
                    'stroke="var(--cpf-note-line, #c8b45f)"/>'
                )
                + "\n"
            )

        # caption lines
        if e.kind == Kind.SELF:
            tx = lay["x"][e.from_] + lay["SELF_DX"]
            anchor = "start"
            mono = ""
        elif e.kind == Kind.NOTE:
            tx = (
                lay["x"][e.from_]
                + lay["NOTE_DX"]
                + (lay["capLens"][i] * lay["CW"] + lay["NOTE_PAD"]) / 2
            )
            anchor = "middle"
            mono = ' font-family="ui-monospace, Menlo, Consolas, monospace"'
        else:
            tx = (lay["x"][e.from_] + lay["x"][e.to]) / 2
            anchor = "middle"
            mono = ' font-family="ui-monospace, Menlo, Consolas, monospace"'
        for j in range(lines):
            out.write(
                (
                    '<text class="cap" x="'
                    + js_num(tx)
                    + '" y="'
                    + js_num(y + 12 + j * lay["LH"])
                    + '" text-anchor="'
                    + anchor
                    + '" fill="var(--cpf-ink, #17232e)"'
                    + mono
                    + ' font-size="12.5">'
                    + esc_html(e.caption[j])
                    + "</text>"
                )
                + "\n"
            )

        # badge: numbered events show (N) over a circle r=10, others a dot
        # r=5; the whole group links to the row (section 3.12.3)
        if e.kind == Kind.NOTE or e.kind == Kind.SELF:
            bx = lay["x"][e.from_]
            by = y + h / 2
        else:
            bx = (lay["x"][e.from_] + lay["x"][e.to]) / 2
            by = ay
        out.write(('<a class="badge" href="#' + prefix + "detail-" + e.id + '">') + "\n")
        if e.num is not None:
            out.write(
                (
                    '<circle class="bdg" cx="'
                    + js_num(bx)
                    + '" cy="'
                    + js_num(by)
                    + '" r="10" fill="var(--cpf-accent, '
                    '#2f6b8f)"/>'
                )
                + "\n"
            )
            out.write(
                (
                    '<text class="bn" x="'
                    + js_num(bx)
                    + '" y="'
                    + js_num(by + 4)
                    + '" font-size="12" text-anchor="middle" '
                    'fill="var(--cpf-page, #ffffff)">' + str(e.num) + "</text>"
                )
                + "\n"
            )
        else:
            out.write(
                (
                    '<circle class="bdg" cx="'
                    + js_num(bx)
                    + '" cy="'
                    + js_num(by)
                    + '" r="5" fill="var(--cpf-accent, '
                    '#2f6b8f)"/>'
                )
                + "\n"
            )
        out.write(("</a>") + "\n")
        out.write(("</g>") + "\n")

    out.write(("</svg>") + "\n")
