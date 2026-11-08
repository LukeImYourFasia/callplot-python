"""OmniGraffle renderer (DESIGN.md section 3.4.5).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Flow.java:540-559 and 584-598 (drawPictureOn GRAFFLE branches; messages come
BEFORE players here),
Player.java:182-352 (drawPictureOn GRAFFLE branch),
Message.java:282-678 (drawPictureOn GRAFFLE branch).
Fixed plist text is copied verbatim from the Java literals, one array entry
per Java println (DESIGN.md section 5.3).  Numbers go through fmtI/fmtD.
DESIGN.md section 3.8 #6 (caption mutation) and #7 (repeatLabel debug to
stderr) are reproduced on purpose.
"""

from ..constants import MODES, GRAFFLE_MULT, GRAFFLE_TOP_MARG, GRAFFLE_LINE_TXT_OFST
from ..jcompat import arrAt, fmtD, fmtI, idiv, parseJavaInt
from ..model import isSelf, isUndirected, isNote
from ..out import Out
from .text import printComment


def emit(out, lines):
    """A run of fixed println lines, copied from Java in order."""
    for s in lines:
        out.println(s)


# Player.java:213-271 (the box style dict)
PLAYER_STYLE = [
    "<key>Style</key>",
    "<dict>",
    "<key>shadow</key>",
    "<dict>",
    "<key>Draws</key>",
    "<string>YES</string>",
    "</dict>",
    "<key>fill</key>",
    "<dict>",
    "<key>FillType</key>",
    "<integer>3</integer>",
    "<key>GradientCenter</key>",
    "<string>{0.266667, -0.190476}</string>",
    "<key>GradientColor</key>",
    "<dict>",
    "<key>a</key>",
    "<string>0.51</string>",
    "<key>b</key>",
    "<string>0.869565</string>",
    "<key>g</key>",
    "<string>0.869565</string>",
    "<key>r</key>",
    "<string>0.869565</string>",
    "</dict>",
    "</dict>",
    "<key>stroke</key>",
    "<dict>",
    "<key>CornerRadius</key>",
    "<real>5</real>",
    "<key>Color</key>",
    "<dict>",
    "<key>a</key>",
    "<string>0.14</string>",
    "<key>b</key>",
    "<string>0</string>",
    "<key>g</key>",
    "<string>0</string>",
    "<key>r</key>",
    "<string>0</string>",
    "</dict>",
    "</dict>",
    "</dict>",
    "<key>Text</key>",
    "<dict>",
    "<key>Align</key>",
    "<integer>0</integer>",
    "<key>Text</key>",
]

# The RTF header lines (Player.java:281-284, Message.java:485-488).
RTF_HEAD = [
    r"<string>{\rtf1\mac\ansicpg10000\cocoartf824\cocoasubrtf110",
    r"{\fonttbl\f0\fswiss\fcharset77 Helvetica;}",
    r"{\colortbl;\red255\green255\blue255;}",
    r"\pard\tx560\tx1120\tx1680\tx2240\tx2800\tx3360\tx3920\tx4480\tx5040\tx5600"
    r"\tx6160\tx6720\qc",
]

# Player.java:314-347 (lifeline style plus Tail link)
PLAYER_LINE_TAIL = [
    "<key>Style</key>",
    "<dict>",
    "<key>stroke</key>",
    "<dict>",
    "<key>Cap</key>",
    "<integer>0</integer>",
    "<key>HeadArrow</key>",
    "<string>0</string>",
    "<key>HeadScale</key>",
    "<real>0.5</real>",
    "<key>TailArrow</key>",
    "<string>0</string>",
    "<key>TailScale</key>",
    "<real>0.5</real>",
    "</dict>",
    "</dict>",
    "<key>Tail</key>",
    "<dict>",
    "<key>ID</key>",
]

