"""VML renderer, also used for -vxml (DESIGN.md section 3.4.4).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Flow.java:514-539 and 579-583 (drawPictureOn VML branches),
Player.java:149-179 (drawPictureOn VML branch),
Message.java:680-738 (drawPictureOn VML branch).
Spacing in the fixed strings is copied from the Java literals; DESIGN.md
section 3.8 #1 says -vxml opens <plot>/<picture> and never closes them,
which is simply the absence of the closing tags in Java's VML epilogue
branch.
"""

import io

from callplot.constants import VML_TEXT_XOFF, VML_TEXT_YOFF, Mode
from callplot.context import RunContext
from callplot.flow import Flow
from callplot.jcompat import arr_at, fmt_d, fmt_i, idiv, parse_java_int
from callplot.model import Message, Player, is_self, is_undirected


def vml_on(f: Flow, mode: Mode, ctx: RunContext) -> str:
    """Flow.java:514-539 + 579-583 for the VML bit.

    DESIGN-PYTHON.md section 3.7: the entry builds its own io.StringIO and
    returns the whole output as one str.
    """
    out = io.StringIO()
    f.start_message_numbers()

    if (mode & Mode.XML) != 0:
        out.write(("<plot>") + "\n")  # Flow.java:454-457 (-vxml)
        out.write(("<picture>") + "\n")

    # prologue, Flow.java:514-538
    out.write(("<html xmlns:v='urn:schemas-microsoft-com:vml'") + "\n")
    out.write(("xmlns='http://www.w3.org/TR/REC-html40'>") + "\n")
    out.write(("") + "\n")
    out.write(("<head>") + "\n")
    out.write(("") + "\n")
    out.write(("<!--[if !mso]>") + "\n")
    out.write(("<style>") + "\n")
    out.write(("v\\:* {behavior:url(#default#VML);}") + "\n")
    out.write((".shape {behavior:url(#default#VML);}") + "\n")
    out.write(("</style>") + "\n")
    out.write(("<![endif]-->") + "\n")
    out.write(("") + "\n")
    out.write(("</head>") + "\n")
    out.write(("") + "\n")
    out.write(("<body>") + "\n")
    f.vml_y_size = f.get_total_height() * 2  # Flow.java:530-531
    f.vml_x_size = f.get_total_width()
    vml_y_pt = idiv(432 * f.vml_y_size, 100)  # Flow.java:532-533
    vml_x_pt = idiv(432 * f.vml_x_size, 100)
    out.write(("<!-- totalHeight =" + fmt_i(f.get_total_height()) + "-->") + "\n")
    out.write(("<!-- totalWidth =" + fmt_i(f.get_total_width()) + "-->") + "\n")
    out.write(
        (
            "<v:group style='position:relative;left:1pt;top:2pt;width:"
            + fmt_i(vml_x_pt)
            + "pt;height:"
            + fmt_i(vml_y_pt)
            + "pt;' coordsize='"
            + fmt_i(f.vml_x_size)
            + ","
            + fmt_i(f.vml_y_size)
            + "' >"
        )
        + "\n"
    )
    out.write(("") + "\n")

    for p in f.players:
        draw_player_vml(f, p, out, ctx)  # Flow.java:563-566
    for m in f.messages:
        draw_message_vml(f, m, out)  # Flow.java:568-571

    # epilogue, Flow.java:579-583: three trailing spaces on the last line
    out.write(("") + "\n")
    out.write(("</v:group>") + "\n")
    out.write(("</body>") + "\n")
    out.write(("</html>   ") + "\n")
    return out.getvalue()


def draw_player_vml(f: Flow, p: Player, out: io.StringIO, ctx: RunContext) -> None:
    """Player.java:149-179"""
    # all int (DESIGN.md 3.5 typing rule): wid prints without a ".0"
    wid = idiv(f.get_column_pitch() * f.get_vml_x_size(), f.get_total_width())
    wid = wid * parse_java_int(f.get_vml_box_width_percentage())  # Flow.java:153
    wid = idiv(wid, 100)  # Flow.java:154
    ht = 4.0
    if f.get_stagger():
        stagger = (ht + 2.0) * (ctx.mynum % 2.0)
        ctx.mynum += 1
    else:
        stagger = 0.0
    ycenter = stagger - ht / 2.0
    center = idiv(p.column * f.get_vml_x_size(), f.get_total_width())

    out.write(
        "<v:rect "
        + f.get_vml_box_style()
        + " style='position:absolute;left:"
        + fmt_d(center - wid / 2.0)
        + ";top:"
        + fmt_d(ycenter - ht / 2.0)
        + ";width:"
        + fmt_i(wid)
        + ";height:"
        + fmt_d(ht)
        + "'>"
    )
    out.write(("  <v:stroke   " + f.get_vml_style() + " />") + "\n")
    out.write("</v:rect>")

    out.write(
        (
            " <v:shape fillcolor='black' strokeweight='0pt' coordorigin='0 0' "
            "coordsize='100 100' style='position:absolute;top:"
            + fmt_d(0.2 + ycenter)
            + ";left:"
            + fmt_d(center - wid / 2.0 + 0.3)
            + ";width:"
            + fmt_i(wid)
            + ";height:"
            + fmt_d(ht)
            + "' path = 'm 0,0 l 100,0  e'>"
        )
        + "\n"
    )
    out.write((" <v:path textpathok='True'/> ") + "\n")
    out.write(
        (
            " <v:textpath on='True' string=\""
            + f.xml_escape(arr_at(p.caption, 0))
            + '" '
            + f.get_vml_box_text_style()
            + "/> "
        )
        + "\n"
    )
    out.write((" </v:shape> ") + "\n")

    out.write(
        "<v:line  from='"
        + fmt_d(center)
        + ","
        + fmt_d(ycenter - ht / 2.0 + ht)
        + "' to='"
        + fmt_d(center)
        + ","
        + fmt_i(f.get_vml_y_size())
        + "'>"
    )
    out.write(("  <v:stroke " + f.get_vml_style() + " />") + "\n")
    out.write("</v:line>")


