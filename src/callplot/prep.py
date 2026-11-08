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
"""

import re

from .jcompat import jsNum

# --- awk number printing ----------------------------------------------------


def awkNum(x):
    """awk prints a non-whole number with OFMT %.6g and a whole one without
    a decimal point.  For this program's values (time-of-day diffs, at most
    ~86400) that is plain decimal; exponent cases do not occur (section
    3.14.1)."""
    return jsNum(float("%.6g" % x))


def awkNumPrefix(s):
    """awk string -> number: longest leading numeric prefix, 0 when none."""
    i = 0
    while i < len(s) and (s[i] == " " or s[i] == "\t"):
        i += 1
    j = i
    if j < len(s) and (s[j] == "+" or s[j] == "-"):
        j += 1
    digitsStart = j
    seenDot = False
    while j < len(s):
        c = s[j]
        if "0" <= c <= "9":
            j += 1
        elif c == "." and not seenDot:
            seenDot = True
            j += 1
        else:
            break
    if j == digitsStart:
        return 0.0  # sign alone or no digits: awk gives 0
    return float(s[i:j])


def toTime(ts):
    """awk's toTime (section 3.14.2 time lines): replace every '/', ',',
    ' ', '.' with ':', split on ':', then arr[n]/1000 + arr[n-1] + 60 *
    arr[n-2] + 3600 * arr[n-3]; empty or non-numeric parts count as 0."""
    parts = re.sub(r"[/,. ]", ":", ts).split(":")
    n = len(parts)

    def at(i):
        if i < 1 or i > n:
            return 0.0
        return awkNumPrefix(parts[i - 1])

    return at(n) / 1000 + at(n - 1) + 60 * at(n - 2) + 3600 * at(n - 3)


# awk field semantics: FS " " splits on runs of blanks, ignoring leading and
# trailing blanks; missing fields are the empty string ($1/$2/$3/$4 are
# indexed directly, so pad to four).

_SPLIT_BLANKS = re.compile(r"[ \t]+")


def splitFields(line):
    trimmed = line.strip(" \t")
    if trimmed == "":
        return ["", "", "", ""]
    f = _SPLIT_BLANKS.split(trimmed)
    while len(f) < 4:
        f.append("")
    return f


# the awk gsub triple: escape & < > of the CURRENT $0 (& first, so the
# entities introduced for < and > are themselves not re-escaped)


def esc0(cur):
    return cur.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --- the rule table (section 3.14.2, file order) -----------------------------

DATE4_RE = re.compile(r"^Date [0-9][0-9]/[0-9][0-9]/[0-9][0-9][0-9][0-9]")
DATE5_RE = re.compile(r"^[0-9][0-9]/[0-9][0-9]/[0-9][0-9][0-9][0-9]")
HTTP_RE = re.compile(r"^HTTP/1.. ")
DASH_HTTP_RE = re.compile(r"^-HTTP/1.. ")

METHODS = ("MESSAGE", "INVITE", "BYE", "CANCEL", "REGISTER", "INFO",
           "NOTIFY", "SUBSCRIBE", "PUBLISH")
VERBS = ("GET", "POST")


def methodStart(word):  # /^MESSAGE|INVITE|.../ tests the START of $1
    for m in METHODS:
        if word.startswith(m):
            return True
    return False


def verbStart(word):
    for v in VERBS:
        if word.startswith(v):
            return True
    return False


LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def prep(text, opts=None):
    """Turn a packet trace into callplot input (section 3.14).

    opts = {"links": bool} mirrors --links / LINKS=y.  Returns {"out": str,
    "debug": [str]}: the awk script appends the debug lines to a file named
    "debug", this port only returns them (section 3.14.4; the CLI writes
    them to --debug-file, an Appendix B erratum of the original).
    """
    if opts is None:
        opts = {}
    links = opts.get("links") is True

    out = []
    debug = []  # the awk ">> debug" lines

    # BEGIN block
    out.append("opt/messageNumbering/on")
    out.append("opt/xml/on")
    out.append("opt/crunch/on")
    out.append("opt/links/on" if links else "opt/links/off")

    letidx = 0
    alias = {}
    guys = {}
    t0 = ""
    t = ""
    lt = ""
    s = ""
    d = ""
    mDate = ""
    mSrc = ""
    mDest = ""

    def setDate(line):
        """rules 4/5 action (the t0/lt/t ladder, then the gsub triple; t
        takes $0 BEFORE it is escaped, as the awk action order does; the
        escaped re-split is unused after `next`, so it is elided)"""
        nonlocal t0, t, lt, mDate
        lt = t
        t = line
        if t0 == "":
            t0 = t
        mDate = "!!" + esc0(line)

    def setAddr(field, line):
        """rules 6/7 action: resolve $3 through ALIAS/GUYS, minting a letter
        label when needed (quirk 2 of section 3.14.3: past 52 labels the
        letter is empty); mSrc/mDest tag the ESCAPED line"""
        nonlocal letidx
        raw = field.replace("\r", "", 1)  # sub("\r","",s): first match only
        v = alias[raw] if raw in alias else raw
        if v not in guys:
            debug.append("[" + v + "] not in guys")
            letr = LETTERS[letidx] if letidx < len(LETTERS) else ""
            letidx += 1
            out.append("guy/" + letr + "/" + v)
            guys[v] = letr
        return guys[v], "!!" + esc0(line)

    def tdiffs():
        """the two time lines; awk's bt != "" guard never fires because a
        number never string-equals "" (quirk 1 of 3.14.3: with lt empty the
        "from last" value is the whole time of day)"""
        at = toTime(t)
        bInit = toTime(t0)
        bLast = toTime(lt)
        out.append("!!    " + awkNum(at - bInit) + " from initial")
        out.append("!!    " + awkNum(at - bLast) + " from last")

    # awk splits input lines on "\n"; a trailing newline adds no empty line
    rawLines = text.split("\n")
    if len(rawLines) > 0 and rawLines[-1] == "":
        rawLines.pop()

    for raw in rawLines:
        cur = raw
        cr = cur.find("\r")
        if cr >= 0:
            cur = cur[:cr] + cur[cr + 1:]  # sub("\r","",$0): first match only
        f = splitFields(cur)

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
            setDate(cur)
            continue  # next

        # rule 5: starts with dd/dd/dddd
        if DATE5_RE.match(cur):
            setDate(cur)
            continue  # next

        # rule 6: starts with Source Address
        if cur.startswith("Source Address"):
            label, tag = setAddr(f[2], cur)
            s = label
            mSrc = tag
            continue  # next

        # rule 7: starts with Destination Address
        if cur.startswith("Destination Address"):
            label, tag = setAddr(f[2], cur)
            d = label
            mDest = tag
            continue  # next

        # rules 8-11: packet request lines; they print, then fall through
        # to rule 16 (quirk 4 of 3.14.3).  cur[len(f[0]) + 1:] copies
        # replace(f[0] + " ", ""): the rule's own test guarantees a match
        # at 0, so the first match removes exactly the first field plus a
        # blank.
        if methodStart(f[0]):
            out.append(s + "->" + d + "/" + f[0])
            out.append(mDate)
            tdiffs()
            out.append(mSrc + " (" + s + ")" if len(s) > 1 else mSrc)
            out.append(mDest + " (" + d + ")")
        elif verbStart(f[0]):
            out.append(s + "->" + d + "/" + f[0])
            out.append(mDate)
            tdiffs()
            out.append(mSrc + " (" + s + ")" if len(s) > 1 else mSrc)
            out.append(mDest + " (" + d + ")")
        elif cur.startswith("SIP/2.0 "):
            line = cur[len(f[0]) + 1:]
            out.append(s + "->" + d + "/" + line)
            out.append(mDate)
            tdiffs()
            out.append(mSrc + " (" + s + ")" if len(s) > 1 else mSrc)
            out.append(mDest + " (" + d + ")")
        elif HTTP_RE.match(cur):
            line = cur[len(f[0]) + 1:]
            out.append(s + "->" + d + "/" + line)
            out.append(mDate)
            tdiffs()
            out.append(mSrc + " (" + s + ")" if len(s) > 1 else mSrc)
            out.append(mDest + " (" + d + ")")

        # rules 12-15: the dash variants print only the hidden-message line
        if f[0].startswith("-") and methodStart(f[0][1:]):
            out.append("-" + s + "->" + d + "/" + f[0][1:])
        elif f[0].startswith("-") and verbStart(f[0][1:]):
            out.append("-" + s + "->" + d + "/" + f[0][1:])
        elif cur.startswith("-SIP/2.0 "):
            line = cur[len(f[0]) + 1:]
            out.append("-" + s + "->" + d + "/" + line)
        elif DASH_HTTP_RE.match(cur):
            line = cur[len(f[0]) + 1:]
            out.append("-" + s + "->" + d + "/" + line)

        # rule 16: every line that got here (and the 8-15 fall-throughs)
        cur = esc0(cur)
        f = splitFields(cur)  # awk re-splits after the gsub; unused after
        out.append("!" + cur)

    return {"out": "\n".join(out) + ("\n" if len(out) > 0 else ""),
            "debug": debug}
