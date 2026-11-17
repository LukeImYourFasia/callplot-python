"""htmltable style: lib/htmltable.xsl (section 3.13.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Col 2 shows captions THEN notes; lib/tmltable.xsl is a byte copy of this
file (section 1.3), so the tmltable style aliases to htmltable in
options.parse_table_style.

The cells and the row shape live in the package __init__ (see the import
note in archtable.py).
"""

import callplot.renderers.table as _table


def htmltable(picture: str, rows: "list[_table.Row]") -> str:
    out = _table.XMLDECL + "<html><body><pre>" + picture + "</pre>"
    if len(rows) == 0:
        out += '<table border="1"/>'
    else:
        out += '<table border="1">'
        for r in rows:
            out += (
                "<tr>"
                + _table.link_cell(r["num"])
                + _table.td_cell(_table.caption_body(r["captions"]) + _table.note_body(r["notes"]))
                + _table.tt_cell(r["comments"])
                + "</tr>"
            )
        out += "</table>"
    return out + "</body></html>"
