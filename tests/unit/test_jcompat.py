"""The Java-semantics helpers of jcompat, under test (DESIGN-PYTHON.md
sections 3.2, 3.3, 3.4 and 4.4).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Covers the trap rows 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15 and 20 of
DESIGN-PYTHON.md section 4.4, named after the helper, plus the rest of the
helper surface of DESIGN-PYTHON.md section 3.3: ``to_units``, ``from_units``,
``read_lines``, ``fmt_i``, ``fmt_d``, ``idiv``, ``fdiv``, ``parse_java_int``,
``js_num``, ``js_round``, ``arr_at``, ``java_trim``, ``java_split``, ``tokenize``
and ``CharBuf``. The pinned values are the Java 8 (OpenJDK 1.8.0_504) ones of
DESIGN.md section 3.5, as restated in DESIGN-PYTHON.md sections 3.2 and 3.3,
so a failure here means the port stopped matching the Java original.

Arrange/act/assert in every test, with no shared state: each test builds its
own input. Nothing here touches the file system (DESIGN-PYTHON.md section 4.2,
rule 5: only the command modules do I/O).
"""

import math
import re

import pytest

from callplot.errors import (
    CallplotArithmeticError,
    CallplotError,
    CallplotIndexError,
    NegativeArraySizeError,
    NumberFormatError,
)
from callplot.jcompat import (
    CharBuf,
    arr_at,
    fdiv,
    fmt_d,
    fmt_i,
    from_units,
    idiv,
    java_split,
    java_trim,
    js_num,
    js_round,
    parse_java_int,
    read_lines,
    to_units,
    tokenize,
)
from callplot.parser import SLASH_RE

# "a😀b" as a source escape: 3 Python characters, 4 Java chars (trap row 11).
EMOJI = "a\U0001f600b"

# The 7 rows of the read_lines table of DESIGN-PYTHON.md section 3.2, plus
# Java-extra rows for the never-split control characters.
READ_LINE_ROWS = [
    ("empty__text", "", []),
    ("one_line__a", "a", ["a"]),
    ("trailing_nl__a", "a\n", ["a"]),
    ("blank_last__a", "a\n\n", ["a", ""]),
    ("single_nl", "\n", [""]),
    ("mixed_ends__abc", "a\r\nb\rc", ["a", "b", "c"]),
    ("vt_kept", "a\x0bb", ["a\x0bb"]),
    ("two_cr__two_empty", "\r\r", ["", ""]),
    ("cr_crlf__ab", "a\r\r\nb", ["a", "", "b"]),
    ("formfeed_kept", "a\x0cb", ["a\x0cb"]),
    ("fs_gs_kept", "a\x1c\x1eb", ["a\x1c\x1eb"]),
    ("nel_kept", "a\u0085b", ["a\u0085b"]),
    ("lsep_kept", "a\u2028b", ["a\u2028b"]),
]

# The 15 rows of the fmt_d table: the 12 Java-confirmed rows of DESIGN.md
# section 3.5 (written as floats) plus the 3 rows of DESIGN-PYTHON.md 3.3.
FMT_D_ROWS = [
    ("d50", 50.0, "50.0"),
    ("d0", 0.0, "0.0"),
    ("dm0", -0.0, "-0.0"),
    ("d10p2", 10.2, "10.2"),
    ("dm0p4", -0.4, "-0.4"),
    ("d44p8", 1.6 * 2 * 14, "44.800000000000004"),
    ("d0p001", 0.001, "0.001"),
    ("d1em4", 0.0001, "1.0E-4"),
    ("d9999999", 9999999.0, "9999999.0"),
    ("d1e7", 1e7, "1.0E7"),
    ("d12345678", 12345678.0, "1.2345678E7"),
    ("inf", float("inf"), "Infinity"),
    ("e16", 1e16, "1.0E16"),
    ("e5m5", 1.5e-5, "1.5E-5"),
    ("e17", 123456789012345680.0, "1.2345678901234568E17"),
]

