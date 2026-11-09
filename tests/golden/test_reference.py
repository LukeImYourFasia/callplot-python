"""Reference layer: the 5 samples x 17 outputs equal samples/reference.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

DESIGN-PYTHON.md sections 4.1 and 5.3 (PY15) with DESIGN.md section 4.10:
these are the user-facing examples, one folder per sample in
`samples/reference/<sample>/`, 17 outputs each, 5 x 17 = 85 files.  They are
read only: compatible outputs came from the Java oracle and Xalan, the 4 new
outputs were copied from the approved snapshots (DESIGN.md section 4.10 rule
2, `gen-reference`).  The Python port compares to them and never regenerates
them, so a mismatch is a port bug, never a file to rewrite.

The [golden] marker is the right one here (DESIGN-PYTHON.md section 4.1: the
reference row is a golden row): every file holds oracle bytes.

The input of `trace_sip` is its `.msd`, which the awk converter made from
`samples/trace_sip.trace` (DESIGN.md section 4.10); the other 4 samples are
plain callplot input files in `samples/`.
"""

import pytest
from conftest import case_id, diff_message
from paths import REFERENCE_DIR, SAMPLES_DIR

from callplot.api import render
from callplot.constants import Mode
from callplot.context import RunContext
from callplot.options import HtmlLayout, RenderOptions, parse_table_style

# output extension -> (mode, options).  Matching uses the longest candidate,
# so `.vxml.html` never reads as `.vml.html` and a table page never reads as
# a bare `.html`.
REF_EXT: dict[str, tuple[Mode, RenderOptions | None]] = {
    ".txt": (Mode.TEXT, None),
    ".pic": (Mode.PIC, None),
    ".xml": (Mode.XML, None),
    ".vml.html": (Mode.VML, None),
    ".vxml.html": (Mode.VXML, None),
    ".svg": (Mode.SVG, None),
    ".graffle": (Mode.GRAFFLE, None),
    ".mmd": (Mode.MERMAID, None),
    ".puml": (Mode.PLANTUML, None),
    ".html-topbottom.html": (Mode.HTML, RenderOptions(html_layout=HtmlLayout.TOPBOTTOM)),
    ".html-sidebyside.html": (Mode.HTML, RenderOptions(html_layout=HtmlLayout.SIDEBYSIDE)),
    **{
        f".table-{style}.html": (
            Mode.TABLE,
            RenderOptions(table_style=parse_table_style(style)),
        )
        for style in ("archtable", "htmltable", "htmltable2", "htmltable3", "nolinks", "wordtable")
    },
}

SAMPLE_INPUT = {
    "fred": SAMPLES_DIR / "fred",
    "fred2": SAMPLES_DIR / "fred2",
    "fred_annot": SAMPLES_DIR / "fred_annot",
    "sip_annot": SAMPLES_DIR / "sip_annot",
    "trace_sip": REFERENCE_DIR / "trace_sip" / "trace_sip.msd",
}


def ref_case(output_name: str) -> str:
    """The extension that says how this output was made ("" if unknown)."""
    return max((ext for ext in REF_EXT if output_name.endswith(ext)), key=len, default="")


CASES: list[tuple[str, str, str]] = [
    (sample, out.name, ref_case(out.name))
    for sample in sorted(p.name for p in REFERENCE_DIR.iterdir() if p.is_dir())
    for out in sorted((REFERENCE_DIR / sample).iterdir())
    if ref_case(out.name) != ""
]


@pytest.mark.golden
@pytest.mark.parametrize(
    ("sample", "output", "ext"),
    CASES,
    ids=[case_id(output) for _, output, _ in CASES],
)
def test_reference(sample: str, output: str, ext: str) -> None:
    """One reference output: the port's bytes equal the stored ones."""
    mode, options = REF_EXT[ext]
    text = SAMPLE_INPUT[sample].read_bytes().decode("utf-8", "replace")
    got = render(text, mode, ctx=RunContext(), options=options).encode("utf-8", "replace")
    want = (REFERENCE_DIR / sample / output).read_bytes()
    assert got == want, diff_message(f"{sample}/{output}", want, got)
