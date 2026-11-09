"""SVG renderer (DESIGN.md section 3.4.3).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Flow.java:462-513 + 562-578 (drawPictureOn SVG branches),
Player.java:127-148 (drawPictureOn SVG branch),
Message.java:226-231 (textout) and 253-279 (drawPictureOn SVG branch).
Fixed text is copied character for character from the Java literals;
numbers go through fmtI/fmtD per section 3.5's typing rule.
"""

import io

from callplot.constants import Mode
from callplot.context import RunContext
from callplot.flow import Flow
from callplot.jcompat import fmt_d, fmt_i, idiv, parse_java_int
from callplot.model import Message, Player, is_self, is_undirected


def svg_on(f: Flow, mode: Mode, ctx: RunContext) -> str:
    """Flow.java:462-513 + 562-578 for the SVG bit.

    DESIGN-PYTHON.md section 3.7: the entry builds its own io.StringIO and
    returns the whole output as one str.
    """
    out = io.StringIO()
    f.start_message_numbers()

    if (mode & Mode.XML) != 0:
        out.write(("<plot>") + "\n")  # Flow.java:454-457
        out.write(("<picture>") + "\n")

    # prologue, Flow.java:462-513
    out.write(("<?xml version='1.0'?>") + "\n")
    out.write(("<!DOCTYPE svg PUBLIC '-//W3C//DTD SVG 1.0//EN'") + "\n")
    out.write(("'http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd'>") + "\n")
    f.vml_y_size = f.get_total_height() * 2  # Flow.java:466-467
    f.vml_x_size = f.get_total_width()
    # Flow.java:468-469 compute vml_y_pt_size and vml_x_pt_size, but the SVG
    # branch never prints them; Java's dead int math has no observable effect.
    out.write(("<!-- totalHeight =" + fmt_i(f.get_total_height()) + "-->") + "\n")
    out.write(("<!-- totalWidth =" + fmt_i(f.get_total_width()) + "-->") + "\n")
    out.write(
        (
            "<svg width='"
            + fmt_i(idiv(f.get_total_width(), 10))
            + "in' height='"
            + fmt_i(idiv(f.get_total_height(), 6))
            + "in' viewBox='0 0 "
            + fmt_i(f.get_total_width())
            + " "
            + fmt_i(f.get_total_height())
            + "'>"
        )
        + "\n"
    )
    out.write(("") + "\n")
    out.write(("  <defs>") + "\n")
    out.write(("    <style type='text/css'><![CDATA[") + "\n")
    out.write(("      rect {") + "\n")
    out.write(("        fill: white;") + "\n")
    out.write(("        stroke: grey;") + "\n")
    out.write(("        stroke-width: 0.1") + "\n")
    out.write(("      }") + "\n")
    out.write(("      text {") + "\n")
    out.write(("        font-size: 1;") + "\n")
    out.write(("      }") + "\n")
    out.write(("      line {") + "\n")
    out.write(("        stroke: black;") + "\n")
    out.write(("        stroke-width: 0.1") + "\n")
    out.write(("      }") + "\n")
    out.write(("      line.dash {") + "\n")
    out.write(("        stroke-dasharray: 1,1;") + "\n")
    out.write(("        stroke: black;") + "\n")
    out.write(("        stroke-width: 0.1") + "\n")
    out.write(("      }") + "\n")
    out.write(("    ]]></style>") + "\n")
    out.write(("    <marker id='Triangle'") + "\n")
    out.write(("      viewBox='0 0 10 10' refX='0' refY='5' ") + "\n")
    out.write(("      markerUnits='strokeWidth'") + "\n")
    out.write(("      markerWidth='4' markerHeight='3'") + "\n")
    out.write(("      orient='auto'>") + "\n")
    out.write(("      <path d='M 0 0 L 10 5 L 0 10 z' />") + "\n")
    out.write(("    </marker>") + "\n")
    out.write(("    <filter id='dropShadow' x='-.1' y='-.1' width='200' height='120'>") + "\n")
    out.write(("       <feOffset in='SourceGraphic' dx='0' dy='0' result='orig' />") + "\n")
    out.write(
        ("       <feGaussianBlur in='SourceAlpha' stdDeviation='.3' result='shadow' />") + "\n"
    )
    out.write(("       <feOffset in='shadow' dx='0' dy='.1' result='movedShadow' />") + "\n")
    out.write(("       <feMerge>") + "\n")
    out.write(("           <feMergeNode in='movedShadow' />") + "\n")
    out.write(("           <feMergeNode in='orig' />") + "\n")
    out.write(("       </feMerge>") + "\n")
    out.write(("    </filter>") + "\n")
    out.write(("  </defs>") + "\n")

    for p in f.players:
        draw_player_svg(f, p, out, ctx)  # Flow.java:563-566
    for m in f.messages:
        draw_message_svg(f, m, out)  # Flow.java:568-571

    # epilogue, Flow.java:577-578
    out.write(("</svg>") + "\n")
    return out.getvalue()


