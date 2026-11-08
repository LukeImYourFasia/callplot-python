#!/usr/bin/env python3
"""The syntax gate (DESIGN.md 4.2/4.7): mmdc on every Mermaid snapshot,
java -jar plantuml.jar -checkonly on every PlantUML snapshot.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Empty snapshots are the crashing fixtures' flushed output (never anything
a parser could read): skipped, counted.  Exit 0 means every non-empty
snapshot was accepted.  Only tools/ starts these processes (section 2.6):
exec with argument arrays, never a built shell string.
"""

import os
import subprocess
import sys

MMD_BIN = "node_modules/@mermaid-js/mermaid-cli/src/cli.js"
MMD_CFG = "tools/mmdc-puppeteer.json"  # --no-sandbox: headless fd check only
PLANTUML_JAR = "reference/plantuml.jar"
OUT_DIR = "/tmp/opencode/syntax"
SNAPS = "test/snapshots"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ok = 0
    skipped = 0
    failures = []

    for name in os.listdir(SNAPS):
        fpath = os.path.join(SNAPS, name)
        if name.endswith(".mmd"):
            if os.stat(fpath).st_size == 0:
                skipped += 1
                continue
            outSvg = os.path.join(OUT_DIR, name[:-len(".mmd")] + ".svg")
            r = subprocess.run(["node", MMD_BIN, "-i", fpath, "-o",
                                outSvg, "-p", MMD_CFG],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
            if r.returncode != 0:
                failures.append("SYNTAX FAIL %s mmdc: %s"
                                % (name, r.stderr.decode("utf-8", "replace")
                                   .strip().split("\n")[0]))
            else:
                ok += 1
        elif name.endswith(".puml"):
            if os.stat(fpath).st_size == 0:
                skipped += 1
                continue
            r = subprocess.run(["java", "-jar", PLANTUML_JAR, "-checkonly",
                                fpath],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
            if r.returncode != 0:
                failures.append("SYNTAX FAIL %s plantuml: %s"
                                % (name, r.stderr.decode("utf-8", "replace")
                                   .strip()))
            else:
                ok += 1

    for line in failures:
        print(line)
    print("syntax: %d accepted, %d empty skipped" % (ok, skipped))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
