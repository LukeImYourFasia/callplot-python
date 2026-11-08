"""Snapshot tests for the new outputs (DESIGN.md section 4.7).

There is no Java oracle for mermaid/plantuml/html: the first approved run of
each new output is stored under test/snapshots, and later runs must match it
byte for byte.  The snapshot itself is the oracle; a mismatch means the port
drifted since approval (the snapshot is regenerated only by the explicit
snapshot-update tool, never by hand).

New modes land per chunk: mermaid and plantuml land with this harness; the
html layouts are added when the html renderer lands.  A missing snapshot
fails as a programmer error ("run the snapshot-update tool"), never silently.
"""

import difflib
import os
import re

import unittest

from callplot import plotFlow, MODES
from callplot.out import Out
from callplot.context import RunContext

# ext is the snapshot file extension; opts carry htmlLayout/idPrefix picks.
NEW_MODES_DONE = {
    "mermaid": {"flag": MODES["MERMAID"], "ext": "mmd", "opts": {}},
    "plantuml": {"flag": MODES["PLANTUML"], "ext": "puml", "opts": {}},
    # html_topbottom / html_sidebyside join this map when html lands:
    # "html_topbottom": {flag MODES.HTML, ext "html-topbottom.html",
    #                    opts {"htmlLayout": "topbottom"}}
}

FIXTURES = os.path.join("test", "fixtures")
SNAPS = os.path.join("test", "snapshots")


def _case(fixture, mode_name, m):
    """One [snapshot] comparison: render fresh, byte-compare the snapshot.

    Same stdout model as the golden runner (DESIGN.md 4.4): a throw cuts
    stdout at the last whole 8192-byte PrintWriter buffer.
    """
    def check(self):
        snapshot = os.path.join(SNAPS, fixture + "." + m["ext"])
        if not os.path.exists(snapshot):
            raise self.fail("no snapshot for %s %s: run the snapshot-update "
                            "tool (tools/snapshot-update.py)" %
                            (fixture, mode_name))
        with open(os.path.join(FIXTURES, fixture), "rb") as fh:
            text = fh.read().decode("utf-8")
        out = Out()
        ctx = RunContext()
        thrown = None
        try:
            plotFlow(text, out, m["flag"], ctx, m["opts"])
        except Exception as err:  # snapshot runs may legitimately crash
            thrown = err
        got = out.toString().encode("utf-8")
        if thrown is not None:
            got = got[0:(len(got) // 8192) * 8192]
        want = open(snapshot, "rb").read()
        if got != want:
            raise self.fail(_diff(fixture + " " + mode_name, want, got))
    return check


def _diff(label, want, got):
    """A unified diff between the approved snapshot and ours."""
    w = want.decode("utf-8", "replace").splitlines(True)
    g = got.decode("utf-8", "replace").splitlines(True)
    body = "".join(difflib.unified_diff(
        g, w, fromfile="port " + label, tofile="snapshot " + label))
    return label + ": snapshot bytes differ\n" + body


class Snapshot(unittest.TestCase):
    """Populated at import time, one method per fixture and new mode."""


def _install_cases():
    for fixture in sorted(os.listdir(FIXTURES)):
        if fixture.endswith(".trace"):
            continue  # prep inputs, not callplot inputs
        for mode_name, m in NEW_MODES_DONE.items():
            name = "test_snapshot_" + re.sub(r"[^a-z0-9]+", "_",
                                             fixture + "_" + mode_name).lower()
            setattr(Snapshot, name, _case(fixture, mode_name, m))


_install_cases()
