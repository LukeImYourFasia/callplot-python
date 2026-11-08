"""Escapes for the new outputs (DESIGN.md sections 3.10, 3.11, 3.12).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Each escape runs in ONE pass over the text so escapes it emits are never
re-escaped.
"""


def escPlantuml(text):
    """PlantUML escapes (section 3.11): ~ in front of each markup character.

    Deviation logged at W13: the pinned plantuml.jar rejects ~" inside a
    quoted participant string, so " becomes &#34; instead of ~".  The jar
    parses &#34; everywhere and renders it as a literal " in titles,
    participant labels, messages and notes (&quot; also parses but renders
    literally, so the numeric form is the right one).
    """
    out = []
    for c in text:
        if c == '"':
            out.append("&#34;")
        elif c in '~*_/-<[' or c == "\\":
            out.append("~" + c)
        else:
            out.append(c)
    return "".join(out)


def escMermaid(text):
    """Mermaid entity-ish escapes: # ; < > " (section 3.10)."""
    out = []
    for c in text:
        if c == "#":
            out.append("#35;")
        elif c == ";":
            out.append("#59;")
        elif c == "<":
            out.append("#lt;")
        elif c == ">":
            out.append("#gt;")
        elif c == '"':
            out.append("#quot;")
        else:
            out.append(c)
    return "".join(out)


def escHtml(text):
    """HTML escapes for the -html page (sections 3.12.1 + 3.12.3): every
    user string passes through escHtml in text, attributes and link text.
    Single pass."""
    out = []
    for c in text:
        if c == "&":
            out.append("&amp;")
        elif c == "<":
            out.append("&lt;")
        elif c == ">":
            out.append("&gt;")
        elif c == '"':
            out.append("&quot;")
        elif c == "'":
            out.append("&#39;")
        else:
            out.append(c)
    return "".join(out)
