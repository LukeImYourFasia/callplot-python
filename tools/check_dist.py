#!/usr/bin/env python3
"""Wheel contents check (DESIGN-PYTHON.md section 3.1 rule 5).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Opens the newest wheel in dist/ with zipfile, lists its entries, and
fails when any entry lies outside callplot/ and callplot_py-*.dist-info/
(DESIGN-PYTHON.md section 3.1 rule 5: the wheel must hold only the
package and its metadata).  Prints the entry list and a summary.

Usage: tools/check_dist.py [path-to-whl]
Exit: 0 when every entry is allowed, 1 otherwise (or when no wheel exists).
"""

import fnmatch
import glob
import os
import sys
import zipfile


def allowed(name):
    """True when the entry sits in callplot/ or callplot_py-*.dist-info/.
    The metadata folder replaces "-" with "_" in the project name
    (callplot-py -> callplot_py-<version>.dist-info)."""
    if name.startswith("callplot/"):
        return True
    return fnmatch.fnmatch(name, "callplot_py-*.dist-info/*")


def main():
    argv = sys.argv[1:]
    if argv:
        path = argv[0]
    else:
        whls = glob.glob("dist/*.whl")
        if not whls:
            print("check_dist: no wheel found in dist/ (run python3 -m build first)")
            return 1
        path = max(whls, key=os.path.getmtime)  # the newest wheel
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
    except (OSError, zipfile.BadZipFile) as err:
        print(f"check_dist: cannot open wheel: {err}")
        return 1

    bad = []
    for name in names:
        print(f"{path}: {name}")
        if not allowed(name):
            bad.append(name)
    if bad:
        print(
            f"check_dist: FAIL, {len(bad)} of {len(names)} entries outside "
            "callplot/ and callplot_py-*.dist-info/:"
        )
        for name in bad:
            print(f"  {name}")
        return 1
    print(
        f"check_dist: ok, {len(names)} entries in {path}, all inside callplot/ "
        "and callplot_py-*.dist-info/"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
