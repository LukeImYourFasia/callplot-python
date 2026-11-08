"""archtable style: plottable's default, lib/archtable.xsl (section 3.13.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Col 2 shows NOTES ONLY (no caption), col 3 the <tt> comments.
"""

from .common import XMLDECL, linkCell, tdCell, noteBody, ttCell


def archtable(picture, rows):
    out = XMLDECL + "<html><body><pre>" + picture + "</pre>"
    if len(rows) == 0:
        out += "<table border=\"true\"/>"  # whole table empty (rule 6)
    else:
        out += "<table border=\"true\">"
        for r in rows:
            out += ("<tr>" + linkCell(r["num"]) +
                    tdCell(noteBody(r["notes"])) + ttCell(r["comments"]) +
                    "</tr>")
        out += "</table>"
    return out + "</body></html>"
