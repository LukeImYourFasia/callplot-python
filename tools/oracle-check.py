#!/usr/bin/env python3
"""Trust check for the harness (DESIGN.md 4.5.1, 4.5.2; use before fuzzing).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Two stages, in order:

1. Probe checks (4.5.2): every row of the probe table run through the
   frame client, plus W19a's 1,000 FileProbe frames (sizes 0, 1, 8,191,
   8,192, 8,193 and 100,000 bytes, non-ASCII, and inputs holding the text
   RESULT).  A failing probe means the harness is not trustworthy: stop.

2. Trust check: 300 fuzz cases (seed 99) x 7 core modes through BOTH the
   harness pool and one-JVM-per-run java.  Stdout bytes and exit codes
   must be equal for every run; when java exits non-zero, only the exit
   code is compared (4.5 rule 5).  Records the run time of each path.

Usage: tools/oracle-check.py [--seed 99] [--count 300]
Exit: 0 when everything passed, 1 otherwise (4.5.1 stop rule: a failing
trust check means: do not use the harness).
"""

import os
import queue
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.join("tools", "oracle"))

from cases import genCases  # noqa: E402 - same directory
from client import ClientError, OracleClient
from pool import runHarnessTasks

MODES = [("text", "text"), ("pic", "-pic"), ("xml", "-xml"),
         ("svg", "-svg"), ("vml", "-vml"), ("vxml", "-vxml"),
         ("graffle", "-graffle")]

# the java leg mirrors the JS repo's tools/jref.sh inline (this repo has
# no jref script): one JVM per run, same JAVA_TOOL_OPTIONS as the harness
JREF_ENV = dict(os.environ)
JREF_ENV["LC_ALL"] = "en_US.UTF-8"
JREF_ENV["JAVA_TOOL_OPTIONS"] = "-Dfile.encoding=UTF-8"

PROBES_DIR = "reference/build-probes"
BUILD_DIR = "reference/build"
MAIN_CLASS = "com.dynamicsoft.callplot.Main"

failures = []


def expect(label, got, wantExit, wantOut):
    """One probe-table comparison: exit code and stdout bytes."""
    if got is None:
        failures.append("%s: timeout (exit 124 wanted %d)" % (label, wantExit))
        return
    if got["exitCode"] != wantExit:
        failures.append("%s: exit %d vs wanted %d"
                        % (label, got["exitCode"], wantExit))
        return
    if wantOut is not None and got["stdout"] != wantOut:
        failures.append("%s: stdout %r vs wanted %r"
                        % (label, got["stdout"], wantOut))


def oneProbe(mainClass, caseId, inputBytes, timeoutSec=5.0):
    """Run one case through a fresh harness for the probe class."""
    client = OracleClient(PROBES_DIR, mainClass)
    client.send(caseId, "text", inputBytes)
    got = client.awaitId(caseId, timeoutSec)
    if got is None:
        client.kill()
    else:
        client.close()
    return got


def probeChecks():
    # ExitProbe: empty input -> exit 7, stdout "hi\n"; no "e" (stderr dropped)
    expect("ExitProbe", oneProbe("ExitProbe", "1", b""), 7, b"hi\n")

    # ReturnProbe: a normal return gives 0
    expect("ReturnProbe", oneProbe("ReturnProbe", "1", b""), 0, b"ok\n")

    # ThrowProbe: an exception gives 1, output kept before the throw
    expect("ThrowProbe", oneProbe("ThrowProbe", "1", b""), 1, b"a")

    # StaticProbe sent 3 times to one harness process: statics reset per
    # case, so every run prints "1\n"
    client = OracleClient(PROBES_DIR, "StaticProbe")
    client.send("1", "text", b"")
    client.send("2", "text", b"")
    client.send("3", "text", b"")
    for caseId in ("1", "2", "3"):
        expect("StaticProbe #%s" % caseId,
               client.awaitId(caseId, 5.0), 0, b"1\n")
    client.close()

    # FileProbe: non-ASCII and a long run of bytes round-trip through the
    # harness temp file and the byte framing
    fileIn = "\u00e9/\n".encode("utf-8") + b"x" * 10000
    expect("FileProbe", oneProbe("FileProbe", "1", fileIn), 0, fileIn)

    # LoopProbe: no RESULT in 5 s -> SIGKILL, exit 124, none on stdout
    got = oneProbe("LoopProbe", "1", b"", 5.0)
    if got is not None:
        failures.append("LoopProbe: expected a timeout (124), got exit %s"
                        % got["exitCode"])
    # and after the kill, the NEXT case still works in a new process
    expect("LoopProbe next case", oneProbe("ReturnProbe", "1", b""), 0,
           b"ok\n")

    # W19a: the framing through FileProbe with awkward sizes and bytes
    sizes = [0, 1, 8191, 8192, 8193, 100000]
    rng = random.Random(7)
    client = OracleClient(PROBES_DIR, "FileProbe")
    badFrames = 0
    for i in range(1000):
        n = sizes[i % len(sizes)]
        body = bytearray(rng.randrange(256) for _ in range(n))
        if n >= 16:  # inputs holding the text RESULT must round-trip too
            at = rng.randrange(n - 16)
            body[at:at + 16] = b"RESULT 9 text 3\n"
        if i % 53 == 0:  # non-ASCII runs
            body = bytearray(b"\xc3\xa9\xc3\xa8") + body
        client.send(str(i), "text", bytes(body))
        got = client.awaitId(str(i), 10.0)
        if got is None or got["exitCode"] != 0 or got["stdout"] != bytes(body):
            badFrames += 1
    client.close()
    if badFrames > 0:
        failures.append("FileProbe framing: %d/1000 frames wrong" % badFrames)


