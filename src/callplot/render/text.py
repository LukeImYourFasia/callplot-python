"""TEXT and XML renderers (one plotOn, selected by mode bits).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Flow.java:315-419 (plotOn), Player.java:99-119 (drawSelf),
Message.java:126-182 (drawSelf), Message.java:192-224 (printComment).
One buffer line at a time, exactly like the Java char[].
"""

from ..constants import MODES
from ..jcompat import (CharBuf, arrAt, fmtI, idiv, parseJavaInt,
                       NumberFormatError)


def plotOn(f, out, mode):
    """Flow.java:315-419 (prologue/epilogue; the line loop is below)."""
    if (mode & MODES["XML"]) != 0:
        out.println("<plot>")  # Flow.java:318-319
        out.println("<picture>")

    lines = drawTextLines(f, mode, None)  # numbering side effect: myNumber
    for l in lines:
        out.println(l)

    if (mode & MODES["XML"]) != 0:
        out.println("</picture>")  # Flow.java:401-403
        for m in f.messages:
            printComment(m, out)
        out.println("</plot>")


def drawTextLines(f, mode, forceLinks):
    """Flow.java:320-399: the picture-content line loop.  Returns the lines
    instead of writing them so the table pipeline (section 3.13.1) can reuse
    them.  forceLinks: True forces links on (tables), False forces off, None
    keeps Flow.links.  The loop runs startMessageNumbers first, exactly like
    Java, so drawMessage's myNumber assignment is visible to callers."""
    f.startMessageNumbers()
    links = f.links if forceLinks is None else forceLinks

    width = f.getTotalWidth()
    buf = CharBuf(width)
    lines = []

    for line in range(0, f.getTotalHeight() + 1):
        for i in range(width):
            buf.set(i, " ")

        for p in f.players:
            drawPlayer(f, p, line, buf)
        for m in f.messages:
            drawMessage(f, m, line, buf)

        if f.shouldPrint(buf):
            lastChar = width - 1
            while buf.get(lastChar) == " " and lastChar > 0:
                lastChar -= 1

            if (mode & MODES["XML"]) != 0:
                lines.append(writeLineXml(f, buf, lastChar, links))
            else:
                lines.append(buf.sliceString(0, lastChar + 1))
    return lines


def writeLineXml(f, buf, lastChar, links):
    """Flow.java:359-395: XML-escape and turn (n) into links.  Reproduces
    the switch fallthrough: '(' falls to default unless the try block breaks."""
    s = []
    i = 0
    while i <= lastChar:
        ch = buf.get(i)
        wrote = False
        if ch == "<":
            s.append("&lt;")  # Flow.java:365
            wrote = True
        elif ch == ">":
            s.append("&gt;")  # Flow.java:369
            wrote = True
        elif ch == "(" and links:
            numStart = i + 1
            while i <= lastChar and buf.get(i) != ")":
                i += 1
            linked = False
            if buf.get(i) == ")":
                # buf.get may raise IndexError: Java's lineBuffer[i] would
                # be an array-index-out-of-bounds error.
                try:
                    num = parseJavaInt(buf.sliceString(numStart, i - numStart))
                    s.append("(<a href='#t" + fmtI(num) + "'>" + fmtI(num) +
                             "</a>)<a name='m" + fmtI(num) + "'/>")
                    linked = True  # break out of the switch (Flow.java:383)
                except NumberFormatError:
                    pass  # Flow.java:384-385: swallow, fall through to i--
            if linked:
                i += 1  # JS: continue, then the loop's i++ is skipped: land
                        # on the char after ')'
                continue
            i = numStart - 1
        if not wrote:
            s.append(buf.get(i))  # default: Flow.java:392
        i += 1
    return "".join(s)


def drawPlayer(f, p, line, buf):
    """Player.java:99-119"""
    lineInCaption = f.labelLine(line)
    if lineInCaption >= 0:
        # blank = arrayOf(" ") (Player.java:51): one space
        image = p.caption[lineInCaption] if lineInCaption < len(p.caption) else " "
    else:
        image = "|"  # glyph (Player.java:50)
    if len(image) == 1:
        buf.set(p.column, image[0])
    else:
        bias = idiv(len(image), 2)
        buf.copyIn(image, p.column - bias, len(image))


def drawMessage(f, m, line, buf):
    """Message.java:126-182"""
    fcol = f.columnOf(m.from_)
    tcol = f.columnOf(m.to)
    locol = fcol if fcol < tcol else tcol
    hicol = tcol if fcol < tcol else fcol

    offset = m.line - line

    if offset == 0 and locol != hicol:
        for j in range(locol + 1, hicol):
            buf.set(j, m.filler)
        if (m.arrowFrom and locol == fcol) or (m.arrowTo and locol == tcol):
            buf.set(locol + 1, "<")
        if (m.arrowFrom and hicol == fcol) or (m.arrowTo and hicol == tcol):
            buf.set(hicol - 1, ">")
    elif offset == len(m.caption) and (locol != hicol or f.getDoNoteNumbering()):
        num = f.nextMessageNumber()
        if num != -1:
            m.myNumber = num
            finalCaption = "(" + fmtI(num) + ") " + arrAt(m.caption, 0)
        else:
            finalCaption = arrAt(m.caption, 0)
        copyCaption(buf, locol, finalCaption)
    elif 0 < offset <= len(m.caption):
        idx = len(m.caption) - offset
        copyCaption(buf, locol, arrAt(m.caption, idx))


def copyCaption(buf, locol, text):
    """Message.java:162-169 and 173-180: clamp the copy, mark truncation with '*'"""
    width = len(buf.a)
    copySize = len(text)
    if locol + 1 + len(text) > width:
        copySize = width - (locol + 1)
    buf.copyIn(text, locol + 1, copySize)
    if copySize != len(text):
        buf.set(width - 1, "*")


def printComment(m, out):
    """Message.java:192-224 (XML epilogue; the Graffle epilogue shares it)"""
    if m.myNumber != 0:
        out.println("<message>")
        out.println("<number>" + fmtI(m.myNumber) + "</number>")
        out.println("<captions>")
        for i in range(len(m.caption)):
            out.println("<caption>" + m.caption[i] + "</caption>")
        out.println("</captions>")
        out.println("<notes>")
        for c in m.notes:
            out.println("<note>")
            out.println(c)
            out.println("</note>")
        out.println("</notes>")
        out.println("<comments>")
        for c in m.comments:
            out.println("<comment>")
            out.println(c)
            out.println("</comment>")
        out.println("</comments>")
        out.println("</message>")
