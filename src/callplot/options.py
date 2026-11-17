"""Render options (DESIGN-PYTHON.md sections 2.3 and 3.1).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

The option bag of the JS port becomes a frozen ``RenderOptions`` dataclass
and ``enum`` types (DESIGN-PYTHON.md section 1.2: "Option objects {
tableStyle: 'x' } | a frozen dataclass and enum types").  Names that
appear in input or output (the style names, the layout names) keep the
DESIGN.md spelling exactly as the enum *values*.
"""

from dataclasses import dataclass
from enum import StrEnum

from callplot.errors import IllegalArgumentError


class TableStyle(StrEnum):
    """The six legacy table styles (DESIGN.md section 3.13.2)."""

    ARCHTABLE = "archtable"
    HTMLTABLE = "htmltable"
    HTMLTABLE2 = "htmltable2"
    HTMLTABLE3 = "htmltable3"
    NOLINKS = "nolinks"
    WORDTABLE = "wordtable"


class HtmlLayout(StrEnum):
    """The two -html page layouts (DESIGN.md section 3.12.6)."""

    TOPBOTTOM = "topbottom"
    SIDEBYSIDE = "sidebyside"


@dataclass(frozen=True)
class RenderOptions:
    """The frozen option object of the public API (section 2.3)."""

    table_style: TableStyle = TableStyle.ARCHTABLE
    html_layout: HtmlLayout | None = None
    id_prefix: str = ""


def parse_table_style(name: str) -> TableStyle:
    """Map a style name to a TableStyle.

    ``tmltable`` aliases ``htmltable``: lib/tmltable.xsl is a byte copy of
    htmltable.xsl (DESIGN.md section 1.3).  An unknown name raises
    (section 2.3).
    """
    if name == "tmltable":
        return TableStyle.HTMLTABLE
    try:
        return TableStyle(name)
    except ValueError:
        raise IllegalArgumentError(f"unknown table style: {name}") from None


def parse_html_layout(value: str) -> HtmlLayout:
    """Map a layout name; an unknown value raises (section 2.3)."""
    try:
        return HtmlLayout(value)
    except ValueError:
        raise IllegalArgumentError(f"unknown html layout: {value}") from None
