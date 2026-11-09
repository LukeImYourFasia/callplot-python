#!/usr/bin/env python3
"""Harness client for the Python fuzz runner (DESIGN-PYTHON.md section 4.6
rule 3; protocol of DESIGN.md section 4.5.1; traps of DESIGN.md 4.5.3).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Starts one provided FuzzOracle JVM (never edit it, DESIGN.md 4.5.1: the
harness is a provided file), sends CASE frames to its stdin and reads
RESULT frames from its stdout.  All framing knowledge lives in this
module: the frames are BYTES, because <m> counts bytes (DESIGN.md 4.5.1).
Request "CASE <id> <modeFlag> <n>\n" then n bytes; response "RESULT <id>
<exitCode> <m>\n" then m bytes (tools/oracle/FuzzOracle.java).  stderr is
log only, never protocol data: it goes to a temp file that close()
deletes, so the JVM never blocks on a full pipe and never prints
"Picked up JAVA_TOOL_OPTIONS" into the data (DESIGN.md 4.5.3).  Timeout
belongs to the runner, not to the harness: threading.Timer(timeout,
process.kill) starts per case; when it fires, await_result returns None,
this client becomes unusable, and the caller starts a new one (DESIGN-
PYTHON.md 4.6 rule 3, DESIGN.md 5.3.1 W19e).  One client per worker
thread, never shared between threads.
"""

import contextlib
import os
import queue
import subprocess
import tempfile
import threading
from concurrent import futures  # 4.6 rule 4: ThreadPoolExecutor(max_workers=8)

MODE_FLAGS = frozenset(
    ["text", "-pic", "-xml", "-svg", "-vml", "-vxml", "-graffle"]
)  # DESIGN.md 4.5.1 request line


class ClientError(Exception):
    """the harness died mid-run or broke protocol; the caller starts a new one"""


class OracleClient:
    """One frame client.  Each instance owns exactly one harness process."""

    def __init__(
        self,
        build_dir="reference/build",
        main_class="com.dynamicsoft.callplot.Main",
        class_dir="reference/build-tools",
    ):
        # build_dir: folder of callplot .class files the harness loads per
        # case through a fresh URLClassLoader, so the statics of DESIGN.md
        # 3.6 start fresh (never put build_dir on -cp, DESIGN.md 4.5.3).
        # class_dir: only the harness classes (DESIGN.md 4.5.1 command).
        env = dict(os.environ)
        env["JAVA_TOOL_OPTIONS"] = "-Dfile.encoding=UTF-8"

        #        closing it right away (with) would break the frame contract.
        self.log = tempfile.NamedTemporaryFile(  # noqa: SIM115
            prefix="oracle-stderr-", delete=False
        )
        self.proc = subprocess.Popen(
            ["java", "-cp", class_dir, "FuzzOracle", build_dir, main_class],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.log,
            env=env,
        )
        self.pending = set()
        self.usable = True
        self.awaiting = False
        self.timed_out = False

    def send(self, case_id, flag, data):
        """Send one CASE frame: "CASE <id> <flag> <n>\n" then n bytes, flush.

        Raises ClientError when the process is gone (EPIPE) or the frame
        would break the framing (DESIGN.md 4.5.1 request line).
        """
        if not self.usable:
            raise ClientError("client is no longer usable: " + self.describe())
        if flag not in MODE_FLAGS:
            raise ValueError("unknown mode flag: " + flag)
        if not isinstance(data, bytes):
            raise ValueError("input must be bytes")
        key = str(case_id)
        if " " in key or "\n" in key or not key:
            raise ValueError("bad case id: " + key)
        if key in self.pending:
            raise ClientError("duplicate case id: " + key)
        header = f"CASE {key} {flag} {len(data)}\n".encode("ascii")
        try:
            self.proc.stdin.write(header)
            if len(data) > 0:
                self.proc.stdin.write(data)
            self.proc.stdin.flush()
        except OSError:
            # the harness died: reading its stdout now hits EOF, and await
            # reports it (DESIGN.md 4.5.1: the harness exits on its own)
            pass
        self.pending.add(key)

    def await_result(self, case_id, timeout=5.0):
        """Wait for one RESULT.  Returns (id, exitCode, stdoutBytes); None
        on timeout (the timer killed the JVM: record 124 and start a new
        client, DESIGN-PYTHON.md 4.6 rule 3).  Raises ClientError when the
        harness died mid-run or broke framing.

        readline() gives the header line; then read EXACTLY m bytes.
        BufferedReader.read(m) returns fewer bytes only at end of file, so
        a short read means the process died inside the frame body (DESIGN-
        PYTHON.md 4.6 rule 3: check the length).
        """
        if not self.usable:
            raise ClientError("client is no longer usable: " + self.describe())
        key = str(case_id)
        if key not in self.pending:
            raise ClientError("no pending frame for id: " + key)
        timer = threading.Timer(timeout, self._on_timeout)
        self.awaiting = True
        timer.start()
        try:
            line = self.proc.stdout.readline()
        except (EOFError, OSError, ValueError):
            line = b""
        self.awaiting = False
        timer.cancel()
        if self.timed_out:
            self.usable = False
            return None
        if line == b"" and self.proc.poll() is not None:
            self.usable = False
            raise ClientError("no RESULT, harness ended: " + self.describe())
        if line == b"":
            self.usable = False
            raise ClientError("no RESULT, harness ended (still running?)")
        parts = line.rstrip(b"\n").split(b" ")
        if len(parts) != 4 or parts[0] != b"RESULT" or parts[1].decode("ascii", "replace") != key:
            self.usable = False
            raise ClientError(f"bad RESULT header: {line!r}") from None
        try:
            code = int(parts[2])
            m = int(parts[3])
        except ValueError:
            self.usable = False
            raise ClientError(f"bad RESULT header: {line!r}") from None
        try:
            body = self.proc.stdout.read(m)
        except (EOFError, OSError, ValueError):
            body = b""
        if self.timed_out:
            # killed inside the body read: same timeout path (4.6 rule 3)
            self.usable = False
            return None
        if len(body) != m:
            self.usable = False
            raise ClientError(f"short RESULT body: {len(body)} of {m} bytes: {self.describe()}")
        self.pending.discard(key)
        return key, code, body

    def _on_timeout(self):
        """Timer fired for a case in flight: SIGKILL the JVM (4.5.1)."""
        if not self.awaiting or not self.usable:
            return  # the case already resolved: never kill a live client
        self.timed_out = True
        with contextlib.suppress(ProcessLookupError):
            self.proc.kill()  # already gone

    def close(self):
        """Close stdin: the harness exits 0 once its buffered frames are
        done (DESIGN.md 4.5.1).  Closes stdout, then the temp stderr file,
        and deletes that temp file (the path is reported nowhere).
        """
        self.usable = False
        with contextlib.suppress(OSError, ValueError):
            self.proc.stdin.close()
        with contextlib.suppress(OSError, ValueError):
            self.proc.stdout.close()
        with contextlib.suppress(OSError, ValueError, KeyboardInterrupt):
            self.proc.wait()
        try:
            self.log.close()
            os.unlink(self.log.name)
        except OSError:
            pass

    def describe(self):
        """Why the harness process ended: exit 2 = bad arguments, 3 =
        harness error with an "FuzzOracle:" message on stderr (4.5.1/4.5.3).
        Reports the stderr LOG TEXT, never the temp file path.
        """
        code = self.proc.poll()
        if code is None:
            how = "still running"
        elif code < 0:
            how = f"killed by signal {-code}"
        else:
            how = f"harness exit code {code}"
        try:
            with open(self.log.name, "rb") as fh:
                text = fh.read().decode("utf-8", "replace")
        except OSError:
            text = ""
        return f"{how}; stderr: {text}"


