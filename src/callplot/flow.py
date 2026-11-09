"""Flow: options, layout and geometry (DESIGN.md section 3.3/3.4.0).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Flow.java:84-88 ctor, 90-116 option helpers, 118-168 geometry getters,
170-212 VML/text getters, 214-247 honorOpts, 249-277 layout, 279-288
columnOf, 289-301 numbering.  Option order per DESIGN.md section 3.3:
stagger first because other defaults depend on it.  All arithmetic is
Java int; idiv for division.  DESIGN-PYTHON.md: the layout results are
declared once in __init__ (honorOpts/layout fill them before any
renderer reads them).
"""

from callplot.errors import IllegalArgumentError, JavaRuntimeError
from callplot.jcompat import CharBuf, parse_java_int
from callplot.model import Message, Player


class Flow:
    def __init__(
        self,
        players: list[Player],
        messages: list[Message],
        opts: dict[str, str],
    ) -> None:
        self.players = players
        self.messages = messages
        self.opts = opts  # Map; later put wins
        self.vml_x_size = 0  # Flow.java:422 vml_x_size; set by picture renderers
        self.vml_y_size = 0  # Flow.java:421 vml_y_size

        # Layout results, filled by honorOpts()/layout() (all read only
        # after layout()).  Declared here so the type checker sees them.
        self.stagger = False
        self.start_line = 0
        self.start_column = 0
        self.line_pitch = 0
        self.column_pitch = 0
        self.num_players = 0
        self.num_messages = 0
        self.crunch = False
        self.links = True
        self.top_label = False
        self.bottom_label = False
        self.do_numbering = False
        self.do_note_numbering = False
        self.pic_x_size = " "
        self.pic_y_size = " "
        self.vml_style = " "
        self.vml_font = "courier new"
        self.vml_text_size = "9"
        self.vml_arrow_style = "EndArrow='Open'"
        self.vml_dot_style = "DashStyle='dot'"
        self.vml_box_style = "fillcolor='red'"
        self.vml_text_style = "-"
        self.vml_box_text_style = "-"
        self.vml_box_width_percentage = "90"
        self.guy_caption_lines = 0
        self.height = 0
        self.msg_num = 0

    # Flow.java:90-97. A bad value throws NumberFormatError.
    def get_int_value_or(self, name: str, dflt: int) -> int:
        val = self.opts.get(name)
        if val is not None:
            return parse_java_int(val)
        return dflt

    # Flow.java:99-116. Case-insensitive yes/true/on and no/false/off;
    # anything else throws, like Java's RuntimeException.
    def get_boolean_value_or(self, name: str, dflt: bool) -> bool:
        val = self.opts.get(name)
        if val is not None:
            lc = val.lower()
            if lc in ("yes", "true", "on"):
                return True
            if lc in ("no", "false", "off"):
                return False
            raise JavaRuntimeError("Bad value for boolean option")
        return dflt

    def opts_has(self, name: str) -> bool:
        return name in self.opts

    # Flow.java:214-247
    def honor_opts(self) -> None:
        self.stagger = self.get_boolean_value_or("stagger", False)

        self.start_line = self.get_int_value_or("startLine", 7 if self.stagger else 4)
        self.start_column = self.get_int_value_or("startColumn", 10)
        self.line_pitch = self.get_int_value_or("linePitch", 4)
        if self.line_pitch < 2:
            self.line_pitch = 2
        self.column_pitch = self.get_int_value_or("columnPitch", 10)
        self.num_players = len(self.players)
        self.num_messages = len(self.messages)

        self.crunch = self.get_boolean_value_or("crunch", False)
        self.links = self.get_boolean_value_or("links", True)
        self.top_label = self.get_boolean_value_or("topLabel", True)
        self.bottom_label = self.get_boolean_value_or("bottomLabel", False)
        self.do_numbering = self.get_boolean_value_or("messageNumbering", False)
        self.do_note_numbering = self.get_boolean_value_or("noteNumbering", False)

        # An option present with an empty value stays empty (a Java Map
        # returns "", not the default), so use dict.get(name, default).
        self.pic_x_size = self.opts.get("picXSize", " ")
        self.pic_y_size = self.opts.get("picYSize", " ")

        self.vml_style = self.opts.get("vmlStyle", " ")
        self.vml_font = self.opts.get("vmlFont", "courier new")
        self.vml_text_size = self.opts.get("vmlTextSize", "9")
        self.vml_arrow_style = self.opts.get("vmlArrowStyle", "EndArrow='Open'")
        self.vml_dot_style = self.opts.get("vmlDottedStyle", "DashStyle='dot'")
        self.vml_box_style = self.opts.get("vmlBoxStyle", "fillcolor='red'")
        self.vml_text_style = self.opts.get("vmlTextStyle", "-")
        self.vml_box_text_style = self.opts.get("vmlBoxTextStyle", "-")
        self.vml_box_width_percentage = self.opts.get(
            "vmlBoxWidthPercentage", "160" if self.stagger else "90"
        )

    # Flow.java:249-277
    def layout(self) -> None:
        self.honor_opts()

        self.guy_caption_lines = 0

        col = self.start_column
        for p in self.players:
            p.column = col
            col += self.column_pitch
            if len(p.caption) > self.guy_caption_lines:
                self.guy_caption_lines = len(p.caption)

        if self.top_label:
            self.start_line += self.guy_caption_lines

        line = self.start_line
        for m in self.messages:
            length = m.get_length()
            line += (length + 1 - self.line_pitch) if length >= self.line_pitch else 0
            m.line = line
            line += self.line_pitch
        self.height = line

    # Flow.java:118-124
    def get_start_line(self) -> int:
        return self.start_line

    def get_line_pitch(self) -> int:
        return self.line_pitch

    # Flow.java:126-128
    def get_start_column(self) -> int:
        return self.start_column

    # Flow.java:130-132
    def get_column_pitch(self) -> int:
        return self.column_pitch

    # Flow.java:134-136
    def get_total_width(self) -> int:
        return self.num_players * self.column_pitch + self.start_column + self.column_pitch

    # Flow.java:138-142
    def get_total_height(self) -> int:
        return self.height

    # Flow.java:144-146
    def get_header_height(self) -> int:
        return self.guy_caption_lines

    # Flow.java:148-156
    def label_line(self, line: int) -> int:
        if self.top_label and line < self.guy_caption_lines:
            return line
        if self.bottom_label and self.get_total_height() - line < self.guy_caption_lines:
            return self.guy_caption_lines - 1 - (self.get_total_height() - line)
        return -1

    # Flow.java:158-168
    def get_do_numbering(self) -> bool:
        return self.do_numbering

    def get_stagger(self) -> bool:
        return self.stagger

    def get_do_note_numbering(self) -> bool:
        return self.do_note_numbering

    # Flow.java:170-184
    def get_vml_style(self) -> str:
        return self.vml_style

    def get_vml_arrow_style(self) -> str:
        return self.vml_arrow_style

    def get_vml_dotted_style(self) -> str:
        return self.vml_dot_style

    def get_vml_box_style(self) -> str:
        return self.vml_box_style

    # Flow.java:186-196. Sentinel "-": build from vml_font/vml_text_size.
    def get_vml_text_style(self) -> str:
        if self.vml_text_style == "-":
            return (
                "style='FONT-FAMILY:\""
                + self.vml_font
                + '";FONT-SIZE:'
                + self.vml_text_size
                + "pt;V-TEXT-ALIGN:left'"
            )
        return self.vml_text_style

    # Flow.java:198-208 (same, center-aligned)
    def get_vml_box_text_style(self) -> str:
        if self.vml_box_text_style == "-":
            return (
                "style='FONT-FAMILY:\""
                + self.vml_font
                + '";FONT-SIZE:'
                + self.vml_text_size
                + "pt;V-TEXT-ALIGN:center'"
            )
        return self.vml_box_text_style

    # Flow.java:210-212; parsed with parseJavaInt at draw time
    def get_vml_box_width_percentage(self) -> str:
        return self.vml_box_width_percentage

    # Flow.java:424-430
    def get_vml_x_size(self) -> int:
        return self.vml_x_size

    def get_vml_y_size(self) -> int:
        return self.vml_y_size

    # Flow.java:432-447: crunch drops lines holding only spaces and bars
    def should_print(self, buf: CharBuf) -> bool:
        if not self.crunch:
            return True
        return any(ch != " " and ch != "|" for ch in buf.a)
        return False

    # Flow.java:303-305: the method exists but does nothing. Section 3.8 #2.
    def xml_escape(self, s: str) -> str:
        return s

    # Flow.java:279-287: first match wins; lazy call sites decide PIC behavior
    def column_of(self, name: str) -> int:
        for p in self.players:
            if p.name == name:
                return p.column
        raise IllegalArgumentError("no player named " + name)

    # Flow.java:289-301: msg_num resets per render, not per run (section 3.6)
    def start_message_numbers(self) -> None:
        self.msg_num = 1

    def next_message_number(self) -> int:
        if self.get_do_numbering():
            num = self.msg_num
            self.msg_num += 1
            return num
        return -1
