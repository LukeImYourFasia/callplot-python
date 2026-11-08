"""The CLI's single entry point (DESIGN.md section 4.1).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Everything else in src/ is pure and importable without side effects; the
interpreter's standard library lives in bin/ only.

Renderer modules land per chunk; the dispatch here is static (DESIGN.md
section 2.5 #6.17: pick one with a switch).  A mode whose renderer has not
landed yet raises a programmer error, so its goldens stay red until the
renderer is ported.
"""

from .parser import parse as parseDoc
from .render.text import plotOn
from .out import Out
from .constants import MODES
from .context import RunContext
from .ir import buildModel


class RendererNotPortedError(Exception):
    """Programmer error: the chunk that lands this renderer has not run."""


def _renderer(name):
    """The static dispatch table, filled as renderer chunks land."""
    return _LANDED[name]


_LANDED = {
    "text": plotOn,
    # pic, svg, vml and graffle land with their chunks; mermaid/plantuml/html,
    # the table styles and callplot-prep land with theirs.
}


def parse(text):
    """parse(text): Flow (Parser.java:37-166 via parser.py)"""
    return parseDoc(text)


def pictureFlow(f, out, mode, ctx):
    """The dispatch inside Flow.java:77-80. Renderer modules land per chunk:
    pic, svg, vml, graffle."""
    if (mode & MODES["GRAFFLE"]) != 0:
        _renderer("graffle")(f, out, mode, ctx)
    elif (mode & MODES["VML"]) != 0:
        _renderer("vml")(f, out, mode, ctx)
    elif (mode & MODES["SVG"]) != 0:
        _renderer("svg")(f, out, mode, ctx)
    else:
        _renderer("pic")(f, out, mode)


def plotFlow(text, out, mode, ctx=None, opts=None):
    if ctx is None:
        ctx = RunContext()
    if opts is None:
        opts = {}
    f = parse(text)
    f.layout()
    if (mode & MODES["TABLE"]) != 0:
        _renderer("table")(f, out, mode, opts)
    elif (mode & MODES["MERMAID"]) != 0:
        # new output (section 3.10): reads the IR, built after layout()
        _renderer("mermaid")(buildModel(f), out)
    elif (mode & MODES["PLANTUML"]) != 0:
        _renderer("plantuml")(buildModel(f), out)
    elif (mode & MODES["HTML"]) != 0:
        # new output (section 3.12): opts picks layout and idPrefix
        _renderer("html")(buildModel(f), out, opts)
    elif (mode & (MODES["PIC"] | MODES["VML"] | MODES["SVG"] | MODES["GRAFFLE"])) != 0:
        pictureFlow(f, out, mode, ctx)
    else:
        _renderer("text")(f, out, mode)


def render(text, mode, ctx=None, opts=None):
    """Section 2.3 public API: whole output as a string, fresh counters by
    default. Throws on any Java throw (leaves no result behind)."""
    if ctx is None:
        ctx = RunContext()
    if opts is None:
        opts = {}
    out = Out()
    plotFlow(text, out, mode, ctx, opts)
    return out.toString()
