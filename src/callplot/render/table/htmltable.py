"""htmltable style: lib/htmltable.xsl (section 3.13.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Col 2 shows captions THEN notes; lib/tmltable.xsl is a byte copy of this
file (section 1.3), so the tmltable style aliases to htmltable in index.py.
"""

from .common import XMLDECL, linkCell, tdCell, captionBody, noteBody, ttCell


def htmltable(picture, rows):
    out = XMLDECL + "<html><body><pre>" + picture + "</pre>"
    if len(rows) == 0:
        out += "<table border=\"1\"/>"
    else:
        out += "<table border=\"1\">"
        for r in rows:
            out += ("<tr>" + linkCell(r["num"]) +
                    tdCell(captionBody(r["captions"]) + noteBody(r["notes"])) +
                    ttCell(r["comments"]) + "</tr>")
        out += "</table>"
    return out + "</body></html>"
