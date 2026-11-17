"""Golden layer: the port equals the stored Java, Xalan and awk bytes.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

DESIGN-PYTHON.md sections 4.1 and 4.2 (the [golden] layer).  One test per
golden file, found with ``sorted(GOLDEN_DIR.glob("*.out"))``, and the file
name is the test id, so a failing case already names its fixture and mode.
The oracle is the truth (DESIGN.md section 5.4 rule 2; DESIGN-PYTHON.md
section 4.3: "if a golden looks wrong, do not change it. Stop and ask Edgar"),
so a mismatch is reported against the port only.

The exit rule of section 4.2, kept exactly:

* ``<name>.exit`` is ``0`` -> compare stdout bytes, and show a unified diff
  on a mismatch (DESIGN.md section 4.1);
* ``<name>.exit`` is not ``0`` -> ``render()`` must raise a ``CallplotError``
  and stdout is NOT compared, because Java may have written partial bytes
  before it died (DESIGN.md section 3.7).

A programmer error (``KeyError``, ``TypeError``, and so on) escapes the harness
and fails the test; nothing here catches a bare ``Exception``.

The CLI goldens under ``test/golden/cli`` are not part of this layer: they run
through the installed commands in tests/cli/test_cli.py (DESIGN-PYTHON.md
section 4.5).  The four packet traces appear here as ``<base>.prep`` and
``<base>.prep-links`` cases, which read the ``<base>.trace`` fixture.
"""

import pytest
from conftest import case_id, diff_message, exit_of, fixture_of, golden_mode_of, port_bytes
from paths import GOLDEN_DIR

from callplot.errors import CallplotError

CASES: list[tuple[str, str, str]] = [
    (
        out.name[: -len(".out")],
        golden_mode_of(out.name[: -len(".out")]),
        fixture_of(out.name[: -len(".out")]),
    )
    for out in sorted(GOLDEN_DIR.glob("*.out"))
]


@pytest.mark.golden
@pytest.mark.parametrize(
    ("stem", "mode", "fixture"),
    CASES,
    ids=[case_id(stem) for stem, _, _ in CASES],
)
def test_golden(stem: str, mode: str, fixture: str) -> None:
    """One golden: bytes, or the throw the golden's exit code asks for."""
    if mode == "":
        # a golden whose mode this harness does not know is a harness gap,
        # never a silent pass
        raise AssertionError(f"no mode mapping for golden {stem}")

    want_exit = exit_of(stem, GOLDEN_DIR)
    if want_exit == 0:
        want = (GOLDEN_DIR / (stem + ".out")).read_bytes()
        got = port_bytes(fixture, mode)
        assert got == want, diff_message(stem, want, got)
    else:
        with pytest.raises(CallplotError):
            port_bytes(fixture, mode)
