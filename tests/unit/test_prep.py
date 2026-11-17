"""Unit tests for callplot-prep (DESIGN.md section 3.14, DESIGN-PYTHON.md section 3.8).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

The awk semantics are pinned (DESIGN.md section 3.14.1): rules run in file
order, `next` stops the later rules for a line, changing $0 re-splits fields,
and number printing uses OFMT %.6g (``awk_num``). Trap rows here: row 4
(``awk_fields("a\x0bb\xa0c")`` gives ONE field), row 18 (the three ``awk_num``
rows of DESIGN-PYTHON.md section 3.8), and the public core calls ``prep`` /
``prep_debug`` from DESIGN-PYTHON.md sections 2.3 and 3.8: the text is a unit
string inside (to_units first, from_units last) and the core never writes a
file (the awk "debug" file goes through prep_debug to the command).

Arrange/act/assert per test; every trace input is built in memory (the unit
layer reads no fixtures, goldens or samples).
"""

import pytest

from callplot.jcompat import to_units
from callplot.trace_prep import (
    awk_num,
    awk_num_prefix,
    prep,
    prep_debug,
    split_fields,
    to_time,
)

HEADER = [
    "opt/messageNumbering/on",
    "opt/xml/on",
    "opt/crunch/on",
    "opt/links/off",
]


def prep_lines(text, links=False):
    """The prep output split into content lines (it always ends in one \\n)."""
    parts = prep(text, links=links).split("\n")
    if parts and parts[-1] == "":
        parts.pop()
    return parts


# --- the BEGIN header and the links flag -------------------------------------


@pytest.mark.unit
def test_prep__header_is_the_begin_block_always():
    assert prep_lines("") == HEADER
    assert prep_lines("----\n") == HEADER


@pytest.mark.unit
def test_prep__links_flag_only_flips_the_opt_line():
    got = prep_lines("GET /x\n", links=True)
    assert got[:4] == [*HEADER[:3], "opt/links/on"]


# --- rule 1/2: alias lines and command pass-through --------------------------


@pytest.mark.unit
def test_prep__alias_line_makes_a_guy_and_records_the_alias():
    _text, debug = prep_debug("@ 192.1.1.1 Bob\n")
    assert prep_lines("@ 192.1.1.1 Bob\n") == [*HEADER, "guy/Bob/Bob"]
    assert debug == ["[Bob] going into guys"]


@pytest.mark.unit
def test_prep__alias_resolves_a_source_address():
    text = "@ 1.1 Bob\nSource Address 1.1\nMESSAGE /z hi\n"
    got = prep_lines(text)
    assert got[:5] == [*HEADER, "guy/Bob/Bob"]
    assert "Bob->/MESSAGE" in got  # the destination is still unset
    assert "!!Source Address 1.1 (Bob)" in got


@pytest.mark.unit
def test_prep__at_prefixed_passes_command_through():
    assert prep_lines("@guy/c/Charlie\n") == [*HEADER, "guy/c/Charlie"]


# --- rule 3: separator lines are dropped --------------------------------------


@pytest.mark.unit
def test_prep__dashes_separator_is_dropped():
    assert prep_lines("----\n---- extra\n") == HEADER


# --- rules 4/5: the date ladder and the time lines ---------------------------


@pytest.mark.unit
def test_prep__date_line_becomes_the_mdate_comment():
    got = prep_lines("Date 09/11/0926 10:00:05.000 1\nMESSAGE /z hi\n")
    assert "!!Date 09/11/0926 10:00:05.000 1" in got
    assert "->/MESSAGE" in got


@pytest.mark.unit
def test_prep__time_diffs_use_the_t_ladder_and_quirk_one():
    # quirk 1 (DESIGN.md 3.14.3): with lt still empty the "from last" value is
    # the whole time of day, not zero
    got = prep_lines("Date 09/11/0926 10:00:05.000 1\nMESSAGE /z hi\n")
    assert "!!    0 from initial" in got
    assert "!!    300.001 from last" in got


@pytest.mark.unit
def test_prep__date_then_another_date_moves_lt():
    text = "Date 09/11/0926 10:00:05.000 1\nDate 09/11/0926 10:00:09.000 1\nMESSAGE /z hi\n"
    got = prep_lines(text)
    assert "!!Date 09/11/0926 10:00:09.000 1" in got
    # the time-of-day ladder reads the trailing fields: 540.001 - 300.001
    assert "!!    240 from initial" in got
    assert "!!    240 from last" in got


# --- rules 6/7: Source/Destination Address mint letters ----------------------


@pytest.mark.unit
def test_prep__unknown_addresses_mint_letters_and_note_them_in_debug():
    text = "Source Address q1\nDestination Address q2\nMESSAGE /z hi\n"
    got = prep_lines(text)
    assert got[4:6] == ["guy/a/q1", "guy/b/q2"]
    _, debug = prep_debug(text)
    assert debug == ["[q1] not in guys", "[q2] not in guys"]
    assert "a->b/MESSAGE" in got