def draw_player_svg(f: Flow, p: Player, out: io.StringIO, ctx: RunContext) -> None:
    """Player.java:127-148"""
    # Flow.java pct is a string parsed at draw time; bad values throw.
    wid = (f.get_column_pitch() * parse_java_int(f.get_vml_box_width_percentage())) / 100.0
    ht = 2.0
    # Java's ternary evaluates mynum++ only when stagger is on (section 3.6).
    # mynum is an int but % 2.0D promotes it, so the product is a double.
    if f.get_stagger():
        stagger = (ht + 2.0) * (ctx.mynum % 2.0)
        ctx.mynum += 1
    else:
        stagger = 0.0
    ycenter = stagger - ht / 2.0
    # int*int/int is Java int division, widened to double: prints as "N.0"
    center = idiv(p.column * f.get_vml_x_size(), f.get_total_width())

    out.write(
        "<rect x='"
        + fmt_d(center - wid / 2.0)
        + "' y='"
        + fmt_d(ycenter - ht / 2.0)
        + "' width='"
        + fmt_d(wid)
        + "' height='"
        + fmt_d(ht)
        + "' rx='.6' ry='.6' filter='url(#dropShadow)'>"
    )
    out.write("</rect>\n")

    for i in range(len(p.caption)):
        out.write(
            (
                " <text text-anchor='middle' y='"
                + fmt_d(ycenter + i + 0.4)
                + "' x='"
                + fmt_d(center)
                + "'>"
            )
            + "\n"
        )
        out.write((f.xml_escape(p.caption[i])) + "\n")
        out.write((" </text> ") + "\n")

    out.write(
        "<line x1='"
        + fmt_d(center)
        + "' y1='"
        + fmt_d(ycenter - ht / 2.0 + ht)
        + "' x2='"
        + fmt_d(center)
        + "' y2='"
        + fmt_i(f.get_vml_y_size())
        + "'>"
    )
    out.write("</line>\n")


def textout(out: io.StringIO, textx: float, texty: float, i: int, text: str) -> None:
    """Message.java:226-231 (textout).  Java's parameter is named `line` and
    shadows the Message.line field, so texty + line means texty + i."""
    out.write((" <text y='" + fmt_d(texty + i) + "' x='" + fmt_d(textx) + "'>") + "\n")
    out.write((text) + "\n")
    out.write((" </text> ") + "\n")


def draw_message_svg(f: Flow, m: Message, out: io.StringIO) -> None:
    """Message.java:253-279"""
    fx = f.column_of(m.from_)
    tx = f.column_of(m.to)
    startx = fx if fx < tx else tx
    textx = 0.2 + startx
    texty = -0.2 + m.line
    arrowx = 0.4

    if is_self(m):
        for i in range(len(m.caption)):
            textout(out, textx, texty, i, f.xml_escape(m.caption[i]))
    elif is_undirected(m):
        for i in range(len(m.caption)):
            textout(out, textx, texty, i, f.xml_escape(m.caption[i]))
        out.write(
            (
                " <line class='dash' x1='"
                + fmt_i(fx)
                + "' y1='"
                + fmt_i(m.line)
                + "' x2='"
                + fmt_i(tx)
                + "' y2='"
                + fmt_i(m.line)
                + "'/>"
            )
            + "\n"
        )
    else:
        for i in range(len(m.caption)):
            textout(out, textx, texty, i, f.xml_escape(m.caption[i]))
        out.write(
            (
                " <line marker-end='url(#Triangle)' x1='"
                + fmt_i(fx)
                + "' y1='"
                + fmt_i(m.line)
                + "' x2='"
                + fmt_d(tx + (-arrowx if tx > fx else arrowx))
                + "' y2='"
                + fmt_i(m.line)
                + "'/>"
            )
            + "\n"
        )
