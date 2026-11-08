"""Section 3.12.7: the page's one CSS string.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Every rule is scoped inside .cpf so the page can be embedded.  System
fonts only; color tokens carry fallbacks so the SVG paints standalone.
The layout switch keeps the radios visually hidden but keyboard-reachable;
attribute selectors are end-matched ($=) so an idPrefix keeps them working.
"""

CSS = "\n".join([
    ".cpf{--cpf-page:#ffffff;--cpf-ink:#17232e;--cpf-mut:#5d6d7a;",
    "--cpf-line:#b7c2cc;--cpf-head:#e8eef4;--cpf-accent:#2f6b8f;",
    "--cpf-hl:rgba(255,212,89,.28);--cpf-note-fill:#fff8dd;--cpf-note-line:#c8b45f;",
    "--cpf-media:#008080;--cpf-pill:#eef3f8;",
    "container-type:inline-size;container-name:cpf;",
    "font-family:ui-sans-serif,system-ui,sans-serif;font-size:14px;",
    "color:var(--cpf-ink);background:var(--cpf-page)}",
    "@media (prefers-color-scheme:dark){.cpf{--cpf-page:#101821;--cpf-ink:#dbe4ec;",
    "--cpf-mut:#93a4b1;--cpf-line:#3a4652;--cpf-head:#1c2632;--cpf-accent:#4182ad;",
    "--cpf-hl:rgba(255,212,89,.16);--cpf-note-fill:#2c2b1c;--cpf-note-line:#c8b45f;",
    "--cpf-media:#3fc0b6;--cpf-pill:#243040}}",
    ".cpf-head h1{font-size:20px;margin:0}",
    ".cpf-head p{margin:0;color:var(--cpf-mut)}",
    ".cpf-radio{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}",
    ".cpf-switch{display:inline-block;margin-top:8px}",
    ".cpf-switch label{cursor:pointer;margin-right:14px}",
    '.cpf:has(.cpf-radio[id$="lay-tb"]:focus-visible) .cpf-switch label[for$="lay-tb"]'
    "{outline:2px solid var(--cpf-accent);outline-offset:2px}",
    '.cpf:has(.cpf-radio[id$="lay-sbs"]:focus-visible) .cpf-switch label[for$="lay-sbs"]'
    "{outline:2px solid var(--cpf-accent);outline-offset:2px}",
    ".cpf-main{display:grid;grid-template-columns:1fr}",
    ".cpf-scroll{overflow-x:auto}",
    ".cpf-tscroll{overflow:auto}",
    "@container cpf (min-width:1100px){",
    '.cpf:has(.cpf-radio[id$="lay-sbs"]:checked) .cpf-main{grid-template-columns:'
    "minmax(0,1.15fr) minmax(0,1fr);height:var(--cpf-pane-h,100vh)}",
    '.cpf:has(.cpf-radio[id$="lay-sbs"]:checked) .cpf-flow,.cpf:has(.cpf-radio'
    '[id$="lay-sbs"]:checked) .cpf-detail{height:100%;overflow:hidden;display:flex;'
    "flex-direction:column}",
    '.cpf:has(.cpf-radio[id$="lay-sbs"]:checked) .cpf-scroll,.cpf:has(.cpf-radio'
    '[id$="lay-sbs"]:checked) .cpf-tscroll{flex:1;overflow:auto}',
    "}",
    ".cpf-svg{display:block}",
    ".lf{stroke:var(--cpf-line)}",
    ".pf-box{fill:var(--cpf-head);stroke:var(--cpf-line)}",
    ".lb,.cap,.bn{font-size:13px}",
    ".lb{font-family:ui-sans-serif,system-ui,sans-serif}",
    ".cap{font-family:ui-monospace,Menlo,Consolas,monospace}",
    ".ln{stroke:var(--cpf-ink);stroke-width:1.5}",
    ".cpf .ev-media .ln{stroke:var(--cpf-media)}",
    ".ah{stroke:none}",
    ".nt{fill:var(--cpf-note-fill);stroke:var(--cpf-note-line)}",
    ".bdg{fill:var(--cpf-accent)}",
    ".bn{font-family:ui-monospace,Menlo,Consolas,monospace}",
    ".badge text-decoration:none",
    ".hl{opacity:0}",
    ".cpf g:target>.hl{opacity:1;fill:var(--cpf-hl)}",
    ".ev{scroll-margin:40px 120px}",
    "@media (prefers-reduced-motion:reduce){.hl{transition:none}}",
    "@media (prefers-reduced-motion:no-reduce){.hl{transition:opacity .18s ease}}",
    "table{border-collapse:collapse;min-width:760px}",
    "th,td{text-align:left;padding:6px 10px;border-bottom:1px solid var(--cpf-line)}",
    "thead th{position:sticky;top:0;z-index:2;background:var(--cpf-head);color:var(--cpf-ink)}",
    'table th[scope="row"]{position:sticky;left:0;z-index:1;background:var(--cpf-page)}',
    ".back{color:var(--cpf-mut)}",
    "tr:target th,tr:target td{background:var(--cpf-hl)}",
    ".pill{display:inline-block;padding:2px 10px;border-radius:999px;"
    "background:var(--cpf-pill)}",
    "code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px}",
    "td:nth-child(6){text-align:right;font-variant-numeric:tabular-nums}",
    "@media print{.cpf-radio{display:none}.cpf-switch{display:none}"
    ".cpf-main{grid-template-columns:1fr}.cpf-flow,.cpf-detail{height:auto}}",
    "",
])
