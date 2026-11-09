"""The public render entry point (DESIGN.md section 4.1 API, DESIGN-PYTHON.md
sections 2.3, 3.6 and 3.7).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

DESIGN-PYTHON.md section 3.7 rule 2: render() does ``to_units``, parse,
layout, the ``match`` renderer pick, ``from_units``.  Rule 2/3: the pick is
a ``match`` statement with a closing ``case _:``, and ``case Mode.VXML:``
is an alias member so it matches the combined flag.  Rule: import every
renderer at the top; no dynamic import by name.
"""

import io

from callplot.constants import Mode
from callplot.context import RunContext
from callplot.errors import CallplotError
from callplot.flow import Flow
from callplot.ir import build_model
from callplot.jcompat import from_units, to_units
from callplot.options import RenderOptions
from callplot.parser import parse
from callplot.renderers.graffle import graffle_on
from callplot.renderers.html.page import page_on
from callplot.renderers.mermaid import mermaid_on
from callplot.renderers.pic import pic_on
from callplot.renderers.plantuml import plantuml_on
from callplot.renderers.svg import svg_on
from callplot.renderers.table import table_on
from callplot.renderers.text import text_on
from callplot.renderers.vml import vml_on


def render(
    text: str,
    mode: Mode,
    *,
    ctx: RunContext | None = None,
    options: RenderOptions | None = None,
) -> str:
    """Whole output as a string; fresh counters by default.

    Raises a CallplotError on bad input and returns no output (section 2.3).
    It never prints and never reads a file.
    """
    if ctx is None:
        ctx = RunContext()
    if options is None:
        options = RenderOptions()
    f = parse(to_units(text))
    f.layout()
    out = io.StringIO()
    match mode:
        case Mode.TABLE:
            out.write(table_on(f, options))
        case Mode.MERMAID:
            # new outputs (DESIGN.md sections 3.10/3.11): read the IR,
            # built after layout()
            out.write(mermaid_on(build_model(f)))
        case Mode.PLANTUML:
            out.write(plantuml_on(build_model(f)))
        case Mode.HTML:
            # new output (DESIGN.md section 3.12): options pick the layout
            # and the link id prefix
            out.write(page_on(build_model(f), options))
        case Mode.PIC:
            out.write(pic_on(f, mode))
        case Mode.SVG:
            out.write(svg_on(f, mode, ctx))
        case Mode.VML:
            out.write(vml_on(f, mode, ctx))
        case Mode.VXML:
            out.write(vml_on(f, mode, ctx))
        case Mode.GRAFFLE:
            out.write(graffle_on(f, mode, ctx))
        case Mode.TEXT:
            out.write(text_on(f, mode))
        case Mode.XML:
            out.write(text_on(f, mode))
        case _:
            raise CallplotError(f"unknown output mode: {mode}")
    return from_units(out.getvalue())


def flow(text: str) -> Flow:
    """parse + layout: the model the renderers and tests share."""
    f = parse(to_units(text))
    f.layout()
    return f
