"""Snapshot layer: the 4 new outputs equal the approved JS snapshots.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

DESIGN-PYTHON.md sections 4.1, 4.7 and 5.4 rule 6 (the [snapshot] layer).
These outputs have no Java oracle: Mermaid, PlantUML and the two `-html`
layouts were approved once in the JS port and pinned in `test/snapshots/`,
which is read only.  Python never writes a snapshot (DESIGN-PYTHON.md
section 4.3), so a mismatch means the port is wrong and the snapshot stays
as it is; if the snapshot itself looks wrong, stop and tell Edgar.

A fixture that crashes writes no bytes and its snapshot is empty, so the
same byte comparison covers it: the port's throw yields `b""`, which is
what the approved corpus holds.
"""

import pytest
from conftest import case_id, diff_message
from paths import FIXTURES_DIR, SNAPSHOTS_DIR

from callplot.api import render
from callplot.constants import Mode
from callplot.context import RunContext
from callplot.errors import CallplotError
from callplot.options import HtmlLayout, RenderOptions

# snapshot extension -> (mode, forced layout).  The two page layouts are the
# same renderer with a different option, so both are one extension each.
SNAP_EXT: dict[str, tuple[Mode, RenderOptions | None]] = {
    ".mmd": (Mode.MERMAID, None),
    ".puml": (Mode.PLANTUML, None),
    ".html-topbottom.html": (Mode.HTML, RenderOptions(html_layout=HtmlLayout.TOPBOTTOM)),
    ".html-sidebyside.html": (
        Mode.HTML,
        RenderOptions(html_layout=HtmlLayout.SIDEBYSIDE),
    ),
}

SNAPSHOTS: list[tuple[str, str, str]] = [
    (snap.name, ext, snap.name[: -len(ext)])
    for snap in sorted(SNAPSHOTS_DIR.iterdir())
    if snap.is_file()
    for ext in [max((cand for cand in SNAP_EXT if snap.name.endswith(cand)), key=len, default="")]
    if ext
]


@pytest.mark.snapshot
@pytest.mark.parametrize(
    ("name", "ext", "fixture"),
    SNAPSHOTS,
    ids=[case_id(name) for name, _, _ in SNAPSHOTS],
)
def test_snapshot(name: str, ext: str, fixture: str) -> None:
    """One approved snapshot: the port's bytes, or nothing when it throws."""
    want = (SNAPSHOTS_DIR / name).read_bytes()
    mode, options = SNAP_EXT[ext]
    text = (FIXTURES_DIR / fixture).read_bytes().decode("utf-8", "replace")
    try:
        got = render(text, mode, ctx=RunContext(), options=options).encode("utf-8", "replace")
    except CallplotError:
        got = b""
    assert got == want, diff_message(name, want, got)