@pytest.mark.unit
def test_prep__known_address_reuses_its_letter_silently():
    text = "Source Address q1\nDestination Address q2\nDestination Address q1\n"
    got = prep_lines(text)
    assert got[4:6] == ["guy/a/q1", "guy/b/q2"]
    _, debug = prep_debug(text)
    assert len(debug) == 2


@pytest.mark.unit
def test_prep__letter_quirk_past_52_labels_the_letter_is_empty():
    # DESIGN.md 3.14.3 quirk 2: LETTERS has 52 entries; the 53rd gets ""
    text = "".join(f"Source Address x{i}\n" for i in range(53))
    got = prep_lines(text)
    assert got[4] == "guy/a/x0"
    assert got[-1] == "guy//x52"  # the 53rd unknown address: empty letter


# --- rules 8-11: packet request lines ----------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    ("line", "caption"),
    [
        ("MESSAGE /z hi", "MESSAGE"),
        ("GET /x", "GET"),
        ("SIP/2.0 400 Bad", "400 Bad"),
        ("HTTP/1.0 NOPE", "NOPE"),
    ],
)
def test_prep__request_lines_emit_arrow_with_the_right_caption(line, caption):
    text = "Source Address a\nDestination Address b\n" + line + "\n"
    got = prep_lines(text)
    assert "a->b/" + caption in got


@pytest.mark.unit
def test_prep__request_line_also_falls_through_to_rule_16():
    # quirk 4 (DESIGN.md 3.14.3): rules 8-11 have no next, rule 16 still runs
    got = prep_lines("MESSAGE /z hi\n")
    assert "->/MESSAGE" in got
    assert "!MESSAGE /z hi" in got
    # and the empty m_date prints an empty line, plus the two time lines
    assert "!!    0 from initial" in got
    assert "!!    0 from last" in got


@pytest.mark.unit
def test_prep__src_line_parenthesized_only_for_real_names():
    # len(s) > 1: a one-letter minted label gets no "( x )" suffix
    got = prep_lines("Source Address q1\nMESSAGE /z hi\n")
    assert "!!Source Address q1" in got  # s == "a": no parens... see next test
    got2 = prep_lines("@ 1.1 Bob\nSource Address 1.1\nMESSAGE /z hi\n")
    assert "!!Source Address 1.1 (Bob)" in got2


@pytest.mark.unit
def test_prep__dest_line_is_always_parenthesized():
    got = prep_lines("Source Address q1\nDestination Address q2\nMESSAGE /z hi\n")
    assert "!!Destination Address q2 (b)" in got
    assert "!!Source Address q1" in got  # one-letter label: no parens
    assert "!!  ()" not in got


@pytest.mark.unit
def test_prep__unset_dest_prints_the_empty_paren_form():
    got = prep_lines("MESSAGE /z hi\n")
    assert " ()" in got  # m_dest is "": " (" + d + ")" with empty parts


# --- rules 12-15: dash variants print only the hidden message ----------------


@pytest.mark.unit
def test_prep__dash_request_makes_hidden_message_and_falls_through():
    text = "Source Address a\nDestination Address b\n-GET /x\n"
    got = prep_lines(text)
    assert "-a->b/GET" in got
    assert "!-GET /x" in got
    # no message/time block for the dashed request (rules 8-11 did not match)
    assert "!!    0 from initial" not in got


@pytest.mark.unit
def test_prep__dash_request_matches_via_f0_second_char():
    # method_start(f[0][1:]) is the rule test after the dash
    for line in ["-MESSAGE /z", "-SIP/2.0 400 Bad", "-HTTP/1.0 NOPE"]:
        text = "Source Address a\nDestination Address b\n" + line + "\n"
        got = prep_lines(text)
        assert any(entry.startswith("-a->b/") for entry in got)


# --- rule 16: the fallback comment line with esc0 ----------------------------


@pytest.mark.unit
def test_prep__fallback_line_is_escaped_once():
    got = prep_lines("random line & <b>\n")
    assert "!random line &amp; &lt;b&gt;" in got
    # esc0 does & first so entities it introduces are not re-escaped (one pass)
    assert "!!amp;" not in got


@pytest.mark.unit
def test_prep__esc0_ampersand_entity_input_survives_one_pass():
    got = prep_lines("&amp; <x>\n")
    assert "!&amp;amp; &lt;x&gt;" in got


# --- sub("\r","",$0): only the FIRST carriage return is removed ---------------


@pytest.mark.unit
def test_prep__only_the_first_cr_is_removed():
    got = prep_lines("x\ra\rb\n")
    assert "!xa\rb" in got


@pytest.mark.unit
def test_prep__cr_removed_before_the_rules_and_alias_field_cr_stripped():
    got = prep_lines("@ 1.1 Bob\r\nMESSAGE /z hi\n")
    assert "guy/Bob/Bob" in got


# --- awk number helpers (trap row 18) -----------------------------------------


@pytest.mark.unit
def test_awk_num__three_rows_of_section_3_8():
    assert awk_num(3.0) == "3"
    assert awk_num(0.5) == "0.5"


