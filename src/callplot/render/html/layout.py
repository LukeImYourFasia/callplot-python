"""Section 3.12.4: diagram geometry for the -html SVG, in CSS pixels.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Text width is ESTIMATED (never measured) so the output is machine-
independent.  Geometry the svgOn draws and layout widths must agree on;
the constants below are my decisions where section 3.12.4 leaves the
drawing open.
"""

from ...jcompat import jsRound

CW = 7.5  # one caption character (12.5px mono font)
LABW = 7.6  # one label character (13px UI font)
LH = 16  # one text line
M = 28  # left and right margin
TOP = 16  # space above the participant boxes
PITCH_MIN = 150
PITCH_MAX = 300

NOTE_DX = 12  # note box left edge, right of the lifeline
NOTE_PAD = 16  # note box width = caption width + padding
NOTE_DY = 18  # note box top inside its event band
SELF_W = 34  # self loop width
SELF_H = 18  # self loop height
SELF_DX = 40  # self caption left edge, right of the loop
HL_DY = 8  # .hl rect starts 8px above the band top
HL_BOT = 12  # SVG height = last event bottom + 12


def capW(event):
    """Estimated caption width of an event: longest line times CW, plus
    room for the badge (numbered events get the wider room)."""
    length = 0
    for line in event["caption"]:
        if len(line) > length:
            length = len(line)
    return length * CW + (28 if event["num"] is not None else 6)


def computeLayout(model):
    """Steps 1-8 of section 3.12.4; returns the layout dict used by svgOn."""
    # steps 2-3: pitch starts at 150, raised by the widest label and by
    # every event spanning 2 or more lifelines
    pitch = PITCH_MIN
    labelLines = 1
    for p in model["participants"]:
        length = 0
        for line in p["label"]:
            if len(line) > length:
                length = len(line)
        if len(p["label"]) > labelLines:
            labelLines = len(p["label"])
        pitch = max(pitch, length * LABW + 36)
    for e in model["events"]:
        span = abs(e["from"] - e["to"])
        if span >= 2:
            pitch = max(pitch, capW(e) / span + 24)

    # step 4: round (half up, JS Math.round), then cap at 300
    pitch = min(jsRound(pitch), PITCH_MAX)

    # step 5: lifelines are centered in their pitch slots
    n = len(model["participants"])
    x = [M + pitch / 2 + i * pitch for i in range(n)]

    # steps 6-8: band stacking; the first event starts below the boxes
    boxH = 14 + labelLines * LH
    top0 = TOP + boxH + 30
    bands = []
    capLens = []
    top = top0
    rightEdge = 2 * M + n * pitch
    for e in model["events"]:
        length = 0
        for line in e["caption"]:
            if len(line) > length:
                length = len(line)
        capLens.append(length)
        lines = len(e["caption"])
        h = lines * LH + (38 if e["kind"] == "self" else 30)
        bands.append({"top": top, "h": h})
        top += h
        if e["kind"] == "note" or e["kind"] == "self":
            if e["kind"] == "note":
                edge = x[e["from"]] + NOTE_DX + length * CW + NOTE_PAD
            else:
                edge = x[e["from"]] + SELF_DX + length * CW
            if edge + M > rightEdge:
                rightEdge = edge + M

    if len(bands) == 0:
        H = top0
    else:
        H = bands[-1]["top"] + bands[-1]["h"]

    return {
        "pitch": pitch,
        "boxH": boxH,
        "top0": top0,
        "x": x,
        "n": n,
        "W": rightEdge,
        "H": H + HL_BOT,
        "CW": CW,
        "LABW": LABW,
        "LH": LH,
        "M": M,
        "TOP": TOP,
        "NOTE_DX": NOTE_DX,
        "NOTE_PAD": NOTE_PAD,
        "NOTE_DY": NOTE_DY,
        "SELF_W": SELF_W,
        "SELF_H": SELF_H,
        "SELF_DX": SELF_DX,
        "HL_DY": HL_DY,
        "HL_BOT": HL_BOT,
        "events": bands,
        "capLens": capLens,
    }
