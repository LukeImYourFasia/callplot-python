"""Mode bits for the renderers.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Port of CallplotConstants.java:30-49 (Python by Edgar Villanueva).
VML_X_SIZE and VML_BOX_PERCENT are unused by the program (see Flow.java).

Bit values are internal: no golden or CLI output depends on them.
The new bits follow DESIGN.md section 2.2 exactly (TABLE at 0x200, so
HTML keeps the section's 0x100).
"""

MODES = {
    "TEXT": 0x01,
    "PIC": 0x02,
    "XML": 0x04,
    "VML": 0x08,
    "SVG": 0x10,
    "GRAFFLE": 0x20,
    "MERMAID": 0x40,
    "PLANTUML": 0x80,
    "HTML": 0x100,
    "TABLE": 0x200,
}

TEXT = MODES["TEXT"]
PIC = MODES["PIC"]
XML = MODES["XML"]
VML = MODES["VML"]
SVG = MODES["SVG"]
GRAFFLE = MODES["GRAFFLE"]
MERMAID = MODES["MERMAID"]
PLANTUML = MODES["PLANTUML"]
HTML = MODES["HTML"]
TABLE = MODES["TABLE"]

GRAFFLE_MULT = 14
GRAFFLE_TOP_MARG = 15
GRAFFLE_LINE_TXT_OFST = -7

VML_TEXT_XOFF = 1
VML_TEXT_YOFF = 2
