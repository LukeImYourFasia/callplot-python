"""Shared cells for the six legacy table styles (section 3.13).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Xalan's XML output method closes an empty element as <foo/> (section 3.13.3
rule 5), so a cell with no content is <td/>.  Note/comment text nodes get
their own lines from printComment, so value-of copies the newlines.
"""

XMLDECL = '<?xml version="1.0" encoding="UTF-8"?>\n'


def linkCell(num):
    """col 1 cell with the diagram link (all styles except nolinks)."""
    return ("<td><message><a name=\"t" + str(num) + "\"/><a href=\"#m" +
            str(num) + "\">" + str(num) + "</a></message></td>")


def plainCell(num):
    """col 1 cell without links (nolinks)."""
    return "<td><message>" + str(num) + "</message></td>"


def tdCell(html):
    """a <td> holding html, or <td/> when html is empty (rule 5)."""
    return "<td/>" if html == "" else "<td>" + html + "</td>"


def noteBody(notes):
    return noteOrCommentBody(notes)


def commentBody(comments):
    return noteOrCommentBody(comments)


def noteOrCommentBody(items):
    """"\ntext\n" per item then the <br/>: the newlines come from printComment
    printing each on its own line (section 3.4.1)."""
    s = ""
    for n in items:
        s += "\n" + n + "\n" + "<br/>"
    return s


def captionBody(captions):
    s = ""
    for c in captions:
        s += c + "<br/>"
    return s


def ttCell(comments):
    """col 3 of archtable/htmltable/nolinks: the <tt> stays even when empty,
    so an empty comments list serializes as <td><tt/></td> (rule 6)."""
    body = noteOrCommentBody(comments)
    inner = "<tt/>" if body == "" else "<tt>" + body + "</tt>"
    return "<td>" + inner + "</td>"


def strongCell(captions):
    s = ""
    for c in captions:
        s += "<strong>" + c + "</strong><br/>"
    return s


def codeCell(notes):
    s = ""
    for n in notes:
        s += "<code>\n" + n + "\n</code><br/>"
    return s
