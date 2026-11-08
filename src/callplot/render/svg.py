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

from ..constants import MODES
from ..jcompat import fmtD, fmtI, idiv, parseJavaInt
from ..model import isSelf, isUndirected


def svgOn(f, out, mode, ctx):
    """Flow.java:462-513 + 562-578 for the SVG bit."""
    f.startMessageNumbers()

    if (mode & MODES["XML"]) != 0:
        out.println("<plot>")  # Flow.java:454-457
        out.println("<picture>")

    # prologue, Flow.java:462-513
    out.println("<?xml version='1.0'?>")
    out.println("<!DOCTYPE svg PUBLIC '-//W3C//DTD SVG 1.0//EN'")
    out.println("'http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd'>")
    f.vmlYSize = f.getTotalHeight() * 2  # Flow.java:466-467
    f.vmlXSize = f.getTotalWidth()
    # Flow.java:468-469 compute vml_y_pt_size and vml_x_pt_size, but the SVG
    # branch never prints them; Java's dead int math has no observable effect.
    out.println("<!-- totalHeight =" + fmtI(f.getTotalHeight()) + "-->")
    out.println("<!-- totalWidth =" + fmtI(f.getTotalWidth()) + "-->")
    out.println("<svg width='" + fmtI(idiv(f.getTotalWidth(), 10)) + "in' height='" +
                fmtI(idiv(f.getTotalHeight(), 6)) + "in' viewBox='0 0 " +
                fmtI(f.getTotalWidth()) + " " + fmtI(f.getTotalHeight()) + "'>")
    out.println("")
    out.println("  <defs>")
    out.println("    <style type='text/css'><![CDATA[")
    out.println("      rect {")
    out.println("        fill: white;")
    out.println("        stroke: grey;")
    out.println("        stroke-width: 0.1")
    out.println("      }")
    out.println("      text {")
    out.println("        font-size: 1;")
    out.println("      }")
    out.println("      line {")
    out.println("        stroke: black;")
    out.println("        stroke-width: 0.1")
    out.println("      }")
    out.println("      line.dash {")
    out.println("        stroke-dasharray: 1,1;")
    out.println("        stroke: black;")
    out.println("        stroke-width: 0.1")
    out.println("      }")
    out.println("    ]]></style>")
    out.println("    <marker id='Triangle'")
    out.println("      viewBox='0 0 10 10' refX='0' refY='5' ")
    out.println("      markerUnits='strokeWidth'")
    out.println("      markerWidth='4' markerHeight='3'")
    out.println("      orient='auto'>")
    out.println("      <path d='M 0 0 L 10 5 L 0 10 z' />")
    out.println("    </marker>")
    out.println("    <filter id='dropShadow' x='-.1' y='-.1' width='200' height='120'>")
    out.println("       <feOffset in='SourceGraphic' dx='0' dy='0' result='orig' />")
    out.println("       <feGaussianBlur in='SourceAlpha' stdDeviation='.3' result='shadow' />")
    out.println("       <feOffset in='shadow' dx='0' dy='.1' result='movedShadow' />")
    out.println("       <feMerge>")
    out.println("           <feMergeNode in='movedShadow' />")
    out.println("           <feMergeNode in='orig' />")
    out.println("       </feMerge>")
    out.println("    </filter>")
    out.println("  </defs>")

    for p in f.players:
        drawPlayerSvg(f, p, out, ctx)  # Flow.java:563-566
    for m in f.messages:
        drawMessageSvg(f, m, out)  # Flow.java:568-571

    # epilogue, Flow.java:577-578
    out.println("</svg>")


def drawPlayerSvg(f, p, out, ctx):
    """Player.java:127-148"""
    # Flow.java pct is a string parsed at draw time; bad values throw.
    wid = (f.getColumnPitch() * parseJavaInt(f.getVMLBoxWidthPercentage())) / 100.0
    ht = 2.0
    # Java's ternary evaluates mynum++ only when stagger is on (section 3.6).
    # mynum is an int but % 2.0D promotes it, so the product is a double.
    if f.getStagger():
        stagger = (ht + 2.0) * (ctx.mynum % 2.0)
        ctx.mynum += 1
    else:
        stagger = 0.0
    ycenter = stagger - ht / 2.0
    # int*int/int is Java int division, widened to double: prints as "N.0"
    center = idiv(p.column * f.getVMLXSize(), f.getTotalWidth())

    out.print("<rect x='" + fmtD(center - wid / 2.0) + "' y='" +
              fmtD(ycenter - ht / 2.0) + "' width='" + fmtD(wid) + "' height='" +
              fmtD(ht) + "' rx='.6' ry='.6' filter='url(#dropShadow)'>")
    out.print("</rect>\n")

    for i in range(len(p.caption)):
        out.println(" <text text-anchor='middle' y='" + fmtD(ycenter + i + 0.4) +
                    "' x='" + fmtD(center) + "'>")
        out.println(f.xmlEscape(p.caption[i]))
        out.println(" </text> ")

    out.print("<line x1='" + fmtD(center) + "' y1='" +
              fmtD(ycenter - ht / 2.0 + ht) + "' x2='" + fmtD(center) +
              "' y2='" + fmtI(f.getVMLYSize()) + "'>")
    out.print("</line>\n")


def textout(out, textx, texty, i, text):
    """Message.java:226-231 (textout).  Java's parameter is named `line` and
    shadows the Message.line field, so texty + line means texty + i."""
    out.println(" <text y='" + fmtD(texty + i) + "' x='" + fmtD(textx) + "'>")
    out.println(text)
    out.println(" </text> ")


def drawMessageSvg(f, m, out):
    """Message.java:253-279"""
    fx = f.columnOf(m.from_)
    tx = f.columnOf(m.to)
    startx = fx if fx < tx else tx
    textx = 0.2 + startx
    texty = -0.2 + m.line
    arrowx = 0.4

    if isSelf(m):
        for i in range(len(m.caption)):
            textout(out, textx, texty, i, f.xmlEscape(m.caption[i]))
    elif isUndirected(m):
        for i in range(len(m.caption)):
            textout(out, textx, texty, i, f.xmlEscape(m.caption[i]))
        out.println(" <line class='dash' x1='" + fmtI(fx) + "' y1='" + fmtI(m.line) +
                    "' x2='" + fmtI(tx) + "' y2='" + fmtI(m.line) + "'/>")
    else:
        for i in range(len(m.caption)):
            textout(out, textx, texty, i, f.xmlEscape(m.caption[i]))
        out.println(" <line marker-end='url(#Triangle)' x1='" + fmtI(fx) + "' y1='" +
                    fmtI(m.line) + "' x2='" + fmtD(tx + (-arrowx if tx > fx else arrowx)) +
                    "' y2='" + fmtI(m.line) + "'/>")
