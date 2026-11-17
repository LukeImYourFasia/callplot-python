"""PIC (XPICTURE) renderer (DESIGN.md section 3.4.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Flow.java:449-461 and 575-576 (prologue/epilogue of drawPictureOn),
Player.java:124-126 (drawPictureOn PIC branch),
Message.java:233-252 (drawPictureOn PIC branch).
PIC never calls columnOf (DESIGN.md section 3.8 #8), so unknown aliases are
fine and never raise IllegalArgumentError here.
"""

import io

from callplot.constants import Mode
from callplot.flow import Flow
from callplot.jcompat import fmt_d
from callplot.model import Message, Player, is_self, is_undirected


def pic_on(f: Flow, mode: Mode) -> str:
    """Flow.java:449-461 + 562-576 for the PIC bit: the shared drawPictureOn
    skeleton with only the PIC branches filled in.

    DESIGN-PYTHON.md section 3.7: the entry builds its own io.StringIO and
    returns the whole output as one str.
    """
    out = io.StringIO()
    f.start_message_numbers()

    if (mode & Mode.XML) != 0:
        out.write(("<plot>") + "\n")  # Flow.java:454-456
        out.write(("<picture>") + "\n")

    # prologue, Flow.java:460-461
    out.write(".PS " + f.pic_x_size + " " + f.pic_y_size + "\n")

    # PIC never sets vml_x_size/vml_y_size and never reads them (Java leaves
    # them 0 here); nothing to do.

    for p in f.players:
        draw_player_pic(f, p, out)  # Flow.java:563-566
    for m in f.messages:
        draw_message_pic(f, m, out)  # Flow.java:568-571

    # epilogue, Flow.java:575-576: println(".PE\n") prints .PE plus a blank line
    out.write((".PE\n") + "\n")
    return out.getvalue()


def draw_player_pic(f: Flow, p: Player, out: io.StringIO) -> None:
    """Player.java:124-126"""
    out.write(
        "P"
        + p.name
        + ': { box "'
        + p.caption_string
        + '"; down; L'
        + p.name
        + ": line "
        + fmt_d(f.get_total_height() / 6.0 + 0.25)
        + "i from last box.s }; right; move 2i\n"
    )


def draw_message_pic(f: Flow, m: Message, out: io.StringIO) -> None:
    """Message.java:235-252"""
    off = fmt_d(-1.0 * m.line / 6.0)  # Java: -1.0D * line / 6.0D
    if is_self(m):
        out.write(
            '{ line invis "'
            + m.caption_string
            + '" "" from L'
            + m.from_
            + ".start + (0,"
            + off
            + ") to L"
            + m.to
            + ".start + (0.1,"
            + off
            + ");  }\n"
        )
    elif is_undirected(m):
        out.write(
            '{ line dotted "'
            + m.caption_string
            + '" "" from L'
            + m.from_
            + ".start + (0,"
            + off
            + ") to L"
            + m.to
            + ".start + (0,"
            + off
            + ");  }\n"
        )
    else:
        out.write(
            '{ arrow "'
            + m.caption_string
            + '" "" from L'
            + m.from_
            + ".start + (0,"
            + off
            + ") to L"
            + m.to
            + ".start + (0,"
            + off
            + ");  }\n"
        )