@pytest.mark.unit
def test_awk_num__1234567_5__pinned_exponential_ofmt_form():
    # DESIGN-PYTHON.md section 3.8 row 3; the goldens never reach this range
    # (time-of-day diffs are at most ~86400), so the golden layer stays green.
    assert awk_num(1234567.5) == "1.23457e+06"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "want"),
    [(2.0, "2"), (-2.0, "-2"), (0.0, "0"), (1.25, "1.25"), (3605.0, "3605")],
)
def test_awk_num__whole_and_plain_decimal_forms(value, want):
    assert awk_num(value) == want


@pytest.mark.unit
@pytest.mark.parametrize(
    ("src", "want"),
    [
        (" 12x", 12.0),
        ("x12", 0.0),
        ("+7.5abc", 7.5),
        ("-", 0.0),
        (".5", 0.5),
        ("", 0.0),
        ("1.2.3", 1.2),
        ("\t42", 42.0),
    ],
)
def test_awk_num_prefix__str2num_prefix_rule(src, want):
    assert awk_num_prefix(src) == want


# --- to_time (DESIGN.md section 3.14.2) ---------------------------------------


@pytest.mark.unit
@pytest.mark.parametrize(
    ("src", "want"),
    [
        ("10/11/09 10:00:01.500", 36001.5),
        ("10:00", 10.0),
        ("", 0.0),
        ("61", 0.061),
        ("1:2:3:4", 3723.004),
        ("10.00.01.500", 36001.5),
    ],
)
def test_to_time__replace_split_and_ladder(src, want):
    assert to_time(src) == want


# --- awk fields (trap row 4) ---------------------------------------------------


@pytest.mark.unit
def test_awk_fields__one_field_for_vt_and_nbsp_input():
    # DESIGN-PYTHON 4.4 row 4: awk FS " " splits on blank RUNS only; \x0b
    # and \xa0 are not blanks, so the whole line is ONE field
    fields = split_fields("a\x0bb\xa0c")
    assert fields[0] == "a\x0bb\xa0c"
    assert fields[1:] == ["", "", ""]  # padded to $4 like the awk indexing


@pytest.mark.unit
@pytest.mark.parametrize(
    ("src", "want"),
    [
        ("", ["", "", "", ""]),
        ("x y", ["x", "y", "", ""]),
        ("  a\t b  c d e  ", ["a", "b", "c", "d", "e"]),
        ("tabs\there", ["tabs", "here", "", ""]),
    ],
)
def test_awk_fields__split_on_blank_runs_pad_to_four(src, want):
    assert split_fields(src) == want


# --- prep / prep_debug agreement and the unit-string round trip ---------------


@pytest.mark.unit
def test_prep_debug__same_text_and_the_debug_lines():
    text = "Source Address q1\n@ 1.1 Bob\nMESSAGE /z hi\n"
    got, debug = prep_debug(text)
    assert got == prep(text)
    assert debug == ["[q1] not in guys", "[Bob] going into guys"]


@pytest.mark.unit
def test_prep_debug__empty_trace_has_no_debug_lines():
    got, debug = prep_debug("----\n")
    assert got == prep("----\n")
    assert debug == []


@pytest.mark.unit
def test_prep__emoji_in_the_trace_round_trips_as_one_character():
    got = prep("Destination Address x\U0001f600y\n")
    assert "guy/a/x\U0001f600y" in got  # to_units inside, from_units last
    got2 = prep("a\U0001f600b\n")
    assert "!a\U0001f600b" in got2
    assert len(to_units("x\U0001f600y")) == 4  # 4 unit chars inside


@pytest.mark.unit
def test_prep_debug__debug_lines_also_return_real_characters():
    _, debug = prep_debug("Source Address x\U0001f600y\n")
    assert debug == ["[x\U0001f600y] not in guys"]


@pytest.mark.unit
def test_prep__lone_surrogate_stays_lone_and_encodes_to_question():
    got = prep("!\ud83d\n")
    assert "!!\ud83d" in got  # kept lone by from_units
    assert got.encode("utf-8", "replace").count(b"?") >= 1


@pytest.mark.unit
def test_prep__trailing_newline_does_not_add_an_empty_line():
    assert prep("MESSAGE /z hi\n") == prep("MESSAGE /z hi")


@pytest.mark.unit
def test_prep_core_is_total_for_plain_trace_text():
    text = "".join(
        line + "\n"
        for line in [
            "----",
            "@ 1.1 Bob",
            "Date 09/11/0926 10:00:05.000 1",
            "GET /x",
            "-MESSAGE /z bye",
            "junk & <b>",
        ]
    )
    got, debug = prep_debug(text)
    lines = got.split("\n")
    assert "guy/Bob/Bob" in lines
    # the alias names the address only; s/d stay unset, so the dashed request
    # prints with empty labels and the time lines show the date ladder quirk
    assert "-->/MESSAGE" in lines
    assert "!junk &amp; &lt;b&gt;" in lines
    assert "!!    300.001 from last" in lines
    assert got.startswith("opt/messageNumbering/on\n")
    assert debug == ["[Bob] going into guys"]
