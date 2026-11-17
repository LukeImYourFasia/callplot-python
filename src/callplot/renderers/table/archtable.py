"""archtable style: plottable's default, lib/archtable.xsl (section 3.13.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Col 2 shows NOTES ONLY (no caption), col 3 the <tt> comments.

The cells and the row shape live in the package __init__ (DESIGN-PYTHON.md
section 2.2).  This module imports the package as a module object because
the __init__ imports this module: at import time the package is only
partially initialized, so names cannot be imported; the cells are reached
by attribute (at call time, when the package is complete), and the row
type only appears in a string annotation (never evaluated at runtime).
"""

import callplot.renderers.table as _table


def archtable(picture: str, rows: "list[_table.Row]") -> str:
    out = _table.XMLDECL + "<html><body><pre>" + picture + "</pre>"
    if len(rows) == 0:
        out += '<table border="true"/>'  # whole table empty (rule 6)
    else:
        out += '<table border="true">'
        for r in rows:
            out += (
                "<tr>"
                + _table.link_cell(r["num"])
                + _table.td_cell(_table.note_body(r["notes"]))
                + _table.tt_cell(r["comments"])
                + "</tr>"
            )
        out += "</table>"
    return out + "</body></html>"
