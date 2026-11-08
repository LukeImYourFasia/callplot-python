"""Harness task dispatcher (DESIGN.md 4.5.1 and 5.3.1 W19e).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Starts a pool of OracleClients (one harness process each) and hands tasks
to them.  A task with no RESULT in timeoutSec kills that client with SIGKILL,
records exit code 124 for the case, and continues in a new harness process
(4.5.1: timeouts belong to the fuzz runner, not to the harness).  A harness
that died mid-run (bad arguments, harness error) records the same code with
the reason and starts a fresh process for the rest.
"""

import queue
import threading

from client import ClientError, OracleClient


def runHarnessTasks(classDir, mainClass, tasks, clients=8, timeoutSec=5.0):
    """Run all tasks through the pool; returns {key: result}.

    Each task is {"key": str, "flag": str, "input": bytes}.  Each result is
    {exitCode, stdout} for a normal RESULT, plus timedOut or error on the
    kill/restart paths.
    """
    results = {}
    q = queue.Queue()
    for task in tasks:
        q.put(task)

    def worker():
        client = OracleClient(classDir, mainClass)
        while True:
            try:
                task = q.get_nowait()
            except queue.Empty:
                break
            key, flag, inputBytes = task["key"], task["flag"], task["input"]
            try:
                client.send(key, flag, inputBytes)
                frame = client.awaitId(key, timeoutSec)
                if frame is None:
                    client.kill()
                    results[key] = {"exitCode": 124, "stdout": b"",
                                    "timedOut": True}
                    client = OracleClient(classDir, mainClass)
                    continue
                results[key] = frame
            except ClientError as err:
                # the harness died mid-run or broke protocol: record it and
                # start a fresh process for the remaining tasks
                results[key] = {"exitCode": 124, "stdout": b"",
                                "error": str(err)}
                client = OracleClient(classDir, mainClass)
                continue
        client.close()

    jobs = []
    for _ in range(min(clients, len(tasks))):
        t = threading.Thread(target=worker)
        t.start()
        jobs.append(t)
    for t in jobs:
        t.join()
    return results
