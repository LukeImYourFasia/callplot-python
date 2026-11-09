"""callplot: a bug-compatible Python port of the Java tool callplot 0.2.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Public API (DESIGN-PYTHON.md section 2.3)::

    from callplot import render, prep, Mode, RunContext, RenderOptions, TableStyle, HtmlLayout
"""

from importlib import metadata

from callplot.api import render
from callplot.constants import Mode
from callplot.context import RunContext
from callplot.options import HtmlLayout, RenderOptions, TableStyle
from callplot.trace_prep import prep

__all__ = [
    "HtmlLayout",
    "Mode",
    "RenderOptions",
    "RunContext",
    "TableStyle",
    "prep",
    "render",
]


def _version() -> str:
    """__version__ per DESIGN-PYTHON.md section 2.3: read the distribution
    version with importlib.metadata.  Falls back to the source tree's own
    pin when the package is used uninstalled (an editable or wheel install
    always has metadata)."""
    try:
        return metadata.version("callplot-py")
    except metadata.PackageNotFoundError:
        return "0.1.0"


__version__ = _version()
