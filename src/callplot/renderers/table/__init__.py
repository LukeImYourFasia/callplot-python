"""Shared row list and entry for the six legacy table styles (DESIGN.md
section 3.13).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

DESIGN.md D8: there is no XML intermediate: this builds the diagram lines
and the row list from Flow, and one style file writes the same bytes Xalan
writes. Xalan parses the -xml line stream, so malformed picture/annotation
text exits 255 in the oracle (section 3.13.4), and Xalan rewrites the
copied single-quoted link attributes to double quotes (section 3.13.3 rule
3). options.table_style picks the style; an unknown style name is rejected
by options.parse_table_style on the command side (section 2.3).

DESIGN-PYTHON.md section 2.2: this file holds JS's table/index.js and
table/common.js merged.  The six style modules import this package as a
plain module object (not by name): this __init__ imports them, so at THEIR
import time this package is only partially initialized; their functions
reach the shared cells through the object, which is complete by the time
they run.  ``Row`` is referenced only inside string annotations so it is
never evaluated at runtime either.

Rows stay plain dicts (logged as an errata in docs/appendix-b.md: section
2.5 asks for dataclasses, but the row list is internal to the table
pipeline and the dict shape is JS's); the ``Row`` TypedDict pins it.
"""

import re
from typing import TypedDict

from callplot.constants import Mode
from callplot.errors import TableInputError
from callplot.flow import Flow
from callplot.options import RenderOptions, TableStyle
from callplot.renderers.table.archtable import archtable
from callplot.renderers.table.htmltable import htmltable
from callplot.renderers.table.htmltable2 import htmltable2
from callplot.renderers.table.htmltable3 import htmltable3
from callplot.renderers.table.nolinks import nolinks
from callplot.renderers.table.wordtable import wordtable
from callplot.renderers.text import draw_text_lines

# --- Shared cells (DESIGN.md section 3.13.2: Xalan's output rules) ------

XMLDECL = '<?xml version="1.0" encoding="UTF-8"?>\n'


class Row(TypedDict):
    """One table row: numbered message, already-escaped text parts."""

    num: int
    captions: list[str]
    notes: list[str]
    comments: list[str]


def link_cell(num: int) -> str:
    """col 1 cell with the diagram link (all styles except nolinks)."""
    return (
        '<td><message><a name="t'
        + str(num)
        + '"/><a href="#m'
        + str(num)
        + '">'
        + str(num)
        + "</a></message></td>"
    )


def plain_cell(num: int) -> str:
    """col 1 cell without links (nolinks)."""
    return "<td><message>" + str(num) + "</message></td>"


def td_cell(html: str) -> str:
    """a <td> holding html, or <td/> when html is empty (rule 5)."""
    return "<td/>" if html == "" else "<td>" + html + "</td>"


def note_or_comment_body(items: list[str]) -> str:
    """ "\ntext\n" per item then the <br/>: the newlines come from printComment
    printing each on its own line (section 3.4.1)."""
    s = ""
    for n in items:
        s += "\n" + n + "\n" + "<br/>"
    return s


def note_body(notes: list[str]) -> str:
    return note_or_comment_body(notes)


def comment_body(comments: list[str]) -> str:
    return note_or_comment_body(comments)


def caption_body(captions: list[str]) -> str:
    s = ""
    for c in captions:
        s += c + "<br/>"
    return s


def tt_cell(comments: list[str]) -> str:
    """col 3 of archtable/htmltable/nolinks: the <tt> stays even when empty,
    so an empty comments list serializes as <td><tt/></td> (rule 6)."""
    body = note_or_comment_body(comments)
    inner = "<tt/>" if body == "" else "<tt>" + body + "</tt>"
    return "<td>" + inner + "</td>"


def strong_cell(captions: list[str]) -> str:
    s = ""
    for c in captions:
        s += "<strong>" + c + "</strong><br/>"
    return s


def code_cell(notes: list[str]) -> str:
    s = ""
    for n in notes:
        s += "<code>\n" + n + "\n</code><br/>"
    return s


# --- Xalan validation (DESIGN.md section 3.13.4) -------------------------