def trustCheck(seed, count):
    """300 cases x 7 modes, harness pool vs one-JVM-per-run java."""
    print("trust check: seed %d, cases %d, modes %d" % (seed, count, len(MODES)))
    cases = genCases(seed, count)
    tasks = []
    for c, case in enumerate(cases):
        for mode, flag in MODES:
            tasks.append({"key": "%d.%s" % (c, mode), "flag": flag,
                          "input": case})

    t0 = time.monotonic()
    harnessResults = runHarnessTasks(BUILD_DIR, MAIN_CLASS, tasks,
                                     clients=8, timeoutSec=5.0)
    harnessSec = time.monotonic() - t0

    # --- one JVM per run (the JS repo's tools/jref.sh, inline here) ---
    tmpDir = tempfile.mkdtemp(prefix="oracle-check-", dir="/tmp/opencode")
    jrefResults = {}

    def jrefWorker(q):
        while True:
            try:
                task, path = q.get_nowait()
            except Exception:
                return
            with open(path, "wb") as fh:
                fh.write(task["input"])
            args = [path] if task["flag"] == "text" else [task["flag"], path]
            cmd = ["java", "-cp", BUILD_DIR, MAIN_CLASS] + args
            try:
                r = subprocess.run(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL,
                                   env=JREF_ENV, timeout=30)
                code = r.returncode if r.returncode >= 0 else 124
                out = r.stdout
            except subprocess.TimeoutExpired as err:
                # 30 s: SIGKILLed; the pool's 5 s kill records 124 too
                code = 124
                out = err.stdout if err.stdout is not None else b""
            jrefResults[task["key"]] = (code, out)

    q = queue.Queue()
    for i, task in enumerate(tasks):
        q.put((task, os.path.join(tmpDir, "%05d.in" % i)))
    threads = [threading.Thread(target=jrefWorker, args=(q,))
               for _ in range(12)]
    t1 = time.monotonic()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    shutil.rmtree(tmpDir, ignore_errors=True)
    jrefSec = time.monotonic() - t1

    # --- compare ---
    diffs = 0
    shown = []
    for task in tasks:
        key = task["key"]
        h = harnessResults.get(key)
        if h is None:
            h = {"exitCode": 124}
        jCode, jOut = jrefResults.get(key, (-1, b""))
        hOut = h.get("stdout", b"")
        ok = jCode == h["exitCode"]
        if ok and h["exitCode"] == 0 and jCode == 0:
            ok = jOut == hOut
        if not ok:
            diffs += 1
            if len(shown) < 20:
                shown.append(key)
    print("runs: %d" % len(tasks))
    print("harness path: %.1f s" % harnessSec)
    print("jref path: %.1f s (%.0f ms/run)"
          % (jrefSec, jrefSec / len(tasks) * 1000))
    print("diffs: %d%s" % (diffs,
                           (" first: " + ", ".join(shown)) if shown else ""))
    if diffs > 0:
        print("TRUST CHECK FAIL - do not use the harness (4.5.1)")
    else:
        print("TRUST CHECK PASS")
    return diffs


def argNum(name, argv, dflt):
    i = argv.index(name) if name in argv else -1
    if i < 0 or i + 1 >= len(argv):
        return dflt
    try:
        return int(argv[i + 1])
    except ValueError:
        return dflt


PROBE_UNITS = 10  # 6 table rows + StaticProbe's 3 sends + the framing row


def main():
    argv = sys.argv[1:]
    seed = argNum("--seed", argv, 99)
    count = argNum("--count", argv, 300)
    if not os.path.exists("reference/build-tools/FuzzOracle.class"):
        print("harness not compiled: run the javac lines in "
              "tools/oracle/README.md first")
        return 1

    probeChecks()
    probeFails = len(failures)
    print("probes: pass %d / fail %d" % (PROBE_UNITS - probeFails, probeFails))
    for why in failures:
        print("  probe fail: " + why)
    if probeFails > 0:
        print("PROBE CHECK FAIL - the harness is untrustworthy (4.5.2)")
        return 1
    diffs = trustCheck(seed, count)
    if diffs > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
