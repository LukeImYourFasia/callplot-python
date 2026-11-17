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

import io

from callplot.constants import GRAFFLE_LINE_TXT_OFST, GRAFFLE_MULT, GRAFFLE_TOP_MARG, Mode
from callplot.context import RunContext
from callplot.flow import Flow
from callplot.jcompat import arr_at, fmt_d, fmt_i, idiv, parse_java_int
from callplot.model import Message, Player, is_note, is_self, is_undirected
from callplot.renderers.text import print_comment


def emit(out: io.StringIO, lines: list[str]) -> None:
    """A run of fixed println lines, copied from Java in order."""
    for s in lines:
        out.write((s) + "\n")


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


def graffle_on(f: Flow, mode: Mode, ctx: RunContext) -> str:
    """Flow.java:540-559 + 584-598 for the GRAFFLE bit.

    DESIGN-PYTHON.md section 3.7: the entry builds its own io.StringIO and
    returns the whole output as one str.
    """
    out = io.StringIO()
    f.start_message_numbers()

    if (mode & Mode.XML) != 0:
        out.write(("<plot>") + "\n")  # Flow.java:454-457
        out.write(("<picture>") + "\n")

    # prologue, Flow.java:540-546
    out.write(('<?xml version="1.0" encoding="UTF-8"?>') + "\n")
    out.write(
        (
            '<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" '
            '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
        )
        + "\n"
    )
    out.write(('<plist version="1.0">') + "\n")
    out.write(("<dict>") + "\n")
    out.write(("<key>GraphicsList</key>") + "\n")
    out.write(("<array>") + "\n")

    f.vml_y_size = f.get_total_height()  # Flow.java:548-549 (H, not 2H)
    f.vml_x_size = f.get_total_width()

    # messages first (Flow.java:551-554), then players (556-559)
    for m in f.messages:
        draw_message_graffle(f, m, out, ctx)
    for p in f.players:
        draw_player_graffle(f, p, out, ctx)

    # epilogue, Flow.java:584-598
    out.write(("</array>") + "\n")
    out.write(("</dict>") + "\n")
    out.write(("</plist>") + "\n")

    if (mode & Mode.XML) != 0:
        out.write(("</picture>") + "\n")
        for m in f.messages:
            print_comment(m, out)
        out.write(("</plot>") + "\n")
    return out.getvalue()


def draw_player_graffle(f: Flow, p: Player, out: io.StringIO, ctx: RunContext) -> None:
    """Player.java:182-352"""
    pct = parse_java_int(f.get_vml_box_width_percentage())  # Player.java:185
    wid = (GRAFFLE_MULT * f.get_column_pitch() * pct) / 100.0
    ht = 1.6 * len(p.caption) * GRAFFLE_MULT  # keep this operator order
    if f.get_stagger():
        stagger = (ht + 2.0) * (ctx.mynum % 2.0)
        ctx.mynum += 1
    else:
        stagger = 0.0
    ycenter = (stagger * GRAFFLE_MULT + GRAFFLE_TOP_MARG) / 2.0
    center = idiv(p.column * f.get_vml_x_size() * GRAFFLE_MULT, f.get_total_width())

    # text box, Player.java:194-200
    out.write(("<dict>") + "\n")
    out.write(("<key>Bounds</key>") + "\n")  # Player.java:197
    out.write(
        (
            "<string>{{"
            + fmt_d(center - wid / 2.0)
            + ", "
            + fmt_d(ycenter - ht / 2.0)
            + " }, {"
            + fmt_d(wid)
            + ", "
            + fmt_d(ht)
            + "}}</string>"
        )
        + "\n"
    )
    out.write(("<key>Class</key>") + "\n")
    out.write(("<string>ShapedGraphic</string>") + "\n")
    out.write(("<key>FitText</key>") + "\n")
    out.write(("<string>NO</string>") + "\n")
    out.write(("<key>ID</key>") + "\n")
    ctx.player_id += 1  # Player.java:207: int textId = ++id
    text_id = ctx.player_id
    out.write(("<integer>" + fmt_i(ctx.player_id) + "</integer>") + "\n")  # Player.java:208

    # Player.java:210-281
    out.write(("<key>Shape</key>") + "\n")
    out.write(("<string>Rectangle</string>") + "\n")
    emit(out, PLAYER_STYLE)

    # Player.java:285-291 (RTF text; caption[i] where i == caption.length - 1
    # throws IndexError when there is no caption line, DESIGN.md 3.8)
    emit(out, RTF_HEAD)  # Player.java:281-284
    out.write(r"\f0\fs24 \cf0 ")
    for i in range(len(p.caption) - 1):
        out.write((p.caption[i] + "\\") + "\n")
    out.write((arr_at(p.caption, len(p.caption) - 1) + "}</string>") + "\n")

    # Player.java:292-295
    out.write(("</dict>") + "\n")
    out.write(("</dict>") + "\n")

    # lifeline, Player.java:298-307
    out.write(("<dict>") + "\n")
    out.write(("<key>Class</key>") + "\n")
    out.write(("<string>LineGraphic</string>") + "\n")
    out.write(("<key>ID</key>") + "\n")
    ctx.player_id += 1  # Player.java:304: ++id
    out.write(("<integer>" + fmt_i(ctx.player_id) + "</integer>") + "\n")
    out.write(("<key>Points</key>") + "\n")
    out.write(("<array>") + "\n")
    out.write(
        ("<string>{" + fmt_d(center) + ", " + fmt_d(ycenter - ht / 2.0 + ht) + "}</string>") + "\n"
    )
    out.write(
        (
            "<string>{"
            + fmt_d(center)
            + ", "
            + fmt_i(GRAFFLE_TOP_MARG + f.get_vml_y_size() * GRAFFLE_MULT)
            + "}</string>"
        )
        + "\n"
    )
    out.write(("</array>") + "\n")

    # Player.java:314-346
    emit(out, PLAYER_LINE_TAIL)
    out.write(("<integer>" + fmt_i(text_id) + "</integer>") + "\n")  # Player.java:346
    out.write(("</dict>") + "\n")
    out.write(("</dict>") + "\n")  # Player.java:350