# parse_java_int rows that must raise, with the pinned message text.
PARSE_INT_REJECTS = [
    ("lead_space", " 5", 'For input string: " 5"'),
    ("trail_space", "5 ", 'For input string: "5 "'),
    ("underscore", "1_0", 'For input string: "1_0"'),
    ("arabic_indic_3", "\u0663", 'For input string: "\u0663"'),
    ("arabic_indic_123", "\u0661\u0662\u0663", 'For input string: "\u0661\u0662\u0663"'),
    ("empty", "", 'For input string: ""'),
    ("fullmatch_fails_dot", "5.0", 'For input string: "5.0"'),
    ("hex", "0x5", 'For input string: "0x5"'),
    ("over_int", "2147483648", 'value out of int range: "2147483648"'),
    ("under_int", "-2147483649", 'value out of int range: "-2147483649"'),
]


# --- trap 1: java_trim(" x ") with a non-breaking space: unchanged ---------


@pytest.mark.unit
def test_java_trim__nbsp_kept():
    assert java_trim("\u00a0x\u00a0") == "\u00a0x\u00a0"


@pytest.mark.unit
def test_java_trim__control_and_blank_stripped():
    assert java_trim(" \t x \r\n") == "x"
    assert java_trim("\x00y\x1f") == "y"


@pytest.mark.unit
def test_java_trim__u2000_and_nbsp_not_whitespace():
    # str.strip() would drop these; Java's trim() stops at code > U+0020.
    assert java_trim("\u2000z\u00a0") == "\u2000z\u00a0"
    assert java_trim("\u00a0\u2000") == "\u00a0\u2000"


@pytest.mark.unit
def test_java_trim__inner_whitespace_kept_and_all_blank_empty():
    assert java_trim("a b") == "a b"
    assert java_trim("a\u001f ") == "a"
    assert java_trim("  \t ") == ""


# --- traps 2 and 3: read_lines splits Java's line ends only ---------------


@pytest.mark.unit
@pytest.mark.parametrize(("case_id", "text", "want"), READ_LINE_ROWS)
def test_read_lines__java_readline__ends_are_nl_cr_only(case_id, text, want):
    assert read_lines(to_units(text)) == want


@pytest.mark.unit
def test_read_lines__surrogate_pair__survives_a_line_end():
    assert read_lines(to_units(EMOJI + "\n")) == [to_units(EMOJI)]


@pytest.mark.unit
def test_read_lines__never_splitlines__the_vt_case():
    assert "a\x0bb".splitlines() == ["a", "b"]  # what Python would do
    assert read_lines("a\x0bb") == ["a\x0bb"]  # what Java does


# --- trap 5: parse_java_int is Integer.parseInt, not int() -----------------


@pytest.mark.unit
def test_parse_java_int__leading_plus_and_int_range_ok():
    assert parse_java_int("+7") == 7
    assert parse_java_int("0") == 0
    assert parse_java_int("+007") == 7
    assert parse_java_int("2147483647") == 2147483647
    assert parse_java_int("-2147483648") == -2147483648


@pytest.mark.unit
@pytest.mark.parametrize(("case_id", "text", "message"), PARSE_INT_REJECTS)
def test_parse_java_int__not_an_ascii_int__number_format_error(case_id, text, message):
    with pytest.raises(NumberFormatError, match=re.escape(message)):
        parse_java_int(text)


@pytest.mark.unit
def test_parse_java_int__python_int_accepts_the_java_rejects():
    # DESIGN-PYTHON.md section 3.4, row 5: int(s) is lenient (DESIGN 3.4 trap).
    assert int("1_0") == 10
    assert int(" 5 ") == 5
    assert int("\u0661\u0662\u0663") == 123  # Arabic-Indic digits
    for bad in ("1_0", " 5 ", "\u0661\u0662\u0663"):
        with pytest.raises(NumberFormatError):
            parse_java_int(bad)


# --- traps 6 and 7: Java int / int rounds toward zero, never to -infinity --


