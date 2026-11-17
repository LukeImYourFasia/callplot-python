"""Mode bits for the renderers (DESIGN.md sections 1.4 and 2.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Port of CallplotConstants.java:30-49.  VML_X_SIZE and VML_BOX_PERCENT are
unused by the program (see Flow.java).  Bit values are internal: no golden
or CLI output depends on them.  The new bits follow DESIGN.md section 2.2
exactly (TABLE at 0x200, so HTML keeps the section's 0x100).

DESIGN-PYTHON.md section 2.3: ``Mode`` is an ``IntFlag``, and VXML is an
alias member so ``case Mode.VXML:`` in api.py matches the combined flag.
"""

from enum import IntFlag


class Mode(IntFlag):
    TEXT = 0x01
    PIC = 0x02
    XML = 0x04
    VML = 0x08
    SVG = 0x10
    GRAFFLE = 0x20
    MERMAID = 0x40
    PLANTUML = 0x80
    HTML = 0x100
    TABLE = 0x200
    VXML = VML | XML


GRAFFLE_MULT = 14
GRAFFLE_TOP_MARG = 15
GRAFFLE_LINE_TXT_OFST = -7

VML_TEXT_XOFF = 1
VML_TEXT_YOFF = 2