# Message.java:310-314 (group wrapper head; its tail carries an id and so
# stays inline in drawMessageGraffle)
GROUP_HEAD = [
    "<dict>",
    "<key>Class</key>",
    "<string>Group</string>",
    "<key>Graphics</key>",
    "<array>",
]

# Message.java:349-426 (note text box style)
NOTE_STYLE = [
    "<key>Style</key>",
    "<dict>",
    "<key>fill</key>",
    "<dict>",
    "<key>Color</key>",
    "<dict>",
    "<key>a</key>",
    "<string>0.72</string>",
    "<key>b</key>",
    "<string>0.804798</string>",
    "<key>g</key>",
    "<string>1</string>",
    "<key>r</key>",
    "<string>1</string>",
    "</dict>",
    "</dict>",
    "<key>shadow</key>",
    "<dict>",
    "<key>Color</key>",
    "<dict>",
    "<key>a</key>",
    "<string>0.21</string>",
    "<key>b</key>",
    "<string>0</string>",
    "<key>g</key>",
    "<string>0</string>",
    "<key>r</key>",
    "<string>0</string>",
    "</dict>",
    "<key>Fuzziness</key>",
    "<real>9.0033035278320312</real>",
    "<key>ShadowVector</key>",
    "<string>{0, 2}</string>",
    "</dict>",
    "<key>stroke</key>",
    "<dict>",
    "<key>Cap</key>",
    "<integer>0</integer>",
    "<key>CornerRadius</key>",
    "<real>7</real>",
    "<key>Width</key>",
    "<string>2</string>",
    "<key>Color</key>",
    "<dict>",
    "<key>a</key>",
    "<string>0.8</string>",
    "<key>b</key>",
    "<string>0</string>",
    "<key>g</key>",
    "<string>0.95</string>",
    "<key>r</key>",
    "<string>0.95</string>",
    "</dict>",
    "</dict>",
    "</dict>",
]

# Message.java:431-473 (non-note text box style)
TEXT_STYLE = [
    "<key>Style</key>",
    "<dict>",
    "<key>fill</key>",
    "<dict>",
    "<key>Color</key>",
    "<dict>",
    "<key>a</key>",
    "<string>0.42</string>",
    "<key>b</key>",
    "<string>1</string>",
    "<key>g</key>",
    "<string>1</string>",
    "<key>r</key>",
    "<string>1</string>",
    "</dict>",
    "</dict>",
    "<key>shadow</key>",
    "<dict>",
    "<key>Draws</key>",
    "<string>NO</string>",
    "</dict>",
    "<key>stroke</key>",
    "<dict>",
    "<key>Cap</key>",
    "<integer>0</integer>",
    "<key>CornerRadius</key>",
    "<real>7</real>",
    "<key>Draws</key>",
    "<string>NO</string>",
    "</dict>",
    "</dict>",
]

# Message.java:550-576 (shadow block, only inside a note's line style)
LINE_NOTE_SHADOW = [
    "<key>shadow</key>",
    "<dict>",
    "<key>Color</key>",
    "<dict>",
    "<key>a</key>",
    "<string>0.26</string>",
    "<key>b</key>",
    "<string>0</string>",
    "<key>g</key>",
    "<string>0</string>",
    "<key>r</key>",
    "<string>0</string>",
    "</dict>",
    "<key>Fuzziness</key>",
    "<real>6</real>",
    "<key>ShadowVector</key>",
    "<string>{0, 1}</string>",
    "<key>Draws</key>",
    "<string>YES</string>",
    "</dict>",
]

# Message.java:611-628 (width+color, only inside a note's stroke dict)
LINE_NOTE_STYLE = [
    "<key>Width</key>",
    "<string>2</string>",
    "<key>Color</key>",
    "<dict>",
    "<key>a</key>",
    "<string>0.8</string>",
    "<key>b</key>",
    "<string>0</string>",
    "<key>g</key>",
    "<string>0.95</string>",
    "<key>r</key>",
    "<string>0.95</string>",
    "</dict>",
]