# An entity as XML defines it; writeLineXml already escaped < and >, so only
# a bare & can break Xalan's parse of a picture line.
ENTITY_RE = re.compile(r"&(?:lt;|gt;|amp;|quot;|apos;|#[0-9]+;|#x[0-9a-fA-F]+;)")

# Xalan's serializer re-quotes the copied link attributes (rule 3).
LINK_T_REF = re.compile(r"href='#(t\d+)'>")
LINK_NAME_REF = re.compile(r"name='(m\d+)'/>")


def fix_link_quotes(line: str) -> str:
    line = LINK_T_REF.sub('href="#\\1">', line)
    return LINK_NAME_REF.sub('name="\\1"/>', line)


def check_picture_line(line: str) -> None:
    for i in range(len(line)):
        if line[i] == "&" and ENTITY_RE.match(line, i) is None:
            raise TableInputError("picture text contains a bare '&'")


def escape_annotated(text: str) -> str:
    """Section 3.13.4 for annotation text: decode the entities the way
    Xalan's parse does (raw '<' and bare '&' throw), then re-print per
    rule 8: only < > & become entities, quotes and everything else stay
    as they are."""
    res: list[str] = []
    i = 0
    while i < len(text):
        c = text[i]
        if c == "<":
            raise TableInputError("annotation text contains raw '<'")
        if c == ">":
            res.append("&gt;")
            i += 1
            continue
        if c != "&":
            res.append(c)
            i += 1
            continue
        m = ENTITY_RE.match(text, i)
        if m is None:
            raise TableInputError("annotation text contains a bare '&'")
        ent = m.group(0)
        if ent == "&lt;":
            ch = "<"
        elif ent == "&gt;":
            ch = ">"
        elif ent == "&amp;":
            ch = "&"
        elif ent == "&quot;":
            ch = '"'
        elif ent == "&apos;":
            ch = "'"
        elif ent[2] == "x":
            cp = int(ent[3:-1], 16)
            if cp <= 0 or cp > 0x10FFFF:
                raise TableInputError("bad character reference " + ent)
            ch = chr(cp)
        else:
            cp = int(ent[2:-1], 10)
            if cp <= 0 or cp > 0x10FFFF:
                raise TableInputError("bad character reference " + ent)
            ch = chr(cp)
        if ch == "<":
            res.append("&lt;")
        elif ch == ">":
            res.append("&gt;")
        elif ch == "&":
            res.append("&amp;")
        else:
            res.append(ch)
        i = m.end()
    return "".join(res)


# --- Entry point ----------------------------------------------------------


def table_on(f: Flow, options: RenderOptions) -> str:
    """The whole table document; options.table_style picks the style.

    Step order per section 3.13.1: draw the XML line stream FIRST (that
    also runs the numbering and sets my_number), then validate every line
    and every annotation text node, then serialize the rows.
    """
    lines = draw_text_lines(f, Mode.XML, None)

    picture: list[str] = []
    for line in lines:
        check_picture_line(line)
        picture.append(fix_link_quotes(line))

    rows: list[Row] = []
    for m in f.messages:
        if m.my_number != 0:
            rows.append(
                {
                    "num": m.my_number,
                    "captions": [escape_annotated(c) for c in m.caption],
                    "notes": [escape_annotated(c) for c in m.notes],
                    "comments": [escape_annotated(c) for c in m.comments],
                }
            )

    picture_doc = "<picture>\n" + "\n".join(picture) + "\n</picture>"
    match options.table_style:
        case TableStyle.ARCHTABLE:
            return archtable(picture_doc, rows)
        case TableStyle.HTMLTABLE:
            return htmltable(picture_doc, rows)
        case TableStyle.HTMLTABLE2:
            return htmltable2(picture_doc, rows)
        case TableStyle.HTMLTABLE3:
            return htmltable3(picture_doc, rows)
        case TableStyle.NOLINKS:
            return nolinks(picture_doc, rows)
        case TableStyle.WORDTABLE:
            return wordtable(picture_doc, rows)
        case _:
            raise TableInputError(f"unknown table style: {options.table_style}")
