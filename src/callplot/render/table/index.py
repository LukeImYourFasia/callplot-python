"""The legacy table styles entry point (DESIGN.md section 3.13).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

There is no XML intermediate (DESIGN.md D8): this builds the diagram lines
and the row list from Flow, and one style file writes the same bytes Xalan
writes. Xalan parses the -xml line stream, so malformed picture/annotation
text exits 255 in the oracle (section 3.13.4), and Xalan rewrites the
copied single-quoted link attributes to double quotes (section 3.13.3
rule 3). opts.tableStyle picks the style; unknown style throws.
"""

import re

from ...constants import MODES
from ..text import drawTextLines
from .archtable import archtable
from .htmltable import htmltable
from .htmltable2 import htmltable2
from .htmltable3 import htmltable3
from .nolinks import nolinks
from .wordtable import wordtable


class TableInputError(Exception):
    """Xalan would reject this input: the oracle exits 255 (section 3.13.4)."""


# An entity as XML defines it; writeLineXml already escaped < and >, so only
# a bare & can break Xalan's parse of a picture line.
ENTITY_RE = re.compile(
    r"&(?:lt;|gt;|amp;|quot;|apos;|#[0-9]+;|#x[0-9a-fA-F]+;)")

# Xalan's serializer re-quotes the copied link attributes (rule 3).
LINK_T_REF = re.compile(r"href='#(t\d+)'>")
LINK_NAME_REF = re.compile(r"name='(m\d+)'/>")


def fixLinkQuotes(line):
    line = LINK_T_REF.sub("href=\"#\\1\">", line)
    return LINK_NAME_REF.sub("name=\"\\1\"/>", line)


def checkPictureLine(line):
    for i in range(len(line)):
        if line[i] == "&" and ENTITY_RE.match(line, i) is None:
            raise TableInputError("picture text contains a bare '&'")


def escapeAnnotated(text):
    """Section 3.13.4 for annotation text: decode the entities the way
    Xalan's parse does (raw '<' and bare '&' throw), then re-print per
    rule 8: only < > & become entities, quotes and everything else stay
    as they are."""
    res = []
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


def tableOn(f, out, mode, opts):
    """mode is unused (a table IS the mode); opts.tableStyle picks the style.

    Step order per section 3.13.1: draw the XML line stream FIRST (that
    also runs the numbering and sets myNumber), then validate every line
    and every annotation text node, then serialize the rows.
    """
    lines = drawTextLines(f, MODES["XML"], None)

    picture = []
    for l in lines:
        checkPictureLine(l)
        picture.append(fixLinkQuotes(l))

    rows = []
    for m in f.messages:
        if m.myNumber != 0:
            rows.append({
                "num": m.myNumber,
                "captions": [escapeAnnotated(c) for c in m.caption],
                "notes": [escapeAnnotated(c) for c in m.notes],
                "comments": [escapeAnnotated(c) for c in m.comments],
            })

    key = opts["tableStyle"] if "tableStyle" in opts else "archtable"
    style = STYLES.get(key)
    if style is None:
        raise TableInputError("unknown table style")
    # section 3.13.3 rule 2: no line end at the very end of the file
    out.print(style("<picture>\n" + "\n".join(picture) +
                    "\n</picture>", rows))


# tmltable is a byte copy of htmltable.xsl (section 1.3), so it aliases.
STYLES = {
    "archtable": archtable,
    "htmltable": htmltable,
    "tmltable": htmltable,
    "htmltable2": htmltable2,
    "htmltable3": htmltable3,
    "nolinks": nolinks,
    "wordtable": wordtable,
}

# section 3.7 CLI validation reads this list (unknown style: exit 1)
TABLE_STYLES = list(STYLES)