def graffleOn(f, out, mode, ctx):
    """Flow.java:540-559 + 584-598 for the GRAFFLE bit."""
    f.startMessageNumbers()

    if (mode & MODES["XML"]) != 0:
        out.println("<plot>")  # Flow.java:454-457
        out.println("<picture>")

    # prologue, Flow.java:540-546
    out.println('<?xml version="1.0" encoding="UTF-8"?>')
    out.println('<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" '
                '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">')
    out.println('<plist version="1.0">')
    out.println("<dict>")
    out.println("<key>GraphicsList</key>")
    out.println("<array>")

    f.vmlYSize = f.getTotalHeight()  # Flow.java:548-549 (H, not 2H)
    f.vmlXSize = f.getTotalWidth()

    # messages first (Flow.java:551-554), then players (556-559)
    for m in f.messages:
        drawMessageGraffle(f, m, out, ctx)
    for p in f.players:
        drawPlayerGraffle(f, p, out, ctx)

    # epilogue, Flow.java:584-598
    out.println("</array>")
    out.println("</dict>")
    out.println("</plist>")

    if (mode & MODES["XML"]) != 0:
        out.println("</picture>")
        for m in f.messages:
            printComment(m, out)
        out.println("</plot>")


def drawPlayerGraffle(f, p, out, ctx):
    """Player.java:182-352"""
    pct = parseJavaInt(f.getVMLBoxWidthPercentage())  # Player.java:185
    wid = (GRAFFLE_MULT * f.getColumnPitch() * pct) / 100.0
    ht = 1.6 * len(p.caption) * GRAFFLE_MULT  # keep this operator order
    if f.getStagger():
        stagger = (ht + 2.0) * (ctx.mynum % 2.0)
        ctx.mynum += 1
    else:
        stagger = 0.0
    ycenter = (stagger * GRAFFLE_MULT + GRAFFLE_TOP_MARG) / 2.0
    center = idiv(p.column * f.getVMLXSize() * GRAFFLE_MULT, f.getTotalWidth())

    # text box, Player.java:194-200
    out.println("<dict>")
    out.println("<key>Bounds</key>")  # Player.java:197
    out.println("<string>{{" + fmtD(center - wid / 2.0) + ", " +
                fmtD(ycenter - ht / 2.0) + " }, {" + fmtD(wid) + ", " +
                fmtD(ht) + "}}</string>")
    out.println("<key>Class</key>")
    out.println("<string>ShapedGraphic</string>")
    out.println("<key>FitText</key>")
    out.println("<string>NO</string>")
    out.println("<key>ID</key>")
    ctx.playerId += 1  # Player.java:207: int textId = ++id
    textId = ctx.playerId
    out.println("<integer>" + fmtI(ctx.playerId) + "</integer>")  # Player.java:208

    # Player.java:210-281
    out.println("<key>Shape</key>")
    out.println("<string>Rectangle</string>")
    emit(out, PLAYER_STYLE)

    # Player.java:285-291 (RTF text; caption[i] where i == caption.length - 1
    # throws IndexError when there is no caption line, DESIGN.md 3.8)
    emit(out, RTF_HEAD)  # Player.java:281-284
    out.print(r"\f0\fs24 \cf0 ")
    for i in range(len(p.caption) - 1):
        out.println(p.caption[i] + "\\")
    out.println(arrAt(p.caption, len(p.caption) - 1) + "}</string>")

    # Player.java:292-295
    out.println("</dict>")
    out.println("</dict>")

    # lifeline, Player.java:298-307
    out.println("<dict>")
    out.println("<key>Class</key>")
    out.println("<string>LineGraphic</string>")
    out.println("<key>ID</key>")
    ctx.playerId += 1  # Player.java:304: ++id
    out.println("<integer>" + fmtI(ctx.playerId) + "</integer>")
    out.println("<key>Points</key>")
    out.println("<array>")
    out.println("<string>{" + fmtD(center) + ", " +
                fmtD(ycenter - ht / 2.0 + ht) + "}</string>")
    out.println("<string>{" + fmtD(center) + ", " +
                fmtI(GRAFFLE_TOP_MARG + f.getVMLYSize() * GRAFFLE_MULT) + "}</string>")
    out.println("</array>")

    # Player.java:314-346
    emit(out, PLAYER_LINE_TAIL)
    out.println("<integer>" + fmtI(textId) + "</integer>")  # Player.java:346
    out.println("</dict>")
    out.println("</dict>")  # Player.java:350