@pytest.mark.unit
@pytest.mark.parametrize(
    ("a", "b", "want"),
    [
        (-7, 2, -3),
        (7, -2, -3),
        (7, 2, 3),
        (-7, -2, 3),
        (9, -4, -2),
        (-9, 4, -2),
        (8, -4, -2),
        (1400, 100, 14),
        (0, 5, 0),
        (2**31, -1, -(2**31)),
    ],
)
def test_idiv__java_int_division__toward_zero(a, b, want):
    assert idiv(a, b) == want


@pytest.mark.unit
def test_idiv__python_floor_division__differs_on_negatives():
    assert -7 // 2 == -4  # what Python's // would give (DESIGN 3.4 trap row)
    assert idiv(-7, 2) == -3  # what Java gives


@pytest.mark.unit
def test_idiv__zero_divisor__callplot_arithmetic_error():
    with pytest.raises(CallplotArithmeticError, match=re.escape("/ by zero")):
        idiv(1, 0)


# --- trap 8: double / double follows IEEE 754, it does not raise -----------


@pytest.mark.unit
def test_fdiv__zero_divisors__inf_minus_inf_nan():
    assert fdiv(1.0, 0.0) == math.inf
    assert fdiv(-1.0, 0.0) == -math.inf
    assert fdiv(0.0, 0.0) != fdiv(0.0, 0.0)  # NaN is not equal to itself


@pytest.mark.unit
def test_fdiv__minus_zero__sign_is_a_times_the_zero():
    assert fdiv(1.0, -0.0) == -math.inf
    assert fdiv(-1.0, -0.0) == math.inf
    assert fdiv(0.0, -0.0) != fdiv(0.0, -0.0)  # NaN again
    assert math.isnan(fdiv(float("nan"), 0.0))


@pytest.mark.unit
def test_fdiv__normal_division__plain_python_div():
    assert fdiv(7.0, 2.0) == 3.5
    assert fdiv(-3.0, 2.0) == -1.5


# --- trap 9: fmt_i rejects a bool, which Python's int check would allow -----


@pytest.mark.unit
def test_fmt_i__bool__raises_callplot_error():
    with pytest.raises(CallplotError, match=re.escape("not a Java int")):
        fmt_i(True)
    with pytest.raises(CallplotError, match=re.escape("not a Java int")):
        fmt_i(False)


@pytest.mark.unit
def test_fmt_i__java_ints__print_without_a_decimal_point():
    assert fmt_i(3) == "3"
    assert fmt_i(-3) == "-3"
    assert fmt_i(0) == "0"
    assert fmt_i(1000001) == "1000001"


@pytest.mark.unit
def test_fmt_i__float__raises_callplot_error():
    with pytest.raises(CallplotError, match=re.escape("not a Java int")):
        fmt_i(3.0)


# --- trap 10: fmt_d is Java's Double.toString, not str() -------------------


@pytest.mark.unit
@pytest.mark.parametrize(("case_id", "value", "want"), FMT_D_ROWS)
def test_fmt_d__pinned_rows__java_double_tostring(case_id, value, want):
    assert fmt_d(value) == want


@pytest.mark.unit
def test_fmt_d__minus_infinity_and_nan__java_words():
    assert fmt_d(float("-inf")) == "-Infinity"
    assert fmt_d(float("nan")) == "NaN"


@pytest.mark.unit
def test_fmt_d__float_words__nan_and_infinity_values():
    # float("NaN")/float("Infinity") are the values a "-NaN" opt could carry.
    assert fmt_d(float("NaN")) == "NaN"
    assert fmt_d(float("Infinity")) == "Infinity"
    assert fmt_d(float("-Infinity")) == "-Infinity"


@pytest.mark.unit
def test_fmt_d__negative_sign_before_the_e_form():
    assert fmt_d(-1e7) == "-1.0E7"
    assert fmt_d(-12345678.0) == "-1.2345678E7"


@pytest.mark.unit
def test_fmt_d__int_argument__float_converted():
    assert fmt_d(50) == "50.0"  # accepts int, converts with float(x)


