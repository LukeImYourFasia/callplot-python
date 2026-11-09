"""Section 3.14: callplot-prep, a port of lib/prep.awk (mawk 1.3.4 oracle).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

The awk semantics are pinned (DESIGN.md section 3.14.1): every rule is
tested in order, `next` stops the rules for the line, changing $0 re-splits
fields, print of numbers uses OFMT %.6g (awkNum), sub is first-match, gsub
all.  Section 3.14.4: awk appends debug lines to a file literally named
"debug"; this port returns them and the CLI writes them only where --debug-
file pointed (logged in Appendix B).

DESIGN-PYTHON.md sections 2.3 and 3.8: the public core call is
``prep(text, *, links=False) -> str``, and it does no I/O.  The debug lines
reach the command through ``prep_debug``, which returns the text and the
lines together, so no module keeps state of its own.  Section 3.2 rule: the
text goes through ``to_units`` first and ``from_units`` last, like ``render``.
"""

import re

from callplot.jcompat import from_units, to_units

# --- awk number printing ----------------------------------------------------


def awk_num(x: float) -> str:
    """DESIGN-PYTHON.md 3.8 rule 3: whole numbers print without a decimal
    point, everything else takes OFMT %.6g (Python's %.6g equals C's, and
    therefore awk's, so 1234567.5 comes out as 1.23457e+06)."""
    v = float(x)
    if v == int(v):
        return str(int(v))
    return f"{v:.6g}"


def awk_num_prefix(s: str) -> float:
    """awk string -> number: longest leading numeric prefix, 0 when none."""
    i = 0
    while i < len(s) and (s[i] == " " or s[i] == "\t"):
        i += 1
    j = i
    if j < len(s) and (s[j] == "+" or s[j] == "-"):
        j += 1
    digits_start = j
    seen_dot = False
    while j < len(s):
        c = s[j]
        if "0" <= c <= "9":
            j += 1
        elif c == "." and not seen_dot:
            seen_dot = True
            j += 1
        else:
            break
    if j == digits_start:
        return 0.0  # sign alone or no digits: awk gives 0
    return float(s[i:j])


def to_time(ts: str) -> float:
    """awk's toTime (section 3.14.2 time lines): replace every '/', ',',
    ' ', '.' with ':', split on ':', then arr[n]/1000 + arr[n-1] + 60 *
    arr[n-2] + 3600 * arr[n-3]; empty or non-numeric parts count as 0."""
    parts = re.sub(r"[/,. ]", ":", ts).split(":")
    n = len(parts)

    def at(i: int) -> float:
        if i < 1 or i > n:
            return 0.0
        return awk_num_prefix(parts[i - 1])

    return at(n) / 1000 + at(n - 1) + 60 * at(n - 2) + 3600 * at(n - 3)


# awk field semantics: FS " " splits on runs of blanks, ignoring leading and
# trailing blanks; missing fields are the empty string ($1/$2/$3/$4 are
# indexed directly, so pad to four).

_SPLIT_BLANKS = re.compile(r"[ \t]+")


def split_fields(line: str) -> list[str]:
    trimmed = line.strip(" \t")
    if trimmed == "":
        return ["", "", "", ""]
    f = _SPLIT_BLANKS.split(trimmed)
    while len(f) < 4:
        f.append("")
    return f


# the awk gsub triple: escape & < > of the CURRENT $0 (& first, so the
# entities introduced for < and > are themselves not re-escaped)


def esc0(cur: str) -> str:
    return cur.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --- the rule table (section 3.14.2, file order) -----------------------------

DATE4_RE = re.compile(r"^Date [0-9][0-9]/[0-9][0-9]/[0-9][0-9][0-9][0-9]")
DATE5_RE = re.compile(r"^[0-9][0-9]/[0-9][0-9]/[0-9][0-9][0-9][0-9]")
HTTP_RE = re.compile(r"^HTTP/1.. ")
DASH_HTTP_RE = re.compile(r"^-HTTP/1.. ")

METHODS = (
    "MESSAGE",
    "INVITE",
    "BYE",
    "CANCEL",
    "REGISTER",
    "INFO",
    "NOTIFY",
    "SUBSCRIBE",
    "PUBLISH",
)
VERBS = ("GET", "POST")


def method_start(word: str) -> bool:  # /^MESSAGE|INVITE|.../ tests the START of $1
    return any(word.startswith(m) for m in METHODS)


def verb_start(word: str) -> bool:
    return any(word.startswith(v) for v in VERBS)


LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _trace_lines(text: str, links: bool) -> tuple[str, list[str]]:
    """Turn a packet trace into callplot input (section 3.14).

    Internal worker for ``prep`` and ``prep_debug``: ``links`` mirrors the
    awk's ``LINKS=y`` (the ``--links`` flag).  Returns the joined text and
    the ``>> debug`` lines the awk script appended to a file literally named
    "debug" (section 3.14.4); this port never writes a file (DESIGN-PYTHON.md
    section 3.8 rule 6), the command writes them only where ``--debug-file``
    pointed, an Appendix B erratum of the original.
    """
    out = []
    debug = []  # the awk ">> debug" lines

    # BEGIN block
    out.append("opt/messageNumbering/on")
    out.append("opt/xml/on")
    out.append("opt/crunch/on")
    out.append("opt/links/on" if links else "opt/links/off")

    letidx = 0
    alias: dict[str, str] = {}
    guys: dict[str, str] = {}
    t0 = ""
    t = ""
    lt = ""
    s = ""
    d = ""
    m_date = ""
    m_src = ""
    m_dest = ""

    def set_date(line: str) -> None:
        """rules 4/5 action (the t0/lt/t ladder, then the gsub triple; t
        takes $0 BEFORE it is escaped, as the awk action order does; the
        escaped re-split is unused after `next`, so it is elided)"""
        nonlocal t0, t, lt, m_date
        lt = t
        t = line
        if t0 == "":
            t0 = t
        m_date = "!!" + esc0(line)

    def set_addr(field: str, line: str) -> tuple[str, str]:
        """rules 6/7 action: resolve $3 through ALIAS/GUYS, minting a letter
        label when needed (quirk 2 of section 3.14.3: past 52 labels the
        letter is empty); mSrc/mDest tag the ESCAPED line"""
        nonlocal letidx
        raw = field.replace("\r", "", 1)  # sub("\r","",s): first match only
        v = alias.get(raw, raw)
        if v not in guys:
            debug.append("[" + v + "] not in guys")
            letr = LETTERS[letidx] if letidx < len(LETTERS) else ""
            letidx += 1
            out.append("guy/" + letr + "/" + v)
            guys[v] = letr
        return guys[v], "!!" + esc0(line)

    def tdiffs() -> None:
        """the two time lines; awk's bt != "" guard never fires because a
        number never string-equals "" (quirk 1 of 3.14.3: with lt empty the
        "from last" value is the whole time of day)"""
        at = to_time(t)
        b_init = to_time(t0)
        b_last = to_time(lt)
        out.append("!!    " + awk_num(at - b_init) + " from initial")
        out.append("!!    " + awk_num(at - b_last) + " from last")

    # awk splits input lines on "\n"; a trailing newline adds no empty line
    raw_lines = text.split("\n")
    if len(raw_lines) > 0 and raw_lines[-1] == "":
        raw_lines.pop()

    for raw in raw_lines:
        cur = raw
        cr = cur.find("\r")
        if cr >= 0:
            cur = cur[:cr] + cur[cr + 1 :]  # sub("\r","",$0): first match only
        f = split_fields(cur)

        # rule 1: $1 == "@" (alias line "@ <address> <name>")
        if f[0] == "@":
            a2 = f[1]
            a3 = f[2].replace("\r", "", 1)  # sub("\r","",$3)
            if a3 not in guys:
                out.append("guy/" + a3 + "/" + a3)
                guys[a3] = a3
                debug.append("[" + a3 + "] going into guys")
            alias[a2] = a3
            continue  # next

        # rule 2: starts with @ (pass callplot commands through)
        if cur.startswith("@"):
            out.append(cur[1:])
            continue  # next

        # rule 3: starts with ----
        if cur.startswith("----"):
            continue  # next

        # rule 4: starts with Date dd/dd/dddd
        if DATE4_RE.match(cur):
            set_date(cur)
            continue  # next

        # rule 5: starts with dd/dd/dddd
        if DATE5_RE.match(cur):
            set_date(cur)
            continue  # next

        # rule 6: starts with Source Address
        if cur.startswith("Source Address"):
            label, tag = set_addr(f[2], cur)
            s = label
            m_src = tag
            continue  # next

        # rule 7: starts with Destination Address
        if cur.startswith("Destination Address"):
            label, tag = set_addr(f[2], cur)
            d = label
            m_dest = tag
            continue  # next

        # rules 8-11: packet request lines; they print, then fall through
        # to rule 16 (quirk 4 of 3.14.3).  cur[len(f[0]) + 1:] copies
        # replace(f[0] + " ", ""): the rule's own test guarantees a match
        # at 0, so the first match removes exactly the first field plus a
        # blank.
        if method_start(f[0]) or verb_start(f[0]):
            out.append(s + "->" + d + "/" + f[0])
            out.append(m_date)
            tdiffs()
            out.append(m_src + " (" + s + ")" if len(s) > 1 else m_src)
            out.append(m_dest + " (" + d + ")")
        elif cur.startswith("SIP/2.0 ") or HTTP_RE.match(cur):
            line = cur[len(f[0]) + 1 :]
            out.append(s + "->" + d + "/" + line)
            out.append(m_date)
            tdiffs()
            out.append(m_src + " (" + s + ")" if len(s) > 1 else m_src)
            out.append(m_dest + " (" + d + ")")

        # rules 12-15: the dash variants print only the hidden-message line
        if f[0].startswith("-") and (method_start(f[0][1:]) or verb_start(f[0][1:])):
            out.append("-" + s + "->" + d + "/" + f[0][1:])
        elif cur.startswith("-SIP/2.0 ") or DASH_HTTP_RE.match(cur):
            line = cur[len(f[0]) + 1 :]
            out.append("-" + s + "->" + d + "/" + line)

        # rule 16: every line that got here (and the 8-15 fall-throughs)
        cur = esc0(cur)
        f = split_fields(cur)  # awk re-splits after the gsub; unused after
        out.append("!" + cur)

    return "\n".join(out) + ("\n" if len(out) > 0 else ""), debug


def prep(text: str, *, links: bool = False) -> str:
    """DESIGN-PYTHON.md section 2.3 public core call: a packet trace turns
    into callplot input, whole, in memory.  It never writes a file; use
    ``callplot-prep`` for the command."""
    converted, _debug = _trace_lines(to_units(text), links)
    return from_units(converted)


def prep_debug(text: str, *, links: bool = False) -> tuple[str, list[str]]:
    """The same conversion plus the awk's ``>> debug`` lines, for the command
    that was asked for ``--debug-file`` (section 3.14.4 erratum).

    A transport, not a second behavior: the lines come from the same single
    pass, so ``prep`` and ``prep_debug`` cannot disagree about the text.
    """
    converted, debug = _trace_lines(to_units(text), links)
    return from_units(converted), [from_units(line) for line in debug]
