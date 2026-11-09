"""Trust check for the fuzz harness client (DESIGN-PYTHON.md section 4.6).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the Java harness pool (`tools/oracle_client.py`) and
DESIGN.md section 4.5.1 framing; traps of DESIGN.md 4.5.3.

Before the full fuzz run, the client must agree with the plain java call
of `DESIGN.md` section 4.2 (the JS repo's ``tools/jref.sh``, inline here:
one JVM per run, same ``JAVA_TOOL_OPTIONS``; this repo has no jref script,
DESIGN-PYTHON.md 4.3 row "Oracle scripts"): 300 cases (seed 99) x 7 core
modes through ``oracle_client.run_tasks`` and through a one-JVM-per-run
call of ``com.dynamicsoft.callplot.Main``.  The stdout bytes and the exit
codes must be equal for every run (DESIGN-PYTHON.md 4.6: "Trust check for
the client (before the full run)").  If any run differs, fix the harness
client, never the data (DESIGN.md 4.5.3).

Cases come from ``tools/fuzz.py`` (same generator, same seed), so this
check exercises exactly the inputs the fuzz run will send.  The JVM leg
runs 12 threads; a 30 s wall per JVM only records 124 if the JVM itself
hangs (DESIGN.md 4.5.3: 5 s belongs to the pool).

Run: ``pytest -m fuzz tests/fuzz_client_check.py`` (needs Java 8).
"""

import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from queue import Empty, Queue

import pytest
from paths import REPO_ROOT

# tools/ is not a package; put it on the path the way tools/fuzz.py does
sys.path.insert(0, str(REPO_ROOT / "tools"))
sys.path.insert(0, str(REPO_ROOT / "src"))

import fuzz as fuzz_tool  # the seeded case generator (DESIGN.md 4.5 steps 1-3)
from oracle_client import run_tasks

BUILD_DIR = str(REPO_ROOT / "reference" / "build")
MAIN_CLASS = "com.dynamicsoft.callplot.Main"

# the environment of DESIGN.md 4.2 and 4.5.1: same for both legs, so a
# non-ASCII case cannot differ because of encodings (DESIGN.md 4.5.3 row)
JREF_ENV = dict(os.environ)
JREF_ENV["LC_ALL"] = "en_US.UTF-8"
JREF_ENV["JAVA_TOOL_OPTIONS"] = "-Dfile.encoding=UTF-8"

SEED = 99
COUNT = 300


@pytest.mark.fuzz
def test_fuzz_client_check__seed_99_x_300_cases_x_7_modes__client_equals_java() -> None:
    """Every case x mode: the pool's bytes and exit equal one JVM's."""
    rng = fuzz_tool.random.Random(SEED)
    cases = [fuzz_tool.gen_case(rng) for _ in range(COUNT)]
    tasks = []
    for c, case in enumerate(cases):
        for mode, flag, _bit in fuzz_tool.CORE_MODES:
            tasks.append({"key": f"{c}.{mode}", "flag": flag, "input": case})

    t0 = time.monotonic()
    pool = run_tasks(tasks, workers=8, timeout=5.0)
    pool_secs = time.monotonic() - t0

    # the one-JVM-per-run leg (the JS repo's tools/jref.sh, inline: DESIGN.md
    # 4.2; java -cp reference/build com.dynamicsoft.callplot.Main [flag] file)
    work_dir = tempfile.mkdtemp(prefix="fuzz-client-check-", dir="/tmp/opencode")
    results = {}

    def jref_worker(q: Queue) -> None:
        while True:
            try:
                task, path = q.get_nowait()
            except Empty:
                return
            with open(path, "wb") as fh:
                fh.write(task["input"])
            args = [path] if task["flag"] == "text" else [task["flag"], path]
            cmd = ["java", "-cp", BUILD_DIR, MAIN_CLASS, *args]
            try:
                r = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    env=JREF_ENV,
                    timeout=30,
                )
                results[task["key"]] = (r.returncode, r.stdout)
            except subprocess.TimeoutExpired:
                results[task["key"]] = (124, b"")

    q = Queue()
    for i, task in enumerate(tasks):
        q.put((task, os.path.join(work_dir, f"{i:05d}.in")))
    threads = [threading.Thread(target=jref_worker, args=(q,)) for _ in range(12)]
    t1 = time.monotonic()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    jref_secs = time.monotonic() - t1
    shutil.rmtree(work_dir, ignore_errors=True)

    diffs = []
    for task in tasks:
        key = task["key"]
        j_code, j_out = results.get(key, (-1, b""))
        p_code, p_out = pool.get(key, (124, b""))
        if j_code != p_code:
            diffs.append(f"{key} exit {j_code} vs {p_code}")
        elif j_code == 0 and j_out != p_out:
            diffs.append(f"{key} bytes differ")
    # the client's own framing stays inside the client module
    print(
        f"trust check: {len(tasks)} runs, pool {pool_secs:.1f} s, "
        f"jvm {jref_secs:.1f} s, diffs {len(diffs)}"
    )
    assert not diffs, (
        f"harness client differs from java in {len(diffs)} runs: {'; '.join(diffs[:10])}"
    )
