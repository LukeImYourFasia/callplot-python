"""Unit tests for the parser state machine (DESIGN.md section 3.1, restated
in DESIGN-PYTHON.md sections 3.5 and 4.4).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Pins the parser traps of DESIGN-PYTHON.md section 4.4 row 19 (one 100,000-
character line parses in well under one second) and the state machine rules of
DESIGN.md section 3.8: reply lines alternate and swap from/to, unknown commands
are silently ignored, empty and blank lines are skipped, bad opt values are
kept raw at parse time (the NumberFormatError is Flow's at layout time), and a
missing line field raises CallplotIndexError through ``at``, never a bare
built-in ``IndexError``.

Arrange/act/assert in every test with no shared state: each test builds its
own input text in memory (no fixture files in the unit layer, DESIGN-PYTHON
rule: unit tests test helpers, not golden data).
"""

import re
import time

import pytest

from callplot.errors import CallplotIndexError, NullPointerError
from callplot.model import is_note, is_self, is_undirected
from callplot.parser import at, parse


def msg_fields(messages):
    """A compact snapshot of each message for the assertions below."""
    return [
        (
            m.from_,
            m.to,
            tuple(m.caption),
            m.filler,
            m.arrow_from,
            m.arrow_to,
            m.is_reply,
            m.repeat_label,
            m.src_line,
        )
        for m in messages
    ]


# --- the basic commands ------------------------------------------------------


@pytest.mark.unit
def test_parse__guy_makes_a_player_with_digested_caption():
    f = parse("guy/a/Alice\n")
    assert len(f.players) == 1
    assert f.players[0].name == "a"
    assert f.players[0].caption == ["Alice"]
    assert not f.messages
    assert not f.opts


@pytest.mark.unit
def test_parse__guy_caption_caret_digests_to_lines():
    f = parse("guy/a/A^B^C\n")
    assert f.players[0].caption == ["A", "B", "C"]
    assert f.players[0].caption_string == 'A" "B" "C'


@pytest.mark.unit
def test_parse__note_line_is_self_and_undirected():
    f = parse("guy/a/A\nnote/x/y\n")
    assert len(f.messages) == 1
    m = f.messages[0]
    assert (m.from_, m.to) == ("x", "x")
    assert m.caption == ["y"]
    assert m.filler == " "
    assert (m.arrow_from, m.arrow_to) == (False, False)
    assert is_note(m)
    assert is_self(m)
    assert is_undirected(m)


# --- opt lines: values are raw, later puts win, case matters -----------------


@pytest.mark.unit
def test_parse__opt_values_are_not_trimmed():
    f = parse("guy/a/A\nopt/linePitch/ 3 \n")
    assert f.opts["linePitch"] == " 3 "


@pytest.mark.unit
def test_parse__bad_opt_values_stay_in_the_map_at_parse_time():
    # the NumberFormatError/RuntimeException only fire at layout time (test_flow)
    f = parse("guy/a/A\nopt/linePitch/nonsense\nopt/stagger/maybe\n")
    assert f.opts["linePitch"] == "nonsense"
    assert f.opts["stagger"] == "maybe"


@pytest.mark.unit
def test_parse__opt_later_put_wins_and_names_are_case_sensitive():
    f = parse("guy/a/A\nopt/t/one\nopt/t/two\nopt/Title/T1\nopt/title/T2\n")
    assert f.opts["t"] == "two"
    assert f.opts["Title"] == "T1"
    assert f.opts["title"] == "T2"
    assert set(f.opts) == {"t", "Title", "title"}


@pytest.mark.unit
def test_parse__extra_opt_fields_are_ignored():
    f = parse("guy/a/A\nopt/t/a/b/c\n")
    assert f.opts == {"t": "a"}


