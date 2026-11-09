"""Shared helpers for every test module (DESIGN-PYTHON.md sections 4.1, 4.2).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Markers come from ``[tool.pytest.ini_options]`` in pyproject.toml and
``--strict-markers`` is in ``addopts``, so every test carries exactly one
marker.  This file makes the shared folders importable as ``paths`` (DESIGN-PYTHON
section 4.2: "one place for every path") and holds the one render/compare pair
that the golden, snapshot and reference harnesses share.

The rules the harnesses follow, all from DESIGN-PYTHON.md section 4.2:

* bytes in, bytes out: the port's text is encoded with ``utf-8, "replace"``
  (section 3.2), never with a locale-dependent write;
* on a mismatch a unified diff is shown, because DESIGN.md section 4.1 asks
  for one;
* a golden whose ``.exit`` file is not ``0`` expects ``render()`` to raise a
  ``CallplotError`` and its stdout is not compared (Java may have leaked
  partial output, DESIGN.md section 3.7);
* a programmer error (``KeyError``, ``TypeError``, and so on) fails the test:
  nothing here catches a bare ``Exception``.
"""

import difflib
import sys
from importlib import import_module
from pathlib import Path
from types import ModuleType

# tests/ is not a package, so the sibling module paths.py is made importable
# here (the design's "one place for every path")
sys.path.insert(0, str(Path(__file__).resolve().parent))

from paths import FIXTURES_DIR

# keep these in one dict: the CLI fallback reuses exactly the modules pip's
# editable finder already loaded, and a bare from-import would load them twice
_PACKAGE: dict[str, ModuleType] = {}

for _pkg_name in ("api", "constants", "context", "errors", "options", "trace_prep"):
    _PACKAGE[_pkg_name] = import_module(f"callplot.{_pkg_name}")
del _pkg_name

render = _PACKAGE["api"].render
Mode = _PACKAGE["constants"].Mode
RunContext = _PACKAGE["context"].RunContext
CallplotError = _PACKAGE["errors"].CallplotError
HtmlLayout = _PACKAGE["options"].HtmlLayout
RenderOptions = _PACKAGE["options"].RenderOptions
parse_table_style = _PACKAGE["options"].parse_table_style
prep = _PACKAGE["trace_prep"].prep

TABLE_STYLES = (
    "archtable",
    "htmltable",
    "tmltable",
    "htmltable2",
    "htmltable3",
    "nolinks",
    "wordtable",
)

# the mode name inside a golden file name -> what render() gets.  The 6 table
# styles share Mode.TABLE and differ by options; ``table-xml`` has no goldens
# (Xalan never ran for that style), so globbing never makes a case for it.
MODE_BY_NAME: dict[str, tuple[Mode, RenderOptions | None]] = {
    "text": (Mode.TEXT, None),
    "xml": (Mode.XML, None),
    "pic": (Mode.PIC, None),
    "svg": (Mode.SVG, None),
    "vml": (Mode.VML, None),
    "vxml": (Mode.VXML, None),
    "graffle": (Mode.GRAFFLE, None),
    "mermaid": (Mode.MERMAID, None),
    "plantuml": (Mode.PLANTUML, None),
    "html-topbottom": (Mode.HTML, RenderOptions(html_layout=HtmlLayout.TOPBOTTOM)),
    "html-sidebyside": (Mode.HTML, RenderOptions(html_layout=HtmlLayout.SIDEBYSIDE)),
    **{
        f"table-{style}": (Mode.TABLE, RenderOptions(table_style=parse_table_style(style)))
        for style in TABLE_STYLES
    },
}

PREP_MODES = ("prep", "prep-links")


def golden_mode_of(stem: str) -> str:
    """The mode part of a ``<fixture>.<mode>`` name: the longest known suffix
    wins, so ``table-archtable`` and ``html-topbottom`` beat their inner dots.
    """
    known = [name for name in MODE_BY_NAME if stem.endswith("." + name)]
    known += [name for name in PREP_MODES if stem.endswith("." + name)]
    if not known:
        return ""
    return max(known, key=len)


def fixture_of(stem: str) -> str:
    """The fixture a golden or snapshot comes from.

    The 4 packet traces are the only fixtures whose name does not match the
    file name in test/fixtures: a ``<base>.prep`` golden reads ``<base>.trace``
    (DESIGN.md section 3.14).
    """
    mode = golden_mode_of(stem)
    if not mode:
        return stem
    base = stem[: -len(".") - len(mode)]
    if mode in PREP_MODES:
        return base + ".trace"
    return base


def port_bytes(fixture: str, mode_name: str) -> bytes:
    """The port's own bytes for one fixture and mode.

    A non-zero-exit golden never reaches the comparison: the CallplotError it
    expects escapes here and the caller asserts it.  Any other exception
    escapes too, which is how a programmer error fails the test.
    """
    text = (FIXTURES_DIR / fixture).read_bytes().decode("utf-8", "replace")
    if mode_name in PREP_MODES:
        return prep(text, links=mode_name == "prep-links").encode("utf-8", "replace")
    mode, options = MODE_BY_NAME[mode_name]
    return render(text, mode, ctx=RunContext(), options=options).encode("utf-8", "replace")


def diff_message(label: str, want: bytes, got: bytes) -> str:
    """DESIGN.md section 4.1: a mismatch shows a unified diff."""
    body = difflib.unified_diff(
        got.decode("utf-8", "replace").splitlines(keepends=True),
        want.decode("utf-8", "replace").splitlines(keepends=True),
        fromfile="port " + label,
        tofile="oracle " + label,
    )
    return f"{label}: bytes differ, {len(got)} port vs {len(want)} oracle\n" + "".join(body)


def exit_of(stem: str, folder: Path) -> int:
    """The exit code a golden pins (section 4.2: read ``<name>.exit``)."""
    return int((folder / (stem + ".exit")).read_text(encoding="utf-8").strip())


def case_id(stem: str) -> str:
    """A pytest-safe id from a golden or snapshot file stem."""
    return "".join(c if c.isalnum() else "_" for c in stem).lower()
