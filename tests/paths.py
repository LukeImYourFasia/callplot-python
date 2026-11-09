"""One place for every path (DESIGN-PYTHON.md section 4.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Every shared folder is reached from here, so no test module builds a path of
its own.  The shared folders belong to the JS port and are read only:
DESIGN-PYTHON.md section 4.3 and section 5.4 rule 4.  Python never writes in
``test/golden``, ``test/snapshots``, ``samples/reference`` or ``reference``.

Delta from the design, logged in docs/appendix-b.md: section 4.2 writes
``REPO_ROOT = Path(__file__).resolve().parents[2]`` for ``python/tests/paths.py``
inside the JS repository.  This repository *is* the Python port, so the
package root sits one level up and the value here is ``parents[1]``.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

FIXTURES_DIR = REPO_ROOT / "test" / "fixtures"
GOLDEN_DIR = REPO_ROOT / "test" / "golden"
SNAPSHOTS_DIR = REPO_ROOT / "test" / "snapshots"
CLI_DIR = REPO_ROOT / "test" / "cli"
CLI_GOLDEN_DIR = GOLDEN_DIR / "cli"
FUZZ_DIR = FIXTURES_DIR / "fuzz"
SAMPLES_DIR = REPO_ROOT / "samples"
REFERENCE_DIR = SAMPLES_DIR / "reference"
BUILD_DIR = REPO_ROOT / "reference" / "build"
BUILD_TOOLS_DIR = REPO_ROOT / "reference" / "build-tools"
ORACLE_DIR = REPO_ROOT / "tools" / "oracle"

COMMANDS = ("callplot", "plottable", "callplot-prep")