@pytest.mark.unit
def test_parse__opt_missing_value_raises_callplot_index_error():
    with pytest.raises(CallplotIndexError, match=re.escape("Index out of range")):
        parse("opt/x\n")
    # and an opt whose value is empty gets dropped by Java's split rule:
    with pytest.raises(CallplotIndexError, match=re.escape("Index out of range")):
        parse("opt/x/\n")


# --- reply lines alternate direction and swap from/to ------------------------


@pytest.mark.unit
def test_parse__reply_line_alternates_and_swaps_from_to():
    f = parse("guy/a/A\nguy/b/B\na->b/hello/goodbye\n")
    assert len(f.messages) == 2
    first, second = f.messages
    assert (first.from_, first.to) == ("a", "b")
    assert first.caption == ["hello"]
    assert not first.is_reply
    assert (second.from_, second.to) == ("b", "a")  # swapped
    assert second.caption == ["goodbye"]
    assert second.is_reply
    assert first.src_line == second.src_line == 3


@pytest.mark.unit
def test_parse__reply_triple_keeps_alternating():
    f = parse("guy/a/A\nguy/b/B\na->b/x/y/z\n")
    assert msg_fields(f.messages) == [
        ("a", "b", ("x",), "-", False, True, False, False, 3),
        ("b", "a", ("y",), "-", False, True, True, False, 3),
        ("a", "b", ("z",), "-", False, True, False, False, 3),
    ]


@pytest.mark.unit
def test_parse__reply_flags_set_before_the_flip():
    # Parser.java:128: is_reply is written from the pre-flip value (DESIGN 3.1)
    f = parse("guy/a/A\nguy/b/B\na->b/p/q/r/s\n")
    assert [m.is_reply for m in f.messages] == [False, True, False, True]


# --- unknown commands are ignored, empty lines are skipped -------------------


@pytest.mark.unit
def test_parse__unknown_command_is_ignored_without_error():
    f = parse("guy/a/A\nbogus line here\nhello world\n")
    assert [p.name for p in f.players] == ["a"]
    assert not f.messages


@pytest.mark.unit
def test_parse__empty_blank_and_hash_lines_are_skipped():
    f = parse("\n   \n# a comment\n#\tguy/a/A\nguy/a/A\n")
    # the tab line starts with '#', so the guy is invisible: only 1 player
    assert [p.name for p in f.players] == ["a"]
    assert len(f.players) == 1


@pytest.mark.unit
def test_parse__hash_inside_a_field_is_not_a_comment():
    f = parse("guy/a/A\nguy/b/B\na->b/#x\n")
    assert f.messages[0].caption == ["#x"]


# --- the missing-field traps: CallplotIndexError, never the built-in --------


@pytest.mark.unit
@pytest.mark.parametrize("text", ["guy/a\n", "note/x\n", "opt/x\n", "guy/a//\n"])
def test_parse__missing_field_raises_callplot_index_error(text):
    with pytest.raises(CallplotIndexError, match=re.escape("Index out of range")):
        parse(text)


@pytest.mark.unit
def test_parse__arrow_line_without_fields_makes_no_message():
    f = parse("guy/a/A\nguy/b/B\na->b\n")
    assert not f.messages  # no caption fields: the while loop never runs


@pytest.mark.unit
def test_parse__dot_line_without_caption_field_raises():
    # the ".." branch always reads at least one caption field (Parser.java:133)
    with pytest.raises(CallplotIndexError, match=re.escape("Index out of range")):
        parse("a..b\n")
    with pytest.raises(CallplotIndexError, match=re.escape("Index out of range")):
        parse("a--b\n")


@pytest.mark.unit
def test_parse__dot_line_extra_fields_are_ignored():
    f = parse("guy/a/A\nguy/b/B\na..b/m/extra\n")
    assert len(f.messages) == 1
    assert f.messages[0].caption == ["m"]


# --- comment/note attachment and the NullPointer traps -----------------------


@pytest.mark.unit
@pytest.mark.parametrize("text", ["!c\n", "!!n\n", "!c\nguy/a/A\n"])
def test_parse__bang_or_bangbang_before_any_message_is_nullpointer(text):
    with pytest.raises(NullPointerError):
        parse(text)


