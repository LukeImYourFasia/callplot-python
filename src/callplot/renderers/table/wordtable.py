"""wordtable style: lib/wordtable.xsl, a Word 9 export document (section 3.13.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

All fixed text is copied from the goldens byte for byte (attribute order
included); the double space after ".5pt;  " in header cell 1 is in the
golden. The table is never empty: it always carries the header row, and
every cell holds a <p class="MsoNormal">.

The cells and the row shape live in the package __init__ (see the import
note in archtable.py); the document head is built inside the function
because at import time the package is only partially initialized.
"""

import callplot.renderers.table as _table

TABLE_OPEN = (
    '<table style="border-collapse:collapse;border:none;'
    "mso-border-alt:solid windowtext .5pt;"
    'mso-padding-alt:0in 5.4pt 0in 5.4pt" '
    'cellpadding="0" cellspacing="0" border="1">'
)

HEADER_ROW = (
    "<tr>"
    '<td style="width:48.3pt;border:solid windowtext .5pt;  '
    'padding:0in 5.4pt 0in 5.4pt" valign="top" width="64">'
    '<p class="MsoNormal"><b>Number<o:p/></b></p></td>'
    '<td style="width:171.0pt;border:solid windowtext .5pt;'
    "border-left:none;mso-border-left-alt:solid windowtext .5pt;"
    'padding:0in 5.4pt 0in 5.4pt" valign="top" width="228">'
    '<p class="MsoNormal"><b>Annotation<o:p/></b></p></td>'
    '<td style="width:3.2in;border:solid windowtext .5pt;'
    "border-left:none;mso-border-left-alt:solid windowtext .5pt;"
    'padding:0in 5.4pt 0in 5.4pt" valign="top" width="307">'
    '<p class="MsoNormal"><b>Packet<o:p/></b></p></td>'
    "</tr>"
)

BODY_TD1_OPEN = (
    '<td style="width:48.3pt;border:solid windowtext .5pt;'
    "border-top:none;mso-border-top-alt:solid windowtext .5pt;"
    'padding:0in 5.4pt 0in 5.4pt" valign="top" width="64">'
)

BODY_TD2_OPEN = (
    '<td style="width:171.0pt;border-top:none;border-left:none;'
    "border-bottom:solid windowtext .5pt;border-right:solid "
    "windowtext .5pt;mso-border-top-alt:solid windowtext .5pt;"
    "mso-border-left-alt:solid windowtext .5pt;"
    'padding:0in 5.4pt 0in 5.4pt" valign="top" width="228">'
)

BODY_TD3_OPEN = (
    '<td style="width:3.2in;border-top:none;border-left:none;'
    "border-bottom:solid windowtext .5pt;border-right:solid "
    "windowtext .5pt;mso-border-top-alt:solid windowtext .5pt;"
    "mso-border-left-alt:solid windowtext .5pt;"
    'padding:0in 5.4pt 0in 5.4pt" valign="top" width="307">'
)


def wordtable(picture: str, rows: "list[_table.Row]") -> str:
    out = (
        _table.XMLDECL + '<html xmlns="http://www.w3.org/TR/REC-html40" '
        'xmlns:w="urn:schemas-microsoft-com:office:word" '
        'xmlns:o="urn:schemas-microsoft-com:office:office">'
        "<head>"
        '<meta content="text/html; charset=windows-1252" '
        'http-equiv="Content-Type"/>'
        '<meta content="Word.Document" name="ProgId"/>'
        '<meta content="Microsoft Word 9" name="Generator"/>'
        '<meta content="Microsoft Word 9" name="Originator"/>'
        "<style/></head>"
        '<body style="tab-interval:.5in" lang="EN-US">'
        '<div class="Section1"><pre>'
    )
    out += picture + "</pre>" + TABLE_OPEN + HEADER_ROW
    for r in rows:
        out += "<tr>"
        out += (
            BODY_TD1_OPEN
            + '<p class="MsoNormal"><message><a name="t'
            + str(r["num"])
            + '"/><a href="#m'
            + str(r["num"])
            + '">'
            + str(r["num"])
            + "</a></message></p></td>"
        )
        out += (
            BODY_TD2_OPEN
            + '<p class="MsoNormal">'
            + _table.caption_body(r["captions"])
            + _table.note_body(r["notes"])
            + "</p></td>"
        )
        out += (
            BODY_TD3_OPEN
            + '<p class="MsoNormal"><span style="font-family:&quot;'
            + 'Courier New&quot;">'
            + _table.comment_body(r["comments"])
            + "<o:p/></span></p></td>"
        )
        out += "</tr>"
    return out + "</table></div></body></html>"
