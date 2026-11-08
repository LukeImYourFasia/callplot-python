"""nolinks style: lib/nolinks.xsl (section 3.13.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Like archtable but col 1 carries just the number (no <a> links); the
picture keeps its links, copied verbatim.
"""

from .common import XMLDECL, plainCell, tdCell, captionBody, noteBody, ttCell


def nolinks(picture, rows):
    out = XMLDECL + "<html><body><pre>" + picture + "</pre>"
    if len(rows) == 0:
        out += "<table border=\"true\"/>"
    else:
        out += "<table border=\"true\">"
        for r in rows:
            out += ("<tr>" + plainCell(r["num"]) +
                    tdCell(captionBody(r["captions"]) + noteBody(r["notes"])) +
                    ttCell(r["comments"]) + "</tr>")
        out += "</table>"
    return out + "</body></html>"
