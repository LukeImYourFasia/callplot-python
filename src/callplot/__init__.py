"""callplot: a bug-compatible Python port of the Java tool callplot 0.2.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Public API (DESIGN.md section 2.3):

    from callplot import render, parse, MODES, RunContext, prep

render(text, mode, ctx, opts) returns the whole output as a string; opts
carries tableStyle, htmlLayout and idPrefix.  Names land chunk by chunk:
prep arrives with the packet-trace converter, so it is re-exported when it
exists.
"""

from .index import parse, plotFlow, render, pictureFlow
from .constants import MODES
from .context import RunContext
from .prep import prep

__all__ = ["parse", "plotFlow", "render", "pictureFlow", "MODES", "RunContext",
           "prep"]
