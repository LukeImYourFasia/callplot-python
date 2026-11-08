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

from ..constants import MODES
from ..jcompat import fmtD
from ..model import isSelf, isUndirected


def picOn(f, out, mode):
    """Flow.java:449-461 + 562-576 for the PIC bit: the shared drawPictureOn
    skeleton with only the PIC branches filled in."""
    f.startMessageNumbers()

    if (mode & MODES["XML"]) != 0:
        out.println("<plot>")  # Flow.java:454-456
        out.println("<picture>")

    # prologue, Flow.java:460-461
    out.print(".PS " + f.picXSize + " " + f.picYSize + "\n")

    # PIC never sets vml_x_size/vml_y_size and never reads them (Java leaves
    # them 0 here); nothing to do.

    for p in f.players:
        drawPlayerPic(f, p, out)  # Flow.java:563-566
    for m in f.messages:
        drawMessagePic(f, m, out)  # Flow.java:568-571

    # epilogue, Flow.java:575-576: println(".PE\n") prints .PE plus a blank line
    out.println(".PE\n")


def drawPlayerPic(f, p, out):
    """Player.java:124-126"""
    out.print(
        "P" + p.name + ": { box \"" + p.captionString +
        "\"; down; L" + p.name + ": line " +
        fmtD(f.getTotalHeight() / 6.0 + 0.25) +
        "i from last box.s }; right; move 2i\n"
    )


def drawMessagePic(f, m, out):
    """Message.java:235-252"""
    off = fmtD(-1.0 * m.line / 6.0)  # Java: -1.0D * line / 6.0D
    if isSelf(m):
        out.print(
            "{ line invis \"" + m.captionString + "\" \"\" from L" + m.from_ +
            ".start + (0," + off + ") to L" + m.to + ".start + (0.1," + off +
            ");  }\n"
        )
    elif isUndirected(m):
        out.print(
            "{ line dotted \"" + m.captionString + "\" \"\" from L" + m.from_ +
            ".start + (0," + off + ") to L" + m.to + ".start + (0," + off +
            ");  }\n"
        )
    else:
        out.print(
            "{ arrow \"" + m.captionString + "\" \"\" from L" + m.from_ +
            ".start + (0," + off + ") to L" + m.to + ".start + (0," + off +
            ");  }\n"
        )
