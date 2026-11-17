"""Unit tests for the IR model of the new outputs (DESIGN.md section 3.9,
DESIGN-PYTHON.md section 2.5).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

build_model(flow) runs after flow.layout() and never changes Flow (DESIGN.md
section 3.9). Pins: the event kind rule (first match wins: note, self, media
repeat, media, reply, message), the alias rule (the FIRST player named X wins
and an unknown name raises the same IllegalArgumentError as Flow.column_of),
the numbering rule (a number only with messageNumbering on, and self/note
events additionally need noteNumbering; ids e1..en never depend on options)
and the title/htmlLayout options passed through raw.

Arrange/act/assert in every test; inputs are built in memory (no fixtures).
"""

import re

import pytest

from callplot.errors import IllegalArgumentError
from callplot.flow import Flow
from callplot.ir import Kind, build_model
from callplot.model import Message, Player, is_note, is_self, is_undirected
from callplot.parser import parse


def model_of(text: str):
    f = parse(text)
    f.layout()
    return build_model(f)


# --- the derived predicates of callplot.model -------------------------------


@pytest.mark.unit
def test_ir_predicates__undirected_arrowed_self_truth_table():
    directed = Message("a", "b", "x", "-", False, True)
    back = Message("a", "b", "x", ".", False, False)
    self_a = Message("a", "a", "x", " ", False, False)
    assert is_undirected(back)
    assert is_undirected(self_a)
    assert not is_undirected(directed)
    assert is_self(self_a)
    assert not is_self(back)
    assert is_note(self_a)
    assert not is_note(back)
    assert not is_note(directed)
    assert not is_self(directed)


# --- the six event kinds, one input each -------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    ("tail", "want"),
    [
        ("note/a/y", "note"),
        ("a->a/s", "self"),
        ("a--b/x", "mediaRepeat"),
        ("a..b/x", "media"),
    ],
)
def test_ir_kind__one_line_per_kind_first_rule(tail, want):
    m = model_of("guy/a/A\nguy/b/B\n" + tail + "\n")
    assert [str(e.kind) for e in m.events] == [want]


@pytest.mark.unit
def test_ir_kind__reply_line_second_event_is_reply():
    m = model_of("guy/a/A\nguy/b/B\na->b/x/y\n")
    assert [str(e.kind) for e in m.events] == ["message", "reply"]
    reply = m.events[1]
    assert (reply.from_, reply.to) != (0, 1)  # swapped: b->a
    assert reply.caption == ["y"]


@pytest.mark.unit
def test_ir_kind__directed_second_line_is_plain_message():
    m = model_of("guy/a/A\nguy/b/B\na->b/x\nb->a/y\n")
    assert [str(e.kind) for e in m.events] == ["message", "message"]


# --- kind precedence traps -----------------------------------------------------


@pytest.mark.unit
def test_ir_precedence__note_beats_self_and_media():
    # a..a is self AND undirected: the note rule comes first (step 4 order)
    m = model_of("guy/a/A\na..a/n\n")
    assert [str(e.kind) for e in m.events] == ["note"]


@pytest.mark.unit
def test_ir_precedence__note_beats_self_on_undirected_self_input():
    # note/a/n is self+undirected too, but made by the note command
    m = model_of("guy/a/A\nnote/a/n\n")
    assert [str(e.kind) for e in m.events] == ["note"]
    assert Kind.NOTE == "note"  # DESIGN.md 3.9 keeps the spelling of the kind


@pytest.mark.unit
def test_ir_precedence__undirected_with_repeat_label_beats_media():
    f = Flow(
        [Player("a", "A"), Player("b", "B")], [Message("a", "b", "r", ".", False, False, True)], {}
    )
    f.layout()
    m = build_model(f)
    assert str(m.events[0].kind) == "mediaRepeat"
    assert is_undirected(f.messages[0])


@pytest.mark.unit
def test_ir_precedence__note_beats_media_repeat_on_self_dashdash():
    # "--a..a" shape: self AND undirected AND repeat -> note still wins first
    msg = Message("a", "a", "r", ".", False, False, True)
    f = Flow([Player("a", "A")], [msg], {})
    f.layout()
    m = build_model(f)
    assert str(m.events[0].kind) == "note"
    assert msg.repeat_label
    assert is_note(msg)


# --- alias rules: first player wins; unknown name raises ----------------------


@pytest.mark.unit
def test_ir_aliases__duplicate_names_keep_both_participants_first_index_wins():
    m = model_of("guy/a/X\nguy/a/Y\nguy/b/B\na->b/m\n")
    assert [(p.alias, p.index) for p in m.participants] == [("a", 0), ("a", 1), ("b", 2)]
    assert m.events[0].from_ == 0  # first "a"
    assert m.events[0].to == 2


