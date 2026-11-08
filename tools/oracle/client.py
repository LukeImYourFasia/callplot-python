"""Frame client for the fast fuzz oracle harness (DESIGN.md section 4.5.1).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Starts one FuzzOracle JVM, sends CASE frames to its stdin, and reads
RESULT frames from its stdout.  A stdout read can hold part of a frame or
more than one frame, so we keep a byte buffer and take a frame only when
its header line and all <m> bytes are present.  <m> counts BYTES, so all
framing works on bytes, never strings.  Timeouts belong to the pool: it
kills this process with SIGKILL and starts a new one (4.5.1: timeouts are
the fuzz runner's, not the harness's).  Stderr is log only, never protocol
data: it goes to a temp file so the JVM can never block on a full pipe.

Frames: request "CASE <id> <modeFlag> <n>\\n" then n bytes; response
"RESULT <id> <exitCode> <m>\\n" then m bytes (tools/oracle/FuzzOracle.java).
"""

import os
import re
import select
import signal
import subprocess
import tempfile
import time

MODE_FLAGS = frozenset(["text", "-pic", "-xml", "-svg", "-vml", "-vxml",
                        "-graffle"])

RESULT_RE = re.compile(rb"^RESULT (\S+) (-?\d+) (\d+)$")


class ClientError(Exception):
    """the harness died mid-run or broke protocol; the pool starts a new one"""


class OracleClient:
    """One frame client.  Each instance owns exactly one harness process."""

    def __init__(self, classDir, mainClass):
        # classDir: folder of .class files the harness loads per case with a
        # fresh URLClassLoader (statics start fresh, section 3.6).  Never put
        # reference/build on -cp (4.5.3): the harness classes live there.
        env = dict(os.environ)
        env["JAVA_TOOL_OPTIONS"] = "-Dfile.encoding=UTF-8"
        self.logFile = tempfile.NamedTemporaryFile(
            prefix="oracle-stderr-", delete=False)
        self.proc = subprocess.Popen(
            ["java", "-cp", "reference/build-tools", "FuzzOracle",
             classDir, mainClass],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.logFile, env=env)
        self.inFd = self.proc.stdin.fileno()
        self.outFd = self.proc.stdout.fileno()
        self.pending = set()
        self.resolved = {}
        self.buf = b""
        self.alive = True
        self.closed = False
        self.protocolError = None
        self.ended = None
        self.logPos = 0

    def send(self, caseId, modeFlag, inputBytes):
        """Send one CASE frame; the RESULT comes back from awaitId."""
        if modeFlag not in MODE_FLAGS:
            raise ValueError("unknown mode flag: " + modeFlag)
        if not isinstance(inputBytes, bytes):
            raise ValueError("input must be bytes")
        if self.closed or not self.alive:
            raise ClientError("client is no longer usable: " + self.describe())
        key = str(caseId)
        if key in self.pending or key in self.resolved:
            raise ClientError("duplicate case id: " + key)
        header = ("CASE %s %s %d\n" % (key, modeFlag, len(inputBytes))
                  ).encode("ascii")
        self.pending.add(key)
        try:
            self._writeAll(header)
            if len(inputBytes) > 0:
                self._writeAll(inputBytes)
        except OSError:
            # EPIPE after the process dies: the exit path reports the loss
            # (JS client.js: child.stdin.on("error") is a no-op too)
            pass

    def awaitId(self, caseId, timeoutSec):
        """Wait for one RESULT.  Returns {id, exitCode, stdout}; None on
        timeout (the pool kills and records 124).  Raises ClientError when
        the harness died mid-run or broke protocol."""
        key = str(caseId)
        deadline = time.monotonic() + timeoutSec
        while True:
            if key in self.resolved:
                return self.resolved.pop(key)
            if self.protocolError is not None:
                raise ClientError("harness protocol break: " + str(
                    self.protocolError))
            if self.ended is not None:
                self.pending.discard(key)
                raise ClientError("no RESULT, harness ended: " +
                                  self.describe())
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            ready, _, _ = select.select([self.outFd], [], [], remaining)
            if not ready:
                continue  # spurious; the deadline ends the loop
            try:
                chunk = os.read(self.outFd, 65536)
            except OSError:
                chunk = b""
            if chunk == b"":  # stdout EOF: the harness process has ended
                self.onExit(self.proc.wait())
                continue
            self._consume(chunk)

    def close(self):
        """Close stdin: the harness exits 0 once its buffered frames are done."""
        self.closed = True
        try:
            self.proc.stdin.close()
        except OSError:
            pass
        self.onExit(self.proc.wait())
        return self.ended

    def kill(self):
        """SIGKILL the harness (the fuzz timeout path, 4.5.1)."""
        self.closed = True
        try:
            os.kill(self.proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # already gone
        self.onExit(self.proc.wait())
        return self.ended

    def breakProtocol(self, why):
        """Malformed or unknown RESULT: harness bug, stop the process."""
        self.protocolError = why
        try:
            os.kill(self.proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    def describe(self):
        if self.protocolError is not None:
            return ("protocol break: %s; stderr: %s"
                    % (self.protocolError, self.stderrText()))
        code = self.ended
        if code is None:
            return "still running"
        how = ("harness exit code %d" % code if code >= 0
               else "killed by signal %d" % -code)
        return "%s; stderr: %s" % (how, self.stderrText())

    def onExit(self, code):
        """The harness process ended: record it (pending frames now fail)."""
        self.alive = False
        self.ended = code

    def _writeAll(self, data):
        off = 0
        while off < len(data):
            off += os.write(self.inFd, data[off:])

    def stderrText(self):
        self.logFile.flush()
        try:
            with open(self.logFile.name, "rb") as fh:
                return fh.read().decode("utf-8", "replace")
        except OSError:
            return ""

    def _consume(self, chunk):
        """Consume one stdout chunk: append, then take whole frames only."""
        if chunk == b"":
            return
        self.buf += chunk
        while True:
            nl = self.buf.find(b"\n")
            if nl < 0:
                return  # no header line yet
            header = self.buf[:nl]
            m = RESULT_RE.match(header)
            if m is None:
                self.breakProtocol(
                    "bad RESULT header: %s" % header.decode("ascii", "replace"))
                return
            frameEnd = nl + 1 + int(m.group(3))
            if len(self.buf) < frameEnd:
                return  # header here, body not complete yet
            key = m.group(1).decode("ascii")
            if key not in self.pending:
                self.breakProtocol("unexpected RESULT id: " + key)
                return
            stdout = self.buf[nl + 1:frameEnd]
            self.buf = self.buf[frameEnd:]
            self.pending.discard(key)
            self.resolved[key] = {"id": key,
                                  "exitCode": int(m.group(2)),
                                  "stdout": stdout}
