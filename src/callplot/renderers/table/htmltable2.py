"""htmltable2 style: lib/htmltable2.xsl (section 3.13.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

The picture sits inside <small>; the table has a header row, captions are
<strong>, notes are <code>, comments sit bare in col 3 (no <tt>, so an
empty col 3 is <td/>).

The cells and the row shape live in the package __init__ (see the import
note in archtable.py).
"""

import callplot.renderers.table as _table

HEADER = "<tr><th>Seq</th><th>Message and Details</th><th>Notes</th></tr>"


def htmltable2(picture: str, rows: "list[_table.Row]") -> str:
    out = (
        _table.XMLDECL
        + "<html><body><small><pre>"
        + picture
        + "</pre></small>"
        + '<table border="1">'
        + HEADER
    )
    for r in rows:
        out += (
            "<tr>"
            + _table.link_cell(r["num"])
            + _table.td_cell(_table.strong_cell(r["captions"]) + _table.code_cell(r["notes"]))
            + _table.td_cell(_table.comment_body(r["comments"]))
            + "</tr>"
        )
    return out + "</table></body></html>"