@pytest.mark.unit
def test_fmt_d__not_the_python_str_or_repr_forms():
    assert repr(1e16) == "1e+16"  # what an f-string would emit (DESIGN 3.4 row)
    assert repr(1.5e-5) == "1.5e-05"
    assert fmt_d(1e16) == "1.0E16"
    assert fmt_d(1.5e-5) == "1.5E-5"


# --- trap 11: a character above U+FFFF takes 2 code units in Java ----------


@pytest.mark.unit
def test_to_units__emoji__counts_four_units():
    assert len(to_units(EMOJI)) == 4


@pytest.mark.unit
def test_from_units__emoji__gives_the_original_back():
    assert from_units(to_units(EMOJI)) == EMOJI
    assert from_units(to_units("plain")) == "plain"


@pytest.mark.unit
def test_to_units__code_point_10000_and_10ffff__exact_surrogate_pairs():
    assert to_units("\U00010000") == "\ud800\udc00"
    assert to_units("\U0010ffff") == "\udbff\udfff"
    assert from_units("\ud800\udc00") == "\U00010000"
    assert from_units("\udbff\udfff") == "\U0010ffff"


@pytest.mark.unit
def test_to_units__text_below_u_plus_ffff__returned_unchanged():
    assert to_units("caf\u00e9 \u260e") == "caf\u00e9 \u260e"


# --- from_units: lone surrogates stay lone (they encode to '?') ------------


@pytest.mark.unit
def test_from_units__lone_surrogates__left_alone():
    assert from_units("\ud83d") == "\ud83d"  # lone high
    assert from_units("\udc00") == "\udc00"  # lone low
    assert from_units("\ud83d\ud83d") == "\ud83d\ud83d"  # high then high
    assert from_units("\udc00\ud800") == "\udc00\ud800"  # low then high


# --- trap 15: a lone surrogate writes '?' like Java ------------------------


@pytest.mark.unit
def test_from_units__lone_surrogate__encodes_to_question_mark():
    assert "a\ud83d".encode("utf-8", "replace") == b"a?"
    assert from_units("a\ud83d") == "a\ud83d"  # from_units keeps it lone
    assert "\ud83d\ude00".encode("utf-8", "replace") == b"??"  # two lone units
    assert "a\U0001f600b".encode("utf-8", "replace") == b"a\xf0\x9f\x98\x80b"


# --- traps 13 and 14: CharBuf checks its indexes in code, not in Python ----


@pytest.mark.unit
def test_char_buf__index_minus_one_and_width__callplot_index_error():
    buf = CharBuf(3)
    with pytest.raises(CallplotIndexError, match=re.escape("Index out of range")):
        buf.get(-1)
    with pytest.raises(CallplotIndexError, match=re.escape("Index out of range")):
        buf.get(3)
    with pytest.raises(CallplotIndexError, match=re.escape("Index out of range")):
        buf.set(3, "y")


@pytest.mark.unit
def test_char_buf__negative_width__negative_array_size_error():
    with pytest.raises(NegativeArraySizeError, match=re.escape("-1")):
        CharBuf(-1)
    with pytest.raises(NegativeArraySizeError, match=re.escape("-100")):
        CharBuf(-100)


@pytest.mark.unit
def test_char_buf__fresh_cells__start_as_nul_not_spaces():
    buf = CharBuf(3)
    assert buf.get(0) == "\u0000"
    assert buf.get(2) == "\u0000"


@pytest.mark.unit
def test_char_buf__set_get__roundtrip_inside_the_buffer():
    buf = CharBuf(3)
    buf.set(1, "x")
    assert buf.get(1) == "x"
    assert buf.slice_string(0, 3) == "\u0000x\u0000"


@pytest.mark.unit
def test_char_buf__copy_in__bounds_checked_before_any_write():
    buf = CharBuf(3)
    buf.copy_in(["x", "y"], 1, 2)
    assert buf.slice_string(0, 3) == "\u0000xy"
    other = CharBuf(3)
    for at, n in ((2, 2), (0, 4), (-1, 1), (0, -1)):
        with pytest.raises(CallplotIndexError, match=re.escape("Index out of range")):
            other.copy_in(["z", "z"], at, n)
    assert other.a == ["\u0000", "\u0000", "\u0000"]  # nothing written


