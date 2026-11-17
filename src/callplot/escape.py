"""Escapes for the new outputs (DESIGN.md sections 3.10, 3.11, 3.12).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

DESIGN-PYTHON.md section 3.7 rule 5: each escape is one character table
handed to ``str.translate``.  ``translate`` changes every character in
ONE pass, so escapes it emits are never re-escaped (DESIGN.md section
3.10 one-pass rule).  ``html.escape`` is NOT used: it writes ' as &#x27;,
not the &#39; of DESIGN.md section 3.12.1.
"""

_HTML_TABLE = str.maketrans(
    {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }
)

_MERMAID_TABLE = str.maketrans(
    {
        "#": "#35;",
        ";": "#59;",
        "<": "#lt;",
        ">": "#gt;",
        '"': "#quot;",
    }
)

# Deviation logged at W13 (kept from the JS port, DESIGN.md appendix): the
# pinned plantuml.jar rejects ~" inside a quoted participant string, so "
# becomes &#34; instead; the jar parses &#34; everywhere and renders it as
# a literal " (the approved snapshots pin this form).
_PLANTUML_TABLE = str.maketrans(
    {
        '"': "&#34;",
        "~": "~~",
        "*": "~*",
        "_": "~_",
        "/": "~/",
        "-": "~-",
        "<": "~<",
        "[": "~[",
        "\\": "~\\",
    }
)


def esc_html(text: str) -> str:
    """HTML escapes for the -html page (sections 3.12.1 + 3.12.3)."""
    return text.translate(_HTML_TABLE)


def esc_mermaid(text: str) -> str:
    """Mermaid escapes (DESIGN.md section 3.10): # ; < > "."""
    return text.translate(_MERMAID_TABLE)


def esc_plantuml(text: str) -> str:
    """PlantUML escapes (DESIGN.md section 3.11): ~ before each markup
    character; " as &#34; (deviation note above)."""
    return text.translate(_PLANTUML_TABLE)
