"""Golden test runner: byte-compare the pure core against the oracle goldens.

The goldens come from tools/gen-golden.sh (and gen-golden-extra.sh) run
against the real Java toolchain, recorded in reference/JDK_VERSION,
reference/AWK_VERSION and reference/PLANTUML_VERSION: the oracle output is
always right, so a mismatch means the port is wrong, never the golden
(DESIGN.md sections 4.1 and 5.4 rule 2).

A mismatch prints a unified diff, as DESIGN.md section 4.1 asks.
"""

import difflib
import os
import re

import unittest

from callplot import plotFlow, MODES, RunContext
from callplot.out import Out
from callplot.index import RendererNotPortedError

# Renderers land per chunk; only modes listed here are compared.
MODES_DONE = {
    "text": MODES["TEXT"],
    "xml": MODES["XML"],
    "pic": MODES["PIC"],
}

# Section 3.14: the packet traces through the awk converter, with and without
# --links.  Lands with the prep chunk.
PREP_DONE = {}

FIXTURES = "test/fixtures"
GOLDEN = "test/golden"


def _case(fixture, mode_name, mode_flag, opts):
    """One [golden] comparison: stdout bytes, plus exit semantics.

    The core's Out buffer holds partial output exactly like a crashing
    PrintWriter run: stdout is a PrintWriter over a BufferedWriter with an
    8192-byte buffer, and the final flush (Main.java:74 out.close()) is a
    crashed run's unreachable step, so only whole buffer loads are kept.
    """
    def check(self):
        golden = os.path.join(GOLDEN, fixture + "." + mode_name)
        with open(os.path.join(FIXTURES, fixture), "rb") as fh:
            text = fh.read().decode("utf-8")
        out = Out()
        ctx = RunContext()
        thrown = None
        try:
            plotFlow(text, out, mode_flag, ctx, opts)
        except RendererNotPortedError:
            raise  # a chunk that has not landed is a programmer error
        except Exception as err:  # every other Java throw is pinned below
            thrown = err
        got = out.toString().encode("utf-8")
        with open(golden + ".exit", "r", encoding="utf-8") as fh:
            want_exit = fh.read().strip()
        want = open(golden + ".out", "rb").read()
        flushed = got
        if want_exit != "0" or thrown is not None:
            flushed = got[0:(len(got) // 8192) * 8192]
        if flushed != want:
            raise self.fail(_diff(fixture + " " + mode_name, want, flushed))
        if want_exit == "0":
            if thrown is not None:
                raise self.fail("expected a clean exit, got a throw: %s"
                                % type(thrown).__name__)
        else:
            if thrown is None:
                raise self.fail("expected a throw (exit %s), got a clean run"
                                % want_exit)
    return check


def _diff(label, want, got):
    """A unified diff between the oracle's bytes and ours, as section 4.1 asks."""
    w = want.decode("utf-8", "replace").splitlines(True)
    g = got.decode("utf-8", "replace").splitlines(True)
    body = "".join(difflib.unified_diff(
        g, w, fromfile="port " + label, tofile="oracle " + label))
    return label + ": stdout bytes differ\n" + body


def _prep_case(fixture, mode_name, links):
    """One prep (awk converter) comparison: stdout bytes plus exit 0.

    The prep converter lands with its own chunk; until it does, importing it
    fails as a programmer error rather than a false green.
    """
    def check(self):
        from callplot.prep import prep  # lands with the prep chunk
        base = fixture[: -len(".trace")]
        golden = os.path.join(GOLDEN, base + "." + mode_name)
        raw = open(os.path.join(FIXTURES, fixture), "rb").read().decode("utf-8")
        r = prep(raw, {"links": links})
        got = r["out"].encode("utf-8")
        want = open(golden + ".out", "rb").read()
        if got != want:
            raise self.fail(_diff(base + " " + mode_name, want, got))
        with open(golden + ".exit", "r", encoding="utf-8") as fh:
            want_exit = fh.read().strip()
        if want_exit != "0":
            raise self.fail("prep golden expected exit " + want_exit)
    return check


class Golden(unittest.TestCase):
    """Populated at import time, one method per fixture and mode."""


def _install_cases():
    for fixture in sorted(os.listdir(FIXTURES)):
        for mode_name, mode_flag in MODES_DONE.items():
            opts = {}
            if mode_name.startswith("table-"):
                opts = {"tableStyle": mode_name[len("table-"):]}
            golden = os.path.join(GOLDEN, fixture + "." + mode_name)
            if not os.path.exists(golden + ".out"):
                continue
            name = "test_golden_" + re.sub(r"[^a-z0-9]+", "_",
                                           fixture + "_" + mode_name).lower()
            setattr(Golden, name, _case(fixture, mode_name, mode_flag, opts))
        if fixture.endswith(".trace"):
            for mode_name, links in PREP_DONE.items():
                base = fixture[:-len(".trace")]
                golden = os.path.join(GOLDEN, base + "." + mode_name)
                if not os.path.exists(golden + ".out"):
                    continue
                name = "test_golden_" + re.sub(
                    r"[^a-z0-9]+", "_", base + "_" + mode_name).lower()
                setattr(Golden, name, _prep_case(fixture, mode_name, links))


_install_cases()
