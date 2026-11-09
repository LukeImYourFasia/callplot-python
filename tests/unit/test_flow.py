"""Unit tests for options and layout in Flow (DESIGN.md sections 3.3/3.4.0,
DESIGN-PYTHON.md section 3.5).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Pins the option and layout rules: stagger first because other defaults depend
on it (startLine 7 when staggered, vmlBoxWidthPercentage 160), linePitch
clamped at 2, bad int values raise NumberFormatError via parse_java_int, bad
boolean values raise the JavaRuntimeError the Java source throws, layout puts
players at startColumn + i*columnPitch, topLabel adds the caption height to
startLine, and a caption at least as tall as linePitch shifts the following
lines by length + 1 - linePitch.

Every test builds its own Flow from callplot.model objects in memory: no file
system access and no fixture reading (DESIGN-PYTHON.md section 4.2 rule 5).
"""

import re

import pytest

from callplot.context import RunContext
from callplot.errors import IllegalArgumentError, JavaRuntimeError, NumberFormatError
from callplot.flow import Flow
from callplot.jcompat import CharBuf, to_units
from callplot.model import Message, Player


def make_flow(n_players=2, captions=("A", "B"), n_messages=2, opts=None):
    """A fresh Flow with distinct players and simple a->b messages."""
    players = [Player(chr(ord("a") + i), captions[i % len(captions)]) for i in range(n_players)]
    messages = [
        Message("a" if i % 2 == 0 else "b", "b" if i % 2 == 0 else "a", f"m{i}")
        for i in range(n_messages)
    ]
    return Flow(players, messages, dict(opts or {}))


# --- option getters ----------------------------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw", "want"), [("42", 42), ("+7", 7), ("0", 0), ("-5", -5), ("2147483647", 2147483647)]
)
def test_flow_get_int_value_or__valid_java_ints(raw, want):
    f = Flow([], [], {"startLine": raw})
    assert f.get_int_value_or("startLine", 4) == want


@pytest.mark.unit
def test_flow_get_int_value_or__missing_uses_default():
    f = Flow([], [], {})
    assert f.get_int_value_or("startLine", 7) == 7
    assert f.get_int_value_or("columnPitch", 10) == 10


@pytest.mark.unit
@pytest.mark.parametrize("raw", [" 42", "42 ", "x", "1_0", "2147483648", ""])
def test_flow_get_int_value_or__bad_int_number_format_error(raw):
    f = Flow([], [], {"startLine": raw})
    with pytest.raises(NumberFormatError):
        f.get_int_value_or("startLine", 4)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw", "want"),
    [
        ("yes", True),
        ("YES", True),
        ("TrUe", True),
        ("on", True),
        ("No", False),
        ("FALSE", False),
        ("off", False),
    ],
)
def test_flow_get_boolean_value_or__case_insensitive_words(raw, want):
    f = Flow([], [], {"stagger": raw})
    assert f.get_boolean_value_or("stagger", False) is want


@pytest.mark.unit
def test_flow_get_boolean_value_or__missing_uses_default():
    f = Flow([], [], {})
    assert f.get_boolean_value_or("links", True) is True
    assert f.get_boolean_value_or("crunch", False) is False


@pytest.mark.unit
def test_flow_get_boolean_value_or__bad_word_raises_java_runtime_error():
    f = Flow([], [], {"stagger": "maybe"})
    with pytest.raises(JavaRuntimeError, match=re.escape("Bad value for boolean option")):
        f.get_boolean_value_or("stagger", False)


@pytest.mark.unit
def test_flow_opts_has__present_and_absent_names():
    f = Flow([], [], {"title": "T"})
    assert f.opts_has("title")
    assert not f.opts_has("stagger")


# --- honorOpts: defaults, the stagger-driven defaults, the clamp -------------


