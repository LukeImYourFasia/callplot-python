"""htmltable3 style: lib/htmltable3.xsl (section 3.13.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Same as htmltable2 but the picture is inside TWO <small> wrappers: the
extra pair is a quirk of the 2008 toolset, kept on purpose.
"""

from .common import XMLDECL, linkCell, tdCell, strongCell, codeCell, commentBody

HEADER = ("<tr><th>Seq</th><th>Message and Details</th>"
          "<th>Notes</th></tr>")


def htmltable3(picture, rows):
    out = (XMLDECL + "<html><body><small><small><pre>" + picture +
           "</pre></small></small><table border=\"1\">" + HEADER)
    for r in rows:
        out += ("<tr>" + linkCell(r["num"]) +
                tdCell(strongCell(r["captions"]) + codeCell(r["notes"])) +
                tdCell(commentBody(r["comments"])) + "</tr>")
    return out + "</table></body></html>"