def drawMessageGraffle(f, m, out, ctx):
    """Message.java:282-678.  One message = an OmniGraffle group holding the
    label text box(es) and the arrow line.  Quirks kept on purpose: repeatLabel
    debug lines go to stderr (DESIGN.md 3.8 #7), caption[0] gains the "N. "
    numbering prefix and stays visible in the epilogue comments (3.8 #6),
    textId refers to the FIRST text box only, and numColumns can divide down to
    0 so a message draws its line with no label box at all."""
    linePos = m.line * GRAFFLE_MULT + GRAFFLE_TOP_MARG
    fx = f.columnOf(m.from_) * GRAFFLE_MULT
    tx = f.columnOf(m.to) * GRAFFLE_MULT
    startx = fx if fx < tx else tx
    numColumns = 1
    if m.repeatLabel:
        numColumns = idiv(abs(f.columnOf(m.from_) - f.columnOf(m.to)),
                          f.getColumnPitch())
        ctx.err.println("startx " + fmtI(startx) + "  numColumns " + fmtI(numColumns))

    # honor message numbering (Message.java:297-307); the caption mutation
    # (DESIGN.md 3.8 #6) prepends "N. " to line 0 and survives to the comments
    if not isNote(m) or f.getDoNoteNumbering():
        num = f.nextMessageNumber()
        if num != -1:
            m.myNumber = num
            m.caption[0] = fmtI(num) + ". " + arrAt(m.caption, 0)

    # group wrapper (Message.java:310-314)
    emit(out, GROUP_HEAD)

    textId = ctx.messageId  # Message.java:317: int textId = id
    curX = startx  # Message.java:318 (int curX)
    textx = curX  # Message.java:320 (double textx = curX)
    texty = -1 * GRAFFLE_MULT * len(m.caption) + GRAFFLE_LINE_TXT_OFST + linePos

    for _i in range(numColumns):
        textx = curX + 10  # Message.java:326 (offset for arrow)

        out.println("<dict>")
        out.println("<key>Bounds</key>")
        out.println("<string>{{" + fmtD(textx) + ", " + fmtD(texty) +
                    " }, {0, 0}}</string>")  # Message.java:331-332; the 0s are ints
        out.println("<key>Class</key>")
        out.println("<string>ShapedGraphic</string>")
        out.println("<key>FitText</key>")
        out.println("<string>YES</string>")
        out.println("<key>ID</key>")
        out.println("<integer>" + fmtI(ctx.messageId) + "</integer>")
        ctx.messageId += 1  # Message.java:341
        out.println("<key>Shape</key>")
        out.println("<string>Rectangle</string>")

        if isNote(m):
            emit(out, NOTE_STYLE)  # Message.java:349-426
        else:
            emit(out, TEXT_STYLE)  # Message.java:431-473

        # RTF label body (Message.java:478-499; empty caption throws, 3.8)
        out.println("<key>Text</key>")
        out.println("<dict>")
        out.println("<key>Align</key>")
        out.println("<integer>0</integer>")
        out.println("<key>Text</key>")
        emit(out, RTF_HEAD)  # Message.java:485-488
        out.print(r"\f0\fs24 \cf0 ")
        j = 0
        while j < len(m.caption) - 1:
            out.println(m.caption[j] + "\\")
            j += 1
        out.println(arrAt(m.caption, j) + "}</string>")
        out.println("<key>VerticalPad</key>")
        out.println("<integer>1</integer>")
        out.println("</dict>")
        out.println("</dict>")  # Message.java:501

        curX += f.getColumnPitch() * GRAFFLE_MULT  # Message.java:503

    # the arrow line (Message.java:511-542)
    out.println("<dict>")
    out.println("<key>Class</key>")
    out.println("<string>LineGraphic</string>")
    out.println("<key>ID</key>")
    out.println("<integer>" + fmtI(ctx.messageId) + "</integer>")
    ctx.messageId += 1
    out.println("<key>Points</key>")
    out.println("<array>")
    if isSelf(m) and not isUndirected(m):
        # self-directed: five-point hook; the doubles print with a ".0"
        out.println("<string>{" + fmtI(fx) + ", " + fmtD(texty - 5) + "}</string>")
        out.println("<string>{" + fmtI(fx + 20) + ", " + fmtD(texty - 10) + "}</string>")
        out.println("<string>{" + fmtI(fx + 30) + ", " +
                    fmtD((texty + linePos) / 2) + "}</string>")
        out.println("<string>{" + fmtI(fx + 20) + ", " + fmtI(linePos + 10) + "}</string>")
        out.println("<string>{" + fmtI(fx) + ", " + fmtI(linePos + 5) + "}</string>")
    elif isNote(m):
        out.println("<string>{" + fmtD(textx) + ", " + fmtD(texty) + "}</string>")
        out.println("<string>{" + fmtI(tx) + ", " + fmtI(linePos) + "}</string>")
    else:
        out.println("<string>{" + fmtI(fx) + ", " + fmtI(linePos) + "}</string>")
        out.println("<string>{" + fmtI(tx) + ", " + fmtI(linePos) + "}</string>")
    out.println("</array>")

    # line style (Message.java:544-654)
    out.println("<key>Style</key>")
    out.println("<dict>")
    if isNote(m):
        emit(out, LINE_NOTE_SHADOW)  # Message.java:550-576
    out.println("<key>stroke</key>")
    out.println("<dict>")
    out.println("<key>HeadArrow</key>")
    if m.arrowTo and not m.arrowFrom:
        out.println("<string>FilledArrow</string>")
        out.println("<key>HeadScale</key>")
        out.println("<real>0.75</real>")
    else:
        out.println("<string>0</string>")
        out.println("<key>HeadScale</key>")
        out.println("<real>0.5</real>")
    if not isSelf(m) and isUndirected(m):
        # ".." long dash vs "--" short dash (Message.java:598/602)
        out.println("<key>Pattern</key>")
        out.println("<integer>2</integer>" if m.repeatLabel else "<integer>1</integer>")
    if isNote(m):
        emit(out, LINE_NOTE_STYLE)  # Message.java:611-628
    out.println("<key>TailArrow</key>")
    if m.arrowFrom and not m.arrowTo:
        out.println("<string>FilledArrow</string>")
        out.println("<key>TailScale</key>")
        out.println("<real>0.75</real>")
    else:
        out.println("<string>0</string>")
        out.println("<key>TailScale</key>")
        out.println("<real>0.5</real>")
    if isSelf(m):
        out.println("<key>LineType</key>")
        out.println("<integer>1</integer>")  # Message.java:648-649
    out.println("</dict>")
    out.println("</dict>")

    # a note links its line to the text box (Message.java:657-668)
    if isNote(m):
        out.println("<key>Tail</key>")
        out.println("<dict>")
        out.println("<key>ID</key>")
        out.println("<integer>" + fmtI(textId) + "</integer>")
        out.println("</dict>")
    out.println("</dict>")  # Message.java:670 (close LineGraphic)

    # end group wrapper (Message.java:674-677)
    out.println("</array>")
    out.println("<key>ID</key>")
    out.println("<integer>" + fmtI(ctx.messageId) + "</integer>")
    ctx.messageId += 1
    out.println("</dict>")