@pytest.mark.unit
def test_flow_honor_opts__defaults_as_in_java():
    f = make_flow()
    f.honor_opts()
    assert f.stagger is False
    assert f.start_line == 4
    assert f.start_column == 10
    assert f.line_pitch == 4
    assert f.column_pitch == 10
    assert f.num_players == 2
    assert f.num_messages == 2
    assert f.crunch is False
    assert f.links is True
    assert f.top_label is True
    assert f.bottom_label is False
    assert f.do_numbering is False
    assert f.do_note_numbering is False
    assert f.pic_x_size == " "
    assert f.vml_font == "courier new"
    assert f.vml_text_size == "9"
    assert f.vml_box_width_percentage == "90"


@pytest.mark.unit
def test_flow_honor_opts__stagger_drives_start_line_and_box_percent():
    f = make_flow(opts={"stagger": "on"})
    f.honor_opts()
    assert f.stagger is True
    assert f.start_line == 7  # stagger's default, not 4
    assert f.vml_box_width_percentage == "160"


@pytest.mark.unit
@pytest.mark.parametrize(("raw", "want"), [("1", 2), ("0", 2), ("-3", 2), ("2", 2), ("3", 3)])
def test_flow_honor_opts__line_pitch_clamped_below_2(raw, want):
    f = make_flow(opts={"linePitch": raw})
    f.honor_opts()
    assert f.line_pitch == want


@pytest.mark.unit
def test_flow_honor_opts__present_option_beats_default_even_when_empty():
    f = make_flow(opts={"picXSize": ""})
    f.honor_opts()
    assert f.pic_x_size == ""  # a Java Map returns "", not the default
    f2 = make_flow()
    f2.honor_opts()
    assert f2.pic_y_size == " "  # absent -> default


@pytest.mark.unit
def test_flow_honor_opts__vml_style_strings_come_through_raw():
    f = make_flow(opts={"vmlArrowStyle": "Arrow='x'", "vmlFont": "Impact"})
    f.honor_opts()
    assert f.vml_arrow_style == "Arrow='x'"
    assert f.vml_font == "Impact"


# --- the option-error traps surface through layout ---------------------------


@pytest.mark.unit
def test_flow_layout__bad_int_option_raises_number_format_error():
    f = make_flow(opts={"linePitch": " 3"})
    with pytest.raises(NumberFormatError, match=re.escape('For input string: " 3"')):
        f.layout()


@pytest.mark.unit
def test_flow_layout__bad_bool_option_raises_java_runtime_error():
    f = make_flow(opts={"stagger": "perhaps"})
    with pytest.raises(JavaRuntimeError, match=re.escape("Bad value for boolean option")):
        f.layout()


# --- layout: columns, start lines, message lines, height, width --------------


@pytest.mark.unit
def test_flow_layout__default_columns_and_lines():
    f = make_flow(n_players=2, n_messages=2)
    f.layout()
    assert [p.column for p in f.players] == [10, 20]
    assert f.start_line == 5  # 4 + guy_caption_lines 1 (topLabel on)
    assert [m.line for m in f.messages] == [5, 9]
    assert f.height == 13
    assert f.guy_caption_lines == 1


@pytest.mark.unit
def test_flow_layout__custom_start_column_and_pitch():
    f = make_flow(n_players=3, opts={"startColumn": "20", "columnPitch": "20"})
    f.layout()
    assert [p.column for p in f.players] == [20, 40, 60]
    assert f.get_total_width() == 3 * 20 + 20 + 20


@pytest.mark.unit
def test_flow_layout__total_width_formula():
    f = make_flow(n_players=2)
    f.layout()
    assert f.get_total_width() == 40  # 2*10 + 10 + 10


@pytest.mark.unit
def test_flow_layout__top_label_off_keeps_start_line_at_4():
    f = make_flow(opts={"topLabel": "off"})
    f.layout()
    assert f.start_line == 4
    assert [m.line for m in f.messages] == [4, 8]


@pytest.mark.unit
def test_flow_layout__start_line_override_plus_captions():
    f = make_flow(opts={"startLine": "0"})
    f.layout()
    assert f.get_start_line() == 1  # 0 + guy_caption_lines 1
    assert [m.line for m in f.messages] == [1, 5]
    assert f.get_total_height() == 9  # 5 + line_pitch 4