@pytest.mark.unit
def test_char_buf__slice_string__out_of_range_through_get():
    buf = CharBuf(2)
    buf.copy_in(["a", "b"], 0, 2)
    assert buf.slice_string(0, 2) == "ab"
    with pytest.raises(CallplotIndexError, match=re.escape("Index out of range")):
        buf.slice_string(1, 2)


# --- arr_at: the helper a missing line field must go through ---------------


@pytest.mark.unit
def test_arr_at__inside__returns_the_field():
    assert arr_at(["a", "b"], 0) == "a"
    assert arr_at(["a", "b"], 1) == "b"


@pytest.mark.unit
def test_arr_at__outside__callplot_index_error():
    with pytest.raises(CallplotIndexError, match=re.escape("Index out of range")):
        arr_at(["a", "b"], 2)
    with pytest.raises(CallplotIndexError, match=re.escape("Index out of range")):
        arr_at(["a", "b"], -1)  # Python's lst[-1] would have given "b"


# --- java_split: Java's String.split, not Python str.split ------------------


@pytest.mark.unit
def test_java_split__plain_slash__pinned_trap_rows():
    slash = re.compile("/")
    assert java_split("///", slash) == []  # trap row 20
    assert java_split("", slash) == [""]  # trap row 20
    assert java_split("a/b/", slash) == ["a", "b"]  # trap row 20
    assert java_split("//", slash) == []
    assert java_split("/a", slash) == ["", "a"]
    assert java_split("a//b", slash) == ["a", "", "b"]


@pytest.mark.unit
def test_java_split__no_match_at_all__returns_the_whole_string():
    assert java_split("abc", re.compile("/")) == ["abc"]
    assert java_split("", re.compile("/")) == [""]


@pytest.mark.unit
def test_java_split__parser_slash_rule__escaped_slash_never_splits():
    rows = [
        ("/", ["/"]),
        ("///", ["/"]),  # position 0 never splits; \/ guards the rest
        ("a->b/x\\/y", ["a->b", "x\\/y"]),
        ("guy/a//cap", ["guy", "a", "", "cap"]),
        ("a->b/x/y/", ["a->b", "x", "y"]),
        ("a\\b", ["a\\b"]),
        ("\\/", ["\\/"]),
        ("guy/a//", ["guy", "a"]),  # trailing empties all dropped
    ]
    for text, want in rows:
        assert java_split(text, SLASH_RE) == want


# --- tokenize: java.util.StringTokenizer drops empty tokens ----------------


@pytest.mark.unit
def test_tokenize__caret_edges__drops_the_empty_tokens():
    assert tokenize("^^a^") == ["a"]
    assert tokenize("") == []
    assert tokenize("a^b^c^") == ["a", "b", "c"]


@pytest.mark.unit
def test_tokenize__other_delimiter__same_rule():
    assert tokenize("a/b", "/") == ["a", "b"]
    assert tokenize("a^-^b") == ["a", "-", "b"]


# --- js_num / js_round (the -html geometry uses JS printing) ---------------


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "want"),
    [(75.0, "75"), (116.5, "116.5"), (3, "3"), (0.0, "0"), (-0.0, "0")],
)
def test_js_num__template_literal_printing(value, want):
    assert js_num(value) == want


@pytest.mark.unit
def test_js_num__bool__raises_callplot_error():
    with pytest.raises(CallplotError, match=re.escape("jsNum: not a number")):
        js_num(True)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "want"),
    [(2.5, 3), (-2.5, -2), (-0.5, 0), (0.5, 1), (0.4999999999, 0), (1.4999, 1)],
)
def test_js_round__half_up_to_plus_infinity(value, want):
    assert js_round(value) == want


@pytest.mark.unit
def test_js_round__differs_from_python_round_on_halves():
    assert round(2.5) == 2  # banker's rounding (DESIGN 3.4 trap row)
    assert js_round(2.5) == 3  # Math.round is floor(x + 0.5)
    assert round(0.5) == 0
    assert js_round(0.5) == 1