def draw_message_vml(f: Flow, m: Message, out: io.StringIO) -> None:
    """Message.java:680-738"""
    v_y = idiv(m.line * f.get_vml_y_size(), f.get_total_height())
    from_x = idiv(f.column_of(m.from_) * f.get_vml_x_size(), f.get_total_width())
    to_x = idiv(f.column_of(m.to) * f.get_vml_x_size(), f.get_total_width())
    start_x = VML_TEXT_XOFF + (from_x if from_x < to_x else to_x)
    text_off = VML_TEXT_YOFF

    xml_caption = f.xml_escape(arr_at(m.caption, 0))

    # honor message numbering (Message.java:690-696)
    if not is_self(m) or f.get_do_note_numbering():
        num = f.next_message_number()
        if num != -1:
            m.my_number = num
            xml_caption = "(" + fmt_i(num) + ") " + xml_caption

    # first line (Message.java:700-707)
    out.write(
        (
            " <v:shape fillcolor='black' strokeweight='0pt' coordorigin='0 0' "
            "coordsize='100 100' style='position:absolute;top:"
            + fmt_i(v_y - text_off)
            + ";left:"
            + fmt_i(start_x)
            + ";width:1;height:1' path = 'm 0,0 l 100,0  e'>"
        )
        + "\n"
    )
    out.write((" <v:path textpathok='True'/> ") + "\n")
    out.write(
        (" <v:textpath on='True' string=\"" + xml_caption + '" ' + f.get_vml_text_style() + " /> ")
        + "\n"
    )
    out.write((" </v:shape> ") + "\n")

    # other lines (Message.java:710-720): v_y moves down per extra caption line
    for caption_index in range(1, len(m.caption)):
        v_y += idiv(f.get_vml_y_size(), f.get_total_height())
        out.write(
            (
                " <v:shape fillcolor='black' strokeweight='0pt' coordorigin='0 0' "
                "coordsize='100 100' style='position:absolute;top:"
                + fmt_i(v_y - text_off)
                + ";left:"
                + fmt_i(start_x)
                + ";width:1;height:1' path = 'm 0,0 l 100,0  e'>"
            )
            + "\n"
        )
        out.write((" <v:path textpathok='True'/> ") + "\n")
        out.write(
            (
                " <v:textpath on='True' string=\""
                + f.xml_escape(arr_at(m.caption, caption_index))
                + '" '
                + f.get_vml_text_style()
                + " /> "
            )
            + "\n"
        )
        out.write((" </v:shape> ") + "\n")

    # arrows, at the FINAL v_y (DESIGN.md section 3.8 #5)
    if is_self(m):
        pass  # Message.java:723-724: nothing to do
    elif is_undirected(m):
        out.write(
            (
                " <v:line from='"
                + fmt_i(from_x)
                + ","
                + fmt_i(v_y)
                + "' to='"
                + fmt_i(to_x)
                + ","
                + fmt_i(v_y)
                + "'>"
            )
            + "\n"
        )
        out.write(
            ("  <v:stroke " + f.get_vml_dotted_style() + "  " + f.get_vml_style() + " />") + "\n"
        )
        out.write((" </v:line>") + "\n")
    else:
        out.write(
            (
                " <v:line from='"
                + fmt_i(from_x)
                + ","
                + fmt_i(v_y)
                + "' to='"
                + fmt_i(to_x)
                + ","
                + fmt_i(v_y)
                + "'>"
            )
            + "\n"
        )
        out.write(
            ("  <v:stroke   " + f.get_vml_style() + " " + f.get_vml_arrow_style() + " />") + "\n"
        )
        out.write((" </v:line>") + "\n")
