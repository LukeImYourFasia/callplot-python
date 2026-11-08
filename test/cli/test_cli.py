"""CLI cases (DESIGN.md section 4.4, test/cli/*.json).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Every test/cli/*.json lists cmd (default callplot), args and an optional
stdin fixture.  The 8 W0-golden cases run the real Java oracle and compare
against test/golden/cli/<name> {out,exit} (the .err files exist in the
corpus but section 4.4 says stderr is never compared).  The other cases
reuse an existing golden or check conditions (exit codes, pipe behaviour,
temp-folder effects).  A case with no handler is a programmer error, never
a silent green.
"""

import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import unittest

# the three entry points; run with this interpreter
CMD = {
    "callplot": "bin/callplot.py",
    "plottable": "bin/plottable.py",
    "prep": "bin/callplot-prep.py",
}

# the 8 cases whose bytes the Java oracle pinned in chunk W0
GOLDEN_CASES = ["help_after_file", "missing_file", "mode_switch",
                "multi_graffle_ids", "multi_stagger", "no_args",
                "stdin", "vxml"]

FIXTURES = os.path.join("test", "fixtures")
GOLDEN = os.path.join("test", "golden")
CLI = os.path.join("test", "cli")


def _map_arg(a):
    """Bare fixture names become their paths (absolute: some cases run in a
    temp folder); literal paths pass through; a missing name stays missing."""
    if a == "-" or a.startswith("-"):
        return a
    fix = os.path.join(FIXTURES, a)
    if os.path.exists(fix):
        return os.path.abspath(fix)
    if os.path.exists(a):
        return os.path.abspath(a)
    return a  # missing_file case: the name must stay missing


def _run(cmd, args, stdin=None, cwd=None):
    """spawnSync equivalent: run the entry point with this interpreter."""
    return subprocess.run(
        [sys.executable, os.path.abspath(CMD[cmd])] +
        [_map_arg(a) for a in args],
        input=(open(os.path.join(FIXTURES, stdin), "rb").read()
               if stdin else b""),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=cwd, encoding=None)


def _goldenStdout(name):
    return os.path.join(GOLDEN, name + ".out")


def _diff(label, want, got):
    w = want.decode("utf-8", "replace").splitlines(True)
    g = got.decode("utf-8", "replace").splitlines(True)
    body = "".join(difflib.unified_diff(g, w, fromfile="port " + label,
                                        tofile="oracle " + label))
    return label + ": stdout bytes differ\n" + body


def _golden_check(name, cfg):
    def check(self):
        r = _run(cfg.get("cmd", "callplot"), cfg["args"], cfg.get("stdin"))
        want = open(os.path.join(GOLDEN, "cli", name + ".out"), "rb").read()
        if r.stdout != want:
            raise self.fail(_diff(name, want, r.stdout))
        wantExit = open(os.path.join(GOLDEN, "cli", name + ".exit"),
                        encoding="utf-8").read().strip()
        if r.returncode != int(wantExit):
            raise self.fail("exit code %d vs wanted %s"
                            % (r.returncode, wantExit))
    return check