def run_tasks(tasks, workers=8, timeout=5.0):
    """Run all harness tasks; returns {key: (exitCode, stdoutBytes)}.

    Each task is {"key": str, "flag": str, "input": bytes}.  A case with
    no RESULT in timeout seconds kills its client and records exit code
    124 with empty stdout, then a fresh client continues (DESIGN-PYTHON.md
    4.6 rule 3; DESIGN.md 5.3.1 W19e).  One OracleClient per worker
    thread, never shared between threads (4.6 rule 3).
    """
    results = {}
    q = queue.Queue()
    for task in tasks:
        q.put(task)
    workers = min(workers, q.qsize())
    if workers <= 0:
        return results

    def worker():
        client = OracleClient()
        while True:
            try:
                task = q.get_nowait()
            except queue.Empty:
                break
            key, flag, data = task["key"], task["flag"], task["input"]
            try:
                client.send(key, flag, data)
                got = client.await_result(key, timeout)
                if got is None:
                    client.close()  # kills already happened: reap and clean
                    results[key] = (124, b"")
                    client = OracleClient()
                    continue
                results[key] = (got[1], got[2])
            except ClientError:
                # the harness died mid-run or broke protocol: record it and
                # start a fresh process for the remaining tasks (4.5.3)
                client.close()
                results[key] = (124, b"")
                client = OracleClient()
                continue
        client.close()

    def guarded():
        try:
            worker()
        except BaseException as err:
            # a worker crash must never pass silently: missing harness
            # results would otherwise hide themselves (4.5.3 trust rule)
            raise ClientError(f"worker died: {err!r}") from err

    with futures.ThreadPoolExecutor(max_workers=workers) as pool:
        done = [pool.submit(guarded) for _ in range(workers)]
        errs = [fut.exception() for fut in done]
    bad = [e for e in errs if isinstance(e, BaseException)]
    if bad:
        raise bad[0]
    return results