@pytest.mark.unit
def test_flow_layout__caption_height_is_the_max_player_caption():
    f = make_flow(n_players=2, captions=("A^B", "C^D^E"))
    f.layout()
    assert f.guy_caption_lines == 3
    assert f.get_header_height() == 3
    assert f.start_line == 4 + 3
    assert [m.line for m in f.messages] == [7, 11]


@pytest.mark.unit
def test_flow_layout__guy_caption_lines_zero_without_players():
    f = Flow([], [Message("a", "b", "x")], {})
    f.layout()
    assert f.guy_caption_lines == 0
    assert f.start_line == 4
    assert f.messages[0].line == 4
    assert f.height == 8


@pytest.mark.unit
def test_flow_layout__long_message_caption_shifts_later_lines():
    # DESIGN.md 3.4.0: a caption with length >= linePitch adds length+1-pitch
    f = make_flow(opts={"linePitch": "3"})
    f.messages[0].caption = ["x", "y", "z", "w"]
    f.layout()
    assert [m.line for m in f.messages] == [7, 10]  # 5+(4+1-3)=7; 7+3=10
    assert f.height == 13


@pytest.mark.unit
def test_flow_layout__caption_length_equal_to_pitch_adds_one():
    f = make_flow(opts={"linePitch": "4"})
    f.messages[0].caption = ["a", "b", "c", "d"]
    f.layout()
    assert f.messages[0].line == 6  # 5 + (4+1-4)
    assert f.messages[1].line == 10


@pytest.mark.unit
def test_flow_message_get_length__counts_caption_lines():
    m = Message("a", "b", "one^two^three")
    assert m.get_length() == 3


@pytest.mark.unit
def test_flow_layout__emoji_caption_counts_four_units_in_length():
    # trap 12 at the Flow level: unit strings, len() counts UTF-16 code units
    m = Message("a", "b", to_units("x\U0001f600y"))
    assert m.caption == ["x\ud83d\ude00y"]
    assert len(m.caption[0]) == 4
    assert m.get_length() == 1


@pytest.mark.unit
def test_flow_char_buf__caption_cells_are_indexed_by_units():
    buf = CharBuf(4)
    buf.copy_in(list(to_units("a\U0001f600b")), 0, 4)
    assert buf.slice_string(0, 4) == "a\ud83d\ude00b"


# --- label lines ---------------------------------------------------------------


@pytest.mark.unit
def test_flow_label_line__top_labels_are_0_to_g_minus_1():
    f = make_flow(n_players=2, captions=("A^B^C", "D^E^F"), n_messages=0)
    f.layout()
    assert f.guy_caption_lines == 3
    assert f.get_total_height() == 7
    assert [f.label_line(y) for y in range(3)] == [0, 1, 2]
    assert f.label_line(3) == -1


@pytest.mark.unit
def test_flow_label_line__bottom_formula_counts_up_from_height():
    f = make_flow(
        n_players=2, captions=("A^B^C", "D^E^F"), n_messages=0, opts={"bottomLabel": "on"}
    )
    f.layout()
    h = f.get_total_height()
    assert f.label_line(h - 1) == 1  # G-1-1
    assert f.label_line(h - 2) == 0  # G-1-2
    assert f.label_line(h - 3) == -1


@pytest.mark.unit
def test_flow_label_line__minus_one_when_both_labels_off():
    f = make_flow(
        n_players=2,
        captions=("A^B^C", "D^E^F"),
        n_messages=0,
        opts={"topLabel": "off", "bottomLabel": "off"},
    )
    f.layout()
    for y in range(0, f.get_total_height() + 1):
        assert f.label_line(y) == -1


# --- column_of and numbering --------------------------------------------------


@pytest.mark.unit
def test_flow_column_of__first_match_wins_for_dup_aliases():
    f = Flow([Player("a", "X"), Player("a", "Y"), Player("b", "B")], [Message("a", "b", "m")], {})
    f.layout()
    assert f.column_of("a") == 10
    assert f.column_of("b") == 30


@pytest.mark.unit
def test_flow_column_of__unknown_player_name_raises():
    f = make_flow()
    f.layout()
    with pytest.raises(IllegalArgumentError, match=re.escape("no player named zz")):
        f.column_of("zz")