def draw_message_graffle(
    f: Flow,
    m: Message,
    out: io.StringIO,
    ctx: RunContext,
) -> None:
    """Message.java:282-678.  One message = an OmniGraffle group holding the
    label text box(es) and the arrow line.  Quirks kept on purpose: repeatLabel
    debug lines go to stderr (DESIGN.md 3.8 #7), caption[0] gains the "N. "
    numbering prefix and stays visible in the epilogue comments (3.8 #6),
    textId refers to the FIRST text box only, and numColumns can divide down to
    0 so a message draws its line with no label box at all."""
    line_pos = m.line * GRAFFLE_MULT + GRAFFLE_TOP_MARG
    fx = f.column_of(m.from_) * GRAFFLE_MULT
    tx = f.column_of(m.to) * GRAFFLE_MULT
    startx = fx if fx < tx else tx
    num_columns = 1
    if m.repeat_label:
        num_columns = idiv(abs(f.column_of(m.from_) - f.column_of(m.to)), f.get_column_pitch())
        ctx.err.write(("startx " + fmt_i(startx) + "  numColumns " + fmt_i(num_columns)) + "\n")

    # honor message numbering (Message.java:297-307); the caption mutation
    # (DESIGN.md 3.8 #6) prepends "N. " to line 0 and survives to the comments
    if not is_note(m) or f.get_do_note_numbering():
        num = f.next_message_number()
        if num != -1:
            m.my_number = num
            m.caption[0] = fmt_i(num) + ". " + arr_at(m.caption, 0)

    # group wrapper (Message.java:310-314)
    emit(out, GROUP_HEAD)

    text_id = ctx.message_id  # Message.java:317: int textId = id
    cur_x = startx  # Message.java:318 (int curX)
    textx = cur_x  # Message.java:320 (double textx = curX)
    texty = -1 * GRAFFLE_MULT * len(m.caption) + GRAFFLE_LINE_TXT_OFST + line_pos

    for _i in range(num_columns):
        textx = cur_x + 10  # Message.java:326 (offset for arrow)

        out.write(("<dict>") + "\n")
        out.write(("<key>Bounds</key>") + "\n")
        out.write(
            ("<string>{{" + fmt_d(textx) + ", " + fmt_d(texty) + " }, {0, 0}}</string>") + "\n"
        )  # Message.java:331-332; the 0s are ints
        out.write(("<key>Class</key>") + "\n")
        out.write(("<string>ShapedGraphic</string>") + "\n")
        out.write(("<key>FitText</key>") + "\n")
        out.write(("<string>YES</string>") + "\n")
        out.write(("<key>ID</key>") + "\n")
        out.write(("<integer>" + fmt_i(ctx.message_id) + "</integer>") + "\n")
        ctx.message_id += 1  # Message.java:341
        out.write(("<key>Shape</key>") + "\n")
        out.write(("<string>Rectangle</string>") + "\n")

        if is_note(m):
            emit(out, NOTE_STYLE)  # Message.java:349-426
        else:
            emit(out, TEXT_STYLE)  # Message.java:431-473

        # RTF label body (Message.java:478-499; empty caption throws, 3.8)
        out.write(("<key>Text</key>") + "\n")
        out.write(("<dict>") + "\n")
        out.write(("<key>Align</key>") + "\n")
        out.write(("<integer>0</integer>") + "\n")
        out.write(("<key>Text</key>") + "\n")
        emit(out, RTF_HEAD)  # Message.java:485-488
        out.write(r"\f0\fs24 \cf0 ")
        j = 0
        while j < len(m.caption) - 1:
            out.write((m.caption[j] + "\\") + "\n")
            j += 1
        out.write((arr_at(m.caption, j) + "}</string>") + "\n")
        out.write(("<key>VerticalPad</key>") + "\n")
        out.write(("<integer>1</integer>") + "\n")
        out.write(("</dict>") + "\n")
        out.write(("</dict>") + "\n")  # Message.java:501

        cur_x += f.get_column_pitch() * GRAFFLE_MULT  # Message.java:503

    # the arrow line (Message.java:511-542)
    out.write(("<dict>") + "\n")
    out.write(("<key>Class</key>") + "\n")
    out.write(("<string>LineGraphic</string>") + "\n")
    out.write(("<key>ID</key>") + "\n")
    out.write(("<integer>" + fmt_i(ctx.message_id) + "</integer>") + "\n")
    ctx.message_id += 1
    out.write(("<key>Points</key>") + "\n")
    out.write(("<array>") + "\n")
    if is_self(m) and not is_undirected(m):
        # self-directed: five-point hook; the doubles print with a ".0"
        out.write(("<string>{" + fmt_i(fx) + ", " + fmt_d(texty - 5) + "}</string>") + "\n")
        out.write(("<string>{" + fmt_i(fx + 20) + ", " + fmt_d(texty - 10) + "}</string>") + "\n")
        out.write(
            ("<string>{" + fmt_i(fx + 30) + ", " + fmt_d((texty + line_pos) / 2) + "}</string>")
            + "\n"
        )
        out.write(
            ("<string>{" + fmt_i(fx + 20) + ", " + fmt_i(line_pos + 10) + "}</string>") + "\n"
        )
        out.write(("<string>{" + fmt_i(fx) + ", " + fmt_i(line_pos + 5) + "}</string>") + "\n")
    elif is_note(m):
        out.write(("<string>{" + fmt_d(textx) + ", " + fmt_d(texty) + "}</string>") + "\n")
        out.write(("<string>{" + fmt_i(tx) + ", " + fmt_i(line_pos) + "}</string>") + "\n")
    else:
        out.write(("<string>{" + fmt_i(fx) + ", " + fmt_i(line_pos) + "}</string>") + "\n")
        out.write(("<string>{" + fmt_i(tx) + ", " + fmt_i(line_pos) + "}</string>") + "\n")
    out.write(("</array>") + "\n")

    # line style (Message.java:544-654)
    out.write(("<key>Style</key>") + "\n")
    out.write(("<dict>") + "\n")
    if is_note(m):
        emit(out, LINE_NOTE_SHADOW)  # Message.java:550-576
    out.write(("<key>stroke</key>") + "\n")
    out.write(("<dict>") + "\n")
    out.write(("<key>HeadArrow</key>") + "\n")
    if m.arrow_to and not m.arrow_from:
        out.write(("<string>FilledArrow</string>") + "\n")
        out.write(("<key>HeadScale</key>") + "\n")
        out.write(("<real>0.75</real>") + "\n")
    else:
        out.write(("<string>0</string>") + "\n")
        out.write(("<key>HeadScale</key>") + "\n")
        out.write(("<real>0.5</real>") + "\n")
    if not is_self(m) and is_undirected(m):
        # ".." long dash vs "--" short dash (Message.java:598/602)
        out.write(("<key>Pattern</key>") + "\n")
        out.write(("<integer>2</integer>" if m.repeat_label else "<integer>1</integer>") + "\n")
    if is_note(m):
        emit(out, LINE_NOTE_STYLE)  # Message.java:611-628
    out.write(("<key>TailArrow</key>") + "\n")
    if m.arrow_from and not m.arrow_to:
        out.write(("<string>FilledArrow</string>") + "\n")
        out.write(("<key>TailScale</key>") + "\n")
        out.write(("<real>0.75</real>") + "\n")
    else:
        out.write(("<string>0</string>") + "\n")
        out.write(("<key>TailScale</key>") + "\n")
        out.write(("<real>0.5</real>") + "\n")
    if is_self(m):
        out.write(("<key>LineType</key>") + "\n")
        out.write(("<integer>1</integer>") + "\n")  # Message.java:648-649
    out.write(("</dict>") + "\n")
    out.write(("</dict>") + "\n")

    # a note links its line to the text box (Message.java:657-668)
    if is_note(m):
        out.write(("<key>Tail</key>") + "\n")
        out.write(("<dict>") + "\n")
        out.write(("<key>ID</key>") + "\n")
        out.write(("<integer>" + fmt_i(text_id) + "</integer>") + "\n")
        out.write(("</dict>") + "\n")
    out.write(("</dict>") + "\n")  # Message.java:670 (close LineGraphic)

    # end group wrapper (Message.java:674-677)
    out.write(("</array>") + "\n")
    out.write(("<key>ID</key>") + "\n")
    out.write(("<integer>" + fmt_i(ctx.message_id) + "</integer>") + "\n")
    ctx.message_id += 1
    out.write(("</dict>") + "\n")