@pytest.mark.unit
def test_parse__bang_alone_adds_an_empty_comment_or_note():
    f = parse("guy/a/A\nguy/b/B\na->b/x\n!\n!!\n")
    m = f.messages[0]
    assert m.comments == [""]
    assert m.notes == [""]


@pytest.mark.unit
def test_parse__comments_and_notes_attach_to_the_last_message():
    f = parse("guy/a/A\nguy/b/B\na->b/x\n!c1\n!!n1\n!c2\n!!n2\n")
    m = f.messages[0]
    assert m.comments == ["c1", "c2"]
    assert m.notes == ["n1", "n2"]


@pytest.mark.unit
def test_parse__bang_lines_do_not_change_src_line_or_make_messages():
    f = parse("guy/a/A\nguy/b/B\na->b/x\n!!n\n")
    assert len(f.messages) == 1
    assert f.messages[0].src_line == 3
    assert f.messages[0].notes == ["n"]


# --- the dash prefix hides exactly the first message of its line -------------


@pytest.mark.unit
def test_parse__dash_hides_only_the_first_message_of_the_line():
    f = parse("guy/a/A\nguy/b/B\n-a->b/h1/h2\n")
    assert msg_fields(f.messages) == [("b", "a", ("h2",), "-", False, True, True, False, 3)]


@pytest.mark.unit
def test_parse__dash_line_then_a_visible_line():
    f = parse("guy/a/A\nguy/b/B\n-a->b/hid\nb->a/vis\n")
    assert [m.caption for m in f.messages] == [["vis"]]
    assert f.messages[0].is_reply is False


# --- whitespace and field slicing quirks -------------------------------------


@pytest.mark.unit
def test_parse__leading_ws_disables_guy_but_not_arrow_lines():
    f = parse(" guy/a/A\n b  ->c/M\n")
    assert [p.name for p in f.players] == []
    assert len(f.messages) == 1
    assert (f.messages[0].from_, f.messages[0].to) == ("b", "c")


@pytest.mark.unit
def test_parse__command_fields_are_not_whitespace_trimmed_at_the_split():
    # " guy" never matches "guy" because the command is the RAW first field
    f = parse("guy/a/A\n guy/x/X\n")
    assert [p.name for p in f.players] == ["a"]


@pytest.mark.unit
def test_parse__dash_slices_the_raw_line_not_the_trimmed_one():
    # Parser.java:69 removes the first char of the RAW line: for " -a->b/x"
    # that drops the space, so the command field keeps its dash and the
    # message's from_ is the odd name "-a" -- but the line is hidden by
    # new_dummy anyway, so no message reaches the flow.
    f = parse("guy/a/A\nguy/b/B\n -a->b/x\nb->a/vis\n")
    assert [m.caption for m in f.messages] == [["vis"]]


@pytest.mark.unit
def test_parse__arrow_from_and_to_are_trimmed_but_names_otherwise_exact():
    f = parse("guy/a/A\nguy/b/B\n a  ->  b /x\n")
    assert (f.messages[0].from_, f.messages[0].to) == ("a", "b")


# --- escaped slashes: unescaped for all fields except the command -----------


@pytest.mark.unit
def test_parse__escaped_slash_survives_inside_a_field():
    f = parse("guy/a/A\nguy/b/B\na->b/GET home\\/away\n")
    assert f.messages[0].caption == ["GET home/away"]


@pytest.mark.unit
def test_parse__escaped_slash_in_a_player_name_or_caption():
    f = parse("guy/a\\/b/Cap\n")
    assert f.players[0].name == "a/b"
    assert f.players[0].caption == ["Cap"]
    g = parse("guy/n/Cap\\/D\n")
    assert g.players[0].name == "n"
    assert g.players[0].caption == ["Cap/D"]