@pytest.mark.unit
@pytest.mark.parametrize("tail", ["zz->a/m\n", "a->zz/m\n", "note/zz/m\n"])
def test_ir_aliases__unknown_name_raises_illegal_argument_error(tail):
    m_text = "guy/a/A\n" + tail
    f = parse(m_text)
    f.layout()
    with pytest.raises(IllegalArgumentError, match=re.escape("no player named zz")):
        build_model(f)


# --- numbering: rule (from != to or noteNumbering) and ids -------------------


@pytest.mark.unit
def test_ir_numbering__no_options_means_no_numbers():
    m = model_of("guy/a/A\nguy/b/B\na->b/x\na..b/y\na->a/z\n")
    assert [e.num for e in m.events] == [None, None, None]
    assert [e.id for e in m.events] == ["e1", "e2", "e3"]


@pytest.mark.unit
def test_ir_numbering__message_numbering_skips_self_and_note_events():
    m = model_of(
        "opt/messageNumbering/on\nopt/noteNumbering/off\n"
        "guy/a/A\nguy/b/B\na..b/m\na->a/s\na->a/t\na->b/u\n"
    )
    assert [e.num for e in m.events] == [1, None, None, 2]
    assert [str(e.kind) for e in m.events] == ["media", "self", "self", "message"]
    assert [e.id for e in m.events] == ["e1", "e2", "e3", "e4"]


@pytest.mark.unit
def test_ir_numbering__note_numbering_adds_self_and_note_events():
    m = model_of("opt/messageNumbering/on\nopt/noteNumbering/on\nguy/a/A\na->a/s\nnote/a/n\n")
    assert [e.num for e in m.events] == [1, 2]
    assert [str(e.kind) for e in m.events] == ["self", "note"]


@pytest.mark.unit
def test_ir_numbering__note_numbering_without_message_numbering_does_nothing():
    m = model_of("opt/noteNumbering/on\nguy/a/A\na->a/s\nnote/a/n\n")
    assert [e.num for e in m.events] == [None, None]


@pytest.mark.unit
def test_ir_numbering__reply_events_are_numbered():
    m = model_of("opt/messageNumbering/on\nguy/a/A\nguy/b/B\na->b/x/y\n")
    assert [e.num for e in m.events] == [1, 2]


@pytest.mark.unit
def test_ir_numbering__counter_skips_unnumbered_events():
    m = model_of("opt/messageNumbering/on\nguy/a/A\nguy/b/B\na..a/n\na->b/x\na->a/s\nb->a/y\n")
    assert [e.num for e in m.events] == [None, 1, None, 2]


# --- model options and title: raw pass-through --------------------------------


@pytest.mark.unit
def test_ir_options__title_and_html_layout_are_raw_values_or_none():
    m = model_of("opt/title/My Title\nopt/htmlLayout/sidebyside\nguy/a/A\nguy/b/B\na->b/x\n")
    assert m.title == "My Title"
    assert m.options.html_layout == "sidebyside"
    assert m.options.message_numbering is False
    assert m.options.note_numbering is False


@pytest.mark.unit
def test_ir_options__absent_options_are_none():
    m = model_of("guy/a/A\nguy/b/B\na->b/x\n")
    assert m.title is None
    assert m.options.html_layout is None


@pytest.mark.unit
def test_ir_options__numbering_flags_come_from_the_layout_result():
    m = model_of("opt/messageNumbering/YES\nopt/noteNumbering/Off\nguy/a/A\nguy/b/B\na->b/x\n")
    assert m.options.message_numbering is True
    assert m.options.note_numbering is False


@pytest.mark.unit
def test_ir_empty_flow__empty_model_but_options_present():
    f = Flow([], [], {})
    f.layout()
    m = build_model(f)
    assert m.title is None
    assert m.participants == []
    assert m.events == []
    assert m.options.html_layout is None
    assert m.options.message_numbering is False


# --- events copy caption/notes/comments and keep src_line ---------------------


@pytest.mark.unit
def test_ir_events__lists_are_copies_and_src_line_survives():
    src = Message("a", "b", "c1^c2", "-", False, True)
    src.notes = ["n1"]
    src.comments = ["k1"]
    src.src_line = 9
    src.is_reply = False
    f = Flow([Player("a", "A"), Player("b", "B")], [src], {"title": "T"})
    f.layout()
    m = build_model(f)
    ev = m.events[0]
    assert ev.caption == ["c1", "c2"]
    assert ev.caption is not src.caption
    assert ev.notes == ["n1"]
    assert ev.notes is not src.notes
    assert ev.comments == ["k1"]
    assert ev.comments is not src.comments
    assert ev.src_line == 9
    assert ev.num is None
    assert m.title == "T"


@pytest.mark.unit
def test_ir_build_model__never_changes_the_flow():
    f = parse("guy/a/A\nguy/b/B\na->b/x\n")
    f.layout()
    line_before = f.messages[0].line
    col_before = f.players[0].column
    m = build_model(f)
    assert len(m.events) == 1
    assert f.messages[0].line == line_before
    assert f.players[0].column == col_before
