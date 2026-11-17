#!/usr/bin/env python3
"""Screenshots for the README "Sample output" section (docs/images/*.png).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Renders the widest tool diagram (docs/diagrams/api.msd, DESIGN.md section
2.7.3) headless with the repo's puppeteer (from node_modules, which is not
committed).  The HTML is generated on the spot through this port's own API
(``callplot.api.render``), so the pictures always show what the tool draws
now; no committed page is read and no command is shelled out (DESIGN-PYTHON.md
section 3.7: the library call is the honest way for a tool of this repo).
Notes carried from the JS tool:

 - sidebyside needs the viewport 1100 px or wider: the stylesheet switches
   layouts inside @container cpf (min-width:1100px), so a narrower window
   stacks the panes (what a browser does at that width too).
 - wordtable re-wraps the page in the capture harness only: the legacy Word
   XML head makes Chrome move the body into <head>, so the body region is
   fed to a blank document here; only the capture works around Chrome's
   parser.

Implementation: the capture itself runs in Node (puppeteer lives in
node_modules), driven as a module -e from the repo root so the bare
"puppeteer" import resolves into the repo's node_modules; this tool starts
it and reports.
"""

import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.abspath("src"))

from callplot.api import render
from callplot.constants import Mode
from callplot.options import HtmlLayout, RenderOptions, parse_table_style

PADS = 10  # whitespace trimmed around the content box
SCALE = 2  # device pixels per CSS pixel: crisp small type

MSD = "docs/diagrams/api.msd"

# [mode, options, destination, viewport width, viewport height]
TABLE_STYLES = ("archtable", "htmltable", "htmltable2", "htmltable3", "nolinks", "wordtable")

SHOTS = [
    (Mode.TABLE, parse_table_style(style), f"docs/images/api-table-{style}.png", 1600, 900)
    for style in TABLE_STYLES
] + [
    (Mode.HTML, None, "docs/images/api-html-topbottom.png", 1500, 1200),
    (Mode.HTML, HtmlLayout.SIDEBYSIDE, "docs/images/api-html-sidebyside.png", 1500, 1000),
]


def render_html(mode, table_style, html_layout):
    """One page through the API (DESIGN-PYTHON.md section 3.7: a string out)."""
    with open(MSD, encoding="utf-8") as fh:
        text = fh.read()
    options = RenderOptions()
    if table_style is not None:
        options = options._replace(table_style=table_style)
    if mode is Mode.HTML and html_layout is not None:
        # -html=sidebyside forces the layout (DESIGN.md 3.12.6 rule)
        options = options._replace(html_layout=html_layout)
    return render(text, mode, options=options)


def staged_shots():
    """HTML for each shot, written to a temp file the Node harness reads."""
    js_shots = []
    tmps = []
    try:
        for mode, opt, dst, width, height in SHOTS:
            if mode is Mode.TABLE:
                html = render_html(mode, opt, None)
            else:
                html = render_html(mode, None, opt)
            if "wordtable" in dst:
                # harness-only rewrap: body region of the Word page fed to a
                # blank document, so Chrome keeps the body
                from_ = html.find("<body")
                to = html.find("</body>")
                html = f"<!doctype html>\n{html[from_ : to if to != -1 else len(html)]}\n"
            fd, path = tempfile.mkstemp(prefix="callplot-shot-", suffix=".html")
            with os.fdopen(fd, "wb") as fh:
                fh.write(html.encode("utf-8"))
            tmps.append(path)
            js_shots.append([path, dst, width, height])
        return js_shots, tmps
    except BaseException:
        for path in tmps:
            os.unlink(path)
        raise


# the puppeteer capture, run headless; exits non-zero if a shot drew
# nothing or came out too small
JS_TEMPLATE = r"""
import puppeteer from "puppeteer";
import fs from "node:fs";

const PADS = 10;
const SCALE = 2;
const SHOTS = __SHOTS__;

fs.mkdirSync("docs/images", { recursive: true });

const BOX_SELECTOR = ".cpf,pre,table";

function measure(page) {
  return page.evaluate(`(() => {
    let l = Infinity, t = Infinity, r = 0, b = 0;
    for (const el of document.querySelectorAll("${BOX_SELECTOR}")) {
      const rect = el.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) continue;
      l = Math.min(l, rect.left); t = Math.min(t, rect.top);
      r = Math.max(r, rect.right); b = Math.max(b, rect.bottom);
    }
    if (l === Infinity) return null;
    return { x: Math.max(0, Math.floor(l) - ${PADS}), y: Math.max(0, Math.floor(t) - ${PADS}),
             width: Math.ceil(r - l) + ${PADS} * 2, height: Math.ceil(b - t) + ${PADS} * 2 };
  })()`);
}

const browser = await puppeteer.launch({ args: ["--no-sandbox"] });
for (const [src, dst, width, height] of SHOTS) {
  const page = await browser.newPage();
  await page.setViewport({ width, height, deviceScaleFactor: SCALE });
  await page.setContent(fs.readFileSync(src, "utf8"),
                       { waitUntil: "networkidle0" });
  const box = await measure(page);
  if (box === null) {
    throw new Error(`${src} drew nothing to capture`);
  }
  await page.screenshot({ path: dst, clip: box,
                          captureBeyondViewport: true });
  const bytes = fs.statSync(dst).size;
  if (bytes < 8000) {
    throw new Error(`${dst} too small (${bytes} bytes): nothing to show off`);
  }
  console.log(`${dst}: ${bytes} bytes (clip ${box.width}x${box.height})`);
}
await browser.close();
"""


def main():
    js_shots, tmps = staged_shots()
    try:
        src = JS_TEMPLATE.replace("__SHOTS__", json.dumps(js_shots))
        r = subprocess.run(["node", "--input-type=module", "-e", src], capture_output=True)
    finally:
        for path in tmps:
            os.unlink(path)
    out = r.stdout.decode("utf-8", "replace")
    err = r.stderr.decode("utf-8", "replace")
    if out:
        sys.stdout.write(out)
    if r.returncode != 0:
        sys.stderr.write(err)
        print(f"shots: puppeteer capture failed, exit {r.returncode}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
