"""nolinks style: lib/nolinks.xsl (section 3.13.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Like archtable but col 1 carries just the number (no <a> links); the
picture keeps its links, copied verbatim.

The cells and the row shape live in the package __init__ (see the import
note in archtable.py).
"""

import callplot.renderers.table as _table


def nolinks(picture: str, rows: "list[_table.Row]") -> str:
    out = _table.XMLDECL + "<html><body><pre>" + picture + "</pre>"
    if len(rows) == 0:
        out += '<table border="true"/>'
    else:
        out += '<table border="true">'
        for r in rows:
            out += (
                "<tr>"
                + _table.plain_cell(r["num"])
                + _table.td_cell(_table.caption_body(r["captions"]) + _table.note_body(r["notes"]))
                + _table.tt_cell(r["comments"])
                + "</tr>"
            )
        out += "</table>"
    return out + "</body></html>"
