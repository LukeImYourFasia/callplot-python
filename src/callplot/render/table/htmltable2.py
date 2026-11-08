"""htmltable2 style: lib/htmltable2.xsl (section 3.13.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

The picture sits inside <small>; the table has a header row, captions are
<strong>, notes are <code>, comments sit bare in col 3 (no <tt>, so an
empty col 3 is <td/>).
"""

from .common import XMLDECL, linkCell, tdCell, strongCell, codeCell, commentBody

HEADER = ("<tr><th>Seq</th><th>Message and Details</th>"
          "<th>Notes</th></tr>")


def htmltable2(picture, rows):
    out = (XMLDECL + "<html><body><small><pre>" + picture +
           "</pre></small><table border=\"1\">" + HEADER)
    for r in rows:
        out += ("<tr>" + linkCell(r["num"]) +
                tdCell(strongCell(r["captions"]) + codeCell(r["notes"])) +
                tdCell(commentBody(r["comments"])) + "</tr>")
    return out + "</table></body></html>"
