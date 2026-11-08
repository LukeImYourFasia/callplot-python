#!/usr/bin/env python3
"""Test harness: run the stdlib unittest suites and report like node:test does.

Every test method is named test_<tag>_<slug>, so the harness can group counts
by tag ([unit], [golden], [cli], [snapshot], [reference]) and print a
node-test-style summary.  DESIGN.md section 4.1 asks for a unified diff on
any golden mismatch: the golden suite raises that diff as the failure text,
and this harness prints failure text verbatim.

Usage: tools/run-tests.py [tag ...]     (default: every tag)
Exit: 0 when nothing failed, 1 otherwise.
"""

import importlib
import importlib.util
import io
import os
import re
import sys
import time
import unittest


_PKG = "_callplot_tests"


def _suite_path():
    return os.path.join("test")


def _modules():
    """Load every test_*.py under test/ as its own module.

    The files are loaded by path with a private package name: the corpus
    directory is called test/ (the design's layout), and stdlib already owns
    the import name "test", so dotted imports would resolve to the wrong one.
    """
    root = _suite_path()
    names = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for fn in sorted(filenames):
            if not fn.startswith("test_") or not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            modname = _PKG + "." + path.replace(os.sep, ".")[:-3]
            names.append((modname, path))
    return names


def _load(modname, path):
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


class _Case(unittest.TestCase):
    """Single-case wrapper so counts are per test method, per version."""


def _run_one(case):
    """Run one TestCase instance; return (kind, label, text)."""
    buf = io.StringIO()
    runner = unittest.TextTestRunner(stream=buf, verbosity=0)
    result = runner.run(unittest.TestSuite([case]))
    ident = case.id()
    if callable(ident):
        ident = ident()
    label = _label(ident)
    if result.failures:
        return "fail", label, str(result.failures[0][1])
    if result.errors:
        return "error", label, str(result.errors[0][1])
    if result.skipped:
        item = result.skipped[0]
        reason = item[1] if isinstance(item, tuple) else ""
        return "skip", label, str(reason)
    if result.unexpectedSuccesses:
        return "fail", label, "unexpected success"
    return "pass", label, ""


def _tag_of(ident):
    method = ident.rsplit(".", 1)[-1]
    m = re.match(r"test_([a-z]+)_", method)
    return m.group(1) if m else "untagged"


def _label(ident):
    method = ident.rsplit(".", 1)[-1]
    return re.sub(r"^test_[a-z]+_", "", method).replace("_", " ")


def main(argv):
    # The suites import the callplot package and read the corpus by relative
    # path, so the harness runs from the repo root and puts src on the path.
    sys.path.insert(0, "src")
    sys.path.insert(0, os.getcwd())

    wanted = set(argv)
    suites = []
    for modname, path in _modules():
        mod = _load(modname, path)
        loader = unittest.TestLoader()
        for name in sorted(dir(mod)):
            obj = getattr(mod, name)
            if not (isinstance(obj, type) and issubclass(obj, unittest.TestCase)
                    and getattr(obj, "__test__", True)):
                continue
            for case in loader.loadTestsFromTestCase(obj):
                suites.append(case)

    counts = {}
    failures = []
    t0 = time.time()
    for case in suites:
        ident = case.id()
        if callable(ident):
            ident = ident()
        tag = _tag_of(ident)
        if wanted and tag not in wanted:
            continue
        kind, label, text = _run_one(case)
        counts.setdefault(tag, {}).setdefault(kind, 0)
        counts[tag][kind] += 1
        if kind in ("fail", "error"):
            failures.append((tag, label, text))
    elapsed = time.time() - t0

    for tag, label, text in failures:
        print("[%s] %s: %s" % (tag, label, text.strip()))
    total_pass = total_fail = total_skip = 0
    for tag in sorted(counts):
        got = counts[tag]
        p = got.get("pass", 0)
        f = got.get("fail", 0) + got.get("error", 0)
        s = got.get("skip", 0)
        total_pass += p
        total_fail += f
        total_skip += s
        print("[%s] pass %d / fail %d%s" %
              (tag, p, f, (" / skip %d" % s) if s else ""))
    summary = ("test: pass %d / fail %d%s in %.2fs" %
               (total_pass, total_fail, (" / skip %d" % total_skip)
                if total_skip else "", elapsed))
    print(summary)
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
