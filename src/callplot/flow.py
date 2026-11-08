"""Flow: options, layout and geometry.

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Flow.java:84-88 ctor, 90-116 option helpers, 118-168 geometry getters,
170-212 VML/text getters, 214-247 honorOpts, 249-277 layout, 279-288
columnOf, 289-301 numbering.  Option order per DESIGN.md section 3.3:
stagger first because other defaults depend on it.  All arithmetic is
Java int; idiv for division.
"""

from .jcompat import IllegalArgumentError, NumberFormatError, parseJavaInt, JavaRuntimeException


class Flow:
    def __init__(self, players, messages, opts):
        self.players = players
        self.messages = messages
        self.opts = opts  # Map; later put wins
        self.vmlXSize = 0  # Flow.java:422 vml_x_size; set by picture renderers
        self.vmlYSize = 0  # Flow.java:421 vml_y_size

    # Flow.java:90-97. A bad value throws NumberFormatError.
    def getIntValueOr(self, name, dflt):
        val = self.opts.get(name)
        if val is not None:
            return parseJavaInt(val)
        return dflt

    # Flow.java:99-116. Case-insensitive yes/true/on and no/false/off;
    # anything else throws, like Java's RuntimeException.
    def getBooleanValueOr(self, name, dflt):
        val = self.opts.get(name)
        if val is not None:
            lc = val.lower()
            if lc in ("yes", "true", "on"):
                return True
            elif lc in ("no", "false", "off"):
                return False
            else:
                raise JavaRuntimeException("Bad value for boolean option")
        return dflt

    def optsHas(self, name):
        return name in self.opts

    # Flow.java:214-247
    def honorOpts(self):
        self.stagger = self.getBooleanValueOr("stagger", False)

        self.startLine = self.getIntValueOr("startLine", 7 if self.stagger else 4)
        self.startColumn = self.getIntValueOr("startColumn", 10)
        self.linePitch = self.getIntValueOr("linePitch", 4)
        if self.linePitch < 2:
            self.linePitch = 2
        self.columnPitch = self.getIntValueOr("columnPitch", 10)
        self.numPlayers = len(self.players)
        self.numMessages = len(self.messages)

        self.crunch = self.getBooleanValueOr("crunch", False)
        self.links = self.getBooleanValueOr("links", True)
        self.topLabel = self.getBooleanValueOr("topLabel", True)
        self.bottomLabel = self.getBooleanValueOr("bottomLabel", False)
        self.doNumbering = self.getBooleanValueOr("messageNumbering", False)
        self.doNoteNumbering = self.getBooleanValueOr("noteNumbering", False)

        # An option present with an empty value stays empty (a Java Map
        # returns "", not the default), so use dict.get(name, default).
        self.picXSize = self.opts.get("picXSize", " ")
        self.picYSize = self.opts.get("picYSize", " ")

        self.vmlStyle = self.opts.get("vmlStyle", " ")
        self.vmlFont = self.opts.get("vmlFont", "courier new")
        self.vmlTextSize = self.opts.get("vmlTextSize", "9")
        self.vmlArrowStyle = self.opts.get("vmlArrowStyle", "EndArrow='Open'")
        self.vmlDotStyle = self.opts.get("vmlDottedStyle", "DashStyle='dot'")
        self.vmlBoxStyle = self.opts.get("vmlBoxStyle", "fillcolor='red'")
        self.vmlTextStyle = self.opts.get("vmlTextStyle", "-")
        self.vmlBoxTextStyle = self.opts.get("vmlBoxTextStyle", "-")
        self.vmlBoxWidthPercentage = self.opts.get(
            "vmlBoxWidthPercentage", "160" if self.stagger else "90")

    # Flow.java:249-277
    def layout(self):
        self.honorOpts()

        self.guyCaptionLines = 0

        col = self.startColumn
        for p in self.players:
            p.column = col
            col += self.columnPitch
            if len(p.caption) > self.guyCaptionLines:
                self.guyCaptionLines = len(p.caption)

        if self.topLabel:
            self.startLine += self.guyCaptionLines

        line = self.startLine
        for m in self.messages:
            length = m.getLength()
            line += (length + 1 - self.linePitch) if length >= self.linePitch else 0
            m.line = line
            line += self.linePitch
        self.height = line

    # Flow.java:118-124
    def getStartLine(self):
        return self.startLine

    def getLinePitch(self):
        return self.linePitch

    # Flow.java:126-128
    def getStartColumn(self):
        return self.startColumn

    # Flow.java:130-132
    def getColumnPitch(self):
        return self.columnPitch

    # Flow.java:134-136
    def getTotalWidth(self):
        return self.numPlayers * self.columnPitch + self.startColumn + self.columnPitch

    # Flow.java:138-142
    def getTotalHeight(self):
        return self.height

    # Flow.java:144-146
    def getHeaderHeight(self):
        return self.guyCaptionLines

    # Flow.java:148-156
    def labelLine(self, line):
        if self.topLabel and line < self.guyCaptionLines:
            return line
        elif self.bottomLabel and self.getTotalHeight() - line < self.guyCaptionLines:
            return self.guyCaptionLines - 1 - (self.getTotalHeight() - line)
        else:
            return -1

    # Flow.java:158-168
    def getDoNumbering(self):
        return self.doNumbering

    def getStagger(self):
        return self.stagger

    def getDoNoteNumbering(self):
        return self.doNoteNumbering

    # Flow.java:170-184
    def getVMLStyle(self):
        return self.vmlStyle

    def getVMLArrowStyle(self):
        return self.vmlArrowStyle

    def getVMLDottedStyle(self):
        return self.vmlDotStyle

    def getVMLBoxStyle(self):
        return self.vmlBoxStyle

    # Flow.java:186-196. Sentinel "-": build from vmlFont/vmlTextSize.
    def getVMLTextStyle(self):
        if self.vmlTextStyle == "-":
            return ('style=\'FONT-FAMILY:"' + self.vmlFont + '";FONT-SIZE:'
                    + self.vmlTextSize + "pt;V-TEXT-ALIGN:left'")
        return self.vmlTextStyle

    # Flow.java:198-208 (same, center-aligned)
    def getVMLBoxTextStyle(self):
        if self.vmlBoxTextStyle == "-":
            return ('style=\'FONT-FAMILY:"' + self.vmlFont + '";FONT-SIZE:'
                    + self.vmlTextSize + "pt;V-TEXT-ALIGN:center'")
        return self.vmlBoxTextStyle

    # Flow.java:210-212; parsed with parseJavaInt at draw time
    def getVMLBoxWidthPercentage(self):
        return self.vmlBoxWidthPercentage

    # Flow.java:424-430
    def getVMLXSize(self):
        return self.vmlXSize

    def getVMLYSize(self):
        return self.vmlYSize

    # Flow.java:303-305: the method exists but does nothing. Section 3.8 #2.
    def xmlEscape(self, s):
        return s

    # Flow.java:279-287: first match wins; lazy call sites decide PIC behavior
    def columnOf(self, name):
        for p in self.players:
            if p.name == name:
                return p.column
        raise IllegalArgumentError("no player named " + name)

    # Flow.java:289-301: msgNum resets per render, not per run (section 3.6)
    def startMessageNumbers(self):
        self.msgNum = 1

    def nextMessageNumber(self):
        if self.getDoNumbering():
            num = self.msgNum
            self.msgNum += 1
            return num
        return -1

    # Flow.java:432-447: crunch drops lines holding only spaces and bars
    def shouldPrint(self, buf):
        if not self.crunch:
            return True
        for ch in buf.a:
            if ch != " " and ch != "|":
                return True
        return False