def _cond_check(name, cfg):
    """the W17 cases: reuse a golden or check conditions."""
    def check(self):
        cmd = cfg.get("cmd", "callplot")
        args = cfg["args"]
        stdin = cfg.get("stdin")
        if name == "table_default":
            r = _run(cmd, args, stdin)
            want = open(_goldenStdout("s_fred_annot.table-archtable"), "rb").read()
            if r.stdout != want:
                raise self.fail(_diff("table_default", want, r.stdout))
            if r.returncode != 0:
                raise self.fail("exit code %d vs wanted 0" % r.returncode)
        elif name == "table_bad_style":
            r = _run(cmd, args, stdin)
            if r.returncode != 1:
                raise self.fail("exit code %d vs wanted 1" % r.returncode)
            if r.stdout != b"":
                raise self.fail("stdout must be empty")
        elif name == "html_bad_layout_file":
            r = _run(cmd, args, stdin)
            if r.returncode != 1:
                raise self.fail("exit code %d vs wanted 1" % r.returncode)
            if r.stdout != b"":
                raise self.fail("stdout must be empty (page throws "
                                "before any byte)")
        elif name == "html_flag_wins":
            r = _run(cmd, args, stdin)
            if r.returncode != 0:
                raise self.fail("exit code %d vs wanted 0" % r.returncode)
            html = r.stdout.decode("utf-8")
            if 'id="lay-sbs" class="cpf-radio" checked' not in html:
                raise self.fail("sidebyside radio must start checked")
            if 'id="lay-tb" class="cpf-radio" checked' in html:
                raise self.fail("topbottom radio must not start checked")
        elif name == "plottable_usage":
            r = _run(cmd, args, stdin)
            want = open(os.path.join(CLI, "plottable_usage.expected"), "rb").read()
            if r.stdout != want:
                raise self.fail(_diff("plottable_usage", want, r.stdout))
            if r.returncode != 1:
                raise self.fail("exit code %d vs wanted 1" % r.returncode)
        elif name == "plottable_debug":
            # run in a temporary folder: the script writes _x_<pid>.xml there
            dir = tempfile.mkdtemp(prefix="plottable-")
            try:
                r = _run(cmd, args, stdin, cwd=dir)
                if r.returncode != 0:
                    raise self.fail("exit code %d vs wanted 0" % r.returncode)
                want = open(_goldenStdout("s_sip_annot.table-htmltable3"),
                            "rb").read()
                if r.stdout != want:
                    raise self.fail(_diff("plottable_debug stdout", want,
                                          r.stdout))
                xfiles = [n for n in os.listdir(dir)
                          if re.match(r"^_x_\d+\.xml$", n)]
                if len(xfiles) != 1:
                    raise self.fail("exactly one _x_<pid>.xml expected, got %d"
                                    % len(xfiles))
                want = open(_goldenStdout("s_sip_annot.xml"), "rb").read()
                got = open(os.path.join(dir, xfiles[0]), "rb").read()
                if got != want:
                    raise self.fail(_diff("plottable_debug xml", want, got))
                if b"retaining xml intermediate file in _x_" not in r.stderr:
                    raise self.fail("stderr must have the retaining line")
            finally:
                shutil.rmtree(dir, ignore_errors=True)
        elif name == "prep_stdin":
            dir = tempfile.mkdtemp(prefix="prep-")
            try:
                r = _run(cmd, args, stdin, cwd=dir)
                want = open(_goldenStdout("trace_sip.prep"), "rb").read()
                if r.stdout != want:
                    raise self.fail(_diff("prep_stdin", want, r.stdout))
                if r.returncode != 0:
                    raise self.fail("exit code %d vs wanted 0" % r.returncode)
                if "debug" in os.listdir(dir):
                    raise self.fail("no debug file must be made "
                                    "(section 3.14.4)")
            finally:
                shutil.rmtree(dir, ignore_errors=True)
        elif name == "epipe":
            # the reader hangs up the pipe after one line; PIPESTATUS[0] is
            # the port's own exit code
            fix = _map_arg(args[0])
            script = ("%s %s %s | head -n 1; exit ${PIPESTATUS[0]}" %
                      (sys.executable, os.path.abspath(CMD[cmd]), fix))
            r = subprocess.run(["/bin/bash", "-c", script],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, encoding=None)
            if r.returncode != 0:
                raise self.fail("exit code %d vs wanted 0" % r.returncode)
            if r.stderr != b"":
                raise self.fail("stderr must be empty (no stack trace escaped)")
        else:
            raise self.fail("cli case %s has no handler in the runner"
                            % name)
    return check


class Cli(unittest.TestCase):
    """Populated at import time, one method per test/cli/*.json case."""


def _install_cases():
    for jsonfile in sorted(os.listdir(CLI)):
        if not jsonfile.endswith(".json"):
            continue
        name = jsonfile[:-len(".json")]
        cfg = json.load(open(os.path.join(CLI, jsonfile), encoding="utf-8"))
        check = (_golden_check(name, cfg) if name in GOLDEN_CASES
                 else _cond_check(name, cfg))
        method = "test_cli_" + re.sub(r"[^a-z0-9]+", "_", name).lower()
        setattr(Cli, method, check)


_install_cases()