@pytest.mark.unit
def test_flow_numbering__counts_up_and_resets_per_render():
    f = make_flow(opts={"messageNumbering": "on"})
    f.layout()
    assert f.get_do_numbering() is True
    f.start_message_numbers()
    assert [f.next_message_number() for _ in range(4)] == [1, 2, 3, 4]
    f.start_message_numbers()
    assert f.next_message_number() == 1


@pytest.mark.unit
def test_flow_numbering__minus_one_without_numbering():
    f = make_flow()
    f.layout()
    assert f.next_message_number() == -1
    assert f.get_do_numbering() is False


# --- crunch (should_print) rules ----------------------------------------------


@pytest.mark.unit
def test_flow_should_print__crunch_drops_space_and_bar_only_lines():
    f = make_flow(opts={"crunch": "on"})
    f.layout()
    blank = CharBuf(4)
    blank.copy_in([" ", "|", " ", " "], 0, 4)
    assert not f.should_print(blank)
    bars = CharBuf(2)
    bars.copy_in(["|", "|"], 0, 2)
    assert not f.should_print(bars)
    keep = CharBuf(3)
    keep.copy_in(["a"], 0, 1)
    assert f.should_print(keep)


@pytest.mark.unit
def test_flow_should_print__without_crunch_every_line_prints():
    f = make_flow()
    f.layout()
    blank = CharBuf(4)
    assert f.should_print(blank)  # all NUL: still prints without crunch


# --- VML style getters: the "-" sentinel builds from font and size ------------


@pytest.mark.unit
def test_flow_vml_text_style__sentinel_builds_from_font_and_size():
    f = make_flow()
    f.layout()
    assert f.get_vml_text_style() == (
        "style='FONT-FAMILY:\"courier new\";FONT-SIZE:9pt;V-TEXT-ALIGN:left'"
    )
    assert f.get_vml_box_text_style() == (
        "style='FONT-FAMILY:\"courier new\";FONT-SIZE:9pt;V-TEXT-ALIGN:center'"
    )


@pytest.mark.unit
def test_flow_vml_text_style__present_option_wins_verbatim():
    f = make_flow(opts={"vmlTextStyle": "FONT-FAMILY:Custom;FONT-SIZE:8pt"})
    f.layout()
    assert f.get_vml_text_style() == "FONT-FAMILY:Custom;FONT-SIZE:8pt"


@pytest.mark.unit
def test_flow_vml_text_style__sentinel_tracks_custom_font_and_size():
    f = make_flow(opts={"vmlFont": "Impact", "vmlTextSize": "8"})
    f.layout()
    assert f.get_vml_text_style() == (
        "style='FONT-FAMILY:\"Impact\";FONT-SIZE:8pt;V-TEXT-ALIGN:left'"
    )


@pytest.mark.unit
def test_flow_vml_box_width_percentage__raw_string_and_custom():
    f = make_flow(opts={"vmlBoxWidthPercentage": "42"})
    f.layout()
    assert f.get_vml_box_width_percentage() == "42"  # raw string, parsed at draw time


# --- xml_escape does nothing (DESIGN.md section 3.8 quirk 2) ------------------


@pytest.mark.unit
def test_flow_xml_escape__is_the_identity_method():
    f = Flow([], [], {})
    assert f.xml_escape("a<b>&c") == "a<b>&c"


# --- RunContext: the Java statics (DESIGN-PYTHON.md section 3.5) --------------


@pytest.mark.unit
def test_flow_run_context__defaults_are_the_java_statics():
    ctx = RunContext()
    assert ctx.player_id == 1_000_000
    assert ctx.message_id == 1
    assert ctx.mynum == 0


@pytest.mark.unit
def test_flow_mynum__stagger_alternates_every_other_picture():
    # (ht + 2.0) * (ctx.mynum % 2.0), mynum++ only when stagger is on
    # (DESIGN.md sections 3.4/3.6: SVG, VML and Graffle stagger).
    ctx = RunContext()
    ht = 4.0
    got = []
    for _ in range(3):
        got.append((ht + 2.0) * (ctx.mynum % 2.0))
        ctx.mynum += 1
    assert got == [0.0, 6.0, 0.0]