@pytest.mark.unit
def test_parse__command_field_is_never_unescaped():
    f = parse("\\/a->b/x\n")
    assert (f.messages[0].from_, f.messages[0].to) == ("\\/a", "b")


# --- consecutive slashes: the empty caption field is kept --------------------


@pytest.mark.unit
def test_parse__consecutive_slash_empty_first_caption_kept():
    f = parse("guy/a/A\nguy/b/B\na->b//x\n")
    assert len(f.messages) == 2
    assert f.messages[0].caption == []
    assert f.messages[0].get_length() == 0
    assert f.messages[1].caption == ["x"]


# --- src_line counts every raw line, comments and blanks included ------------


@pytest.mark.unit
def test_parse__src_line_counts_blanks_and_comments():
    f = parse("guy/a/A\n# c\n\na->a/x\n")
    assert f.messages[0].src_line == 4
    assert f.messages[0].from_ == f.messages[0].to == "a"


@pytest.mark.unit
def test_parse__reply_messages_share_the_lines_src_line():
    f = parse("guy/a/A\nguy/b/B\n\n\na->b/x/y\n")
    assert [m.src_line for m in f.messages] == [5, 5]


# --- filler rules: .. and -- both use ".", -- sets repeat_label --------------


@pytest.mark.unit
def test_parse__dot_filler_and_dashdash_repeat_label():
    f = parse("guy/a/A\nguy/b/B\na..b/m1\na--b/m2\n")
    one, two = f.messages
    assert (one.filler, one.repeat_label) == (".", False)
    assert (two.filler, two.repeat_label) == (".", True)
    assert is_undirected(one)
    assert is_undirected(two)


@pytest.mark.unit
def test_parse__arrow_line_never_sets_repeat_label_or_dot_filler():
    f = parse("guy/a/A\nguy/b/B\na->b/m\n")
    assert f.messages[0].filler == "-"
    assert not f.messages[0].repeat_label
    assert not is_undirected(f.messages[0])  # arrow_to True


# --- no trailing newline still parses ----------------------------------------


@pytest.mark.unit
def test_parse__no_trailing_newline_parses_the_last_line():
    f = parse("guy/a/A")
    assert [p.name for p in f.players] == ["a"]


@pytest.mark.unit
def test_parse__crlf_and_cr_parse_like_the_lf_form():
    f = parse("guy/a/A\r\nguy/b/B\ra->b/x\r\n")
    assert [p.name for p in f.players] == ["a", "b"]
    assert len(f.messages) == 1
    assert f.messages[0].src_line == 3  # the CR-only line still counts


# --- trap 19: one 100,000-character line parses in well under one second -----


@pytest.mark.unit
def test_parse__one_hundred_thousand_char_line__under_one_second():
    text = "guy/a/A\nguy/b/B\na->b/" + "x" * 100_000 + "\n"
    start = time.time()
    f = parse(text)
    elapsed = time.time() - start
    assert elapsed < 1.0
    assert len(f.messages) == 1
    assert len(f.messages[0].caption[0]) == 100_000


@pytest.mark.unit
def test_parse__one_hundred_thousand_char_unknown_line__under_one_second():
    text = "z" * 100_000 + "\n"
    start = time.time()
    f = parse(text)
    elapsed = time.time() - start
    assert elapsed < 1.0
    assert not f.players
    assert not f.messages
    assert not f.opts


# --- the at() helper itself ---------------------------------------------------


@pytest.mark.unit
def test_at__inside_returns_the_field():
    assert at(["guy", "a"], 0) == "guy"
    assert at(["guy", "a"], 1) == "a"


@pytest.mark.unit
def test_at__outside_or_negative_raises_callplot_index_error():
    with pytest.raises(CallplotIndexError, match=re.escape("Index out of range")):
        at(["guy", "a"], 2)
    with pytest.raises(CallplotIndexError, match=re.escape("Index out of range")):
        at(["guy", "a"], -1)
