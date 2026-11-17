"""Unit tests for the escape tables of escape.py (DESIGN.md sections
3.10/3.11/3.12, DESIGN-PYTHON.md section 3.7 rule 5).

Copyright (C) 2004 dynamicsoft, Inc.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation; either version 2.1 of the License, or (at
your option) any later version.  A copy of the license is in LICENSE.

Each escape is one character table handed to ``str.translate``, which changes
every character in ONE pass, so escapes it emits are never re-escaped (DESIGN
section 3.10 one-pass rule). The trap rows pinned here are DESIGN-PYTHON.md
section 4.4 rows 16 (``esc_html("'")`` is ``&#39;``, not the ``&#x27;`` of
Python's html.escape) and 17 (``esc_mermaid("#;")`` is ``#35;#59;`` in one
pass).

Arrange/act/assert per test, no shared state, no file access.
"""

import pytest

from callplot.escape import esc_html, esc_mermaid, esc_plantuml

HTML_ROWS = [
    ("amp", "&", "&amp;"),
    ("lt", "<", "&lt;"),
    ("gt", ">", "&gt;"),
    ("quot", '"', "&quot;"),
    ("apos", "'", "&#39;"),  # trap row 16: not the &#x27; of html.escape
    ("plain_a", "a", "a"),
    ("space", " ", " "),
    ("tab", "\t", "\t"),
    ("newline", "\n", "\n"),
    ("slash", "/", "/"),
    ("unicode", "\u00e9", "\u00e9"),
]

MERMAID_ROWS = [
    ("hash", "#", "#35;"),
    ("semi", ";", "#59;"),
    ("lt", "<", "#lt;"),
    ("gt", ">", "#gt;"),
    ("quot", '"', "#quot;"),
    ("amp_kept", "&", "&"),  # mermaid does not escape &
    ("apos_kept", "'", "'"),  # mermaid does not escape '
    ("plain_a", "a", "a"),
    ("colon", ":", ":"),
    ("newline", "\n", "\n"),
    ("unicode", "\u00e9", "\u00e9"),
]

PLANTUML_ROWS = [
    ("quot", '"', "&#34;"),
    ("tilde", "~", "~~"),
    ("star", "*", "~*"),
    ("underscore", "_", "~_"),
    ("slash", "/", "~/"),
    ("dash", "-", "~-"),
    ("lt", "<", "~<"),
    ("lbracket", "[", "~["),
    ("backslash", "\\", "~\\"),
    ("amp_kept", "&", "&"),
    ("gt_kept", ">", ">"),
    ("rbracket_kept", "]", "]"),
    ("plain_a", "a", "a"),
    ("space", " ", " "),
    ("newline", "\n", "\n"),
]


@pytest.mark.unit
def test_escape_html__trapped_apostrophe_entity():
    assert esc_html("'") == "&#39;"
    # Python's html.escape would have written &#x27; (DESIGN-PYTHON 3.4 row):
    assert "&#39;" != "&#x27;"


@pytest.mark.unit
def test_escape_html__amp_is_escaped_first_in_one_pass():
    # translate is one pass: the "&" introduced by &lt; is NOT re-escaped
    assert esc_html("<") == "&lt;"
    assert esc_html("&lt;") == "&amp;lt;"
    assert esc_html("&amp;") == "&amp;amp;"
    assert esc_html("&#39;") == "&amp;#39;"


@pytest.mark.unit
def test_escape_html__combined_special_string():
    src = "a & b < c > d \"e\" 'f'"
    assert esc_html(src) == "a &amp; b &lt; c &gt; d &quot;e&quot; &#39;f&#39;"


@pytest.mark.unit
@pytest.mark.parametrize(("case_id", "src", "want"), HTML_ROWS)
def test_escape_html__table_rows(case_id, src, want):
    assert esc_html(src) == want


@pytest.mark.unit
def test_escape_html__empty_string_unchanged():
    assert esc_html("") == ""


@pytest.mark.unit
def test_escape_mermaid__trap_row_one_pass_hash_semicolon():
    assert esc_mermaid("#;") == "#35;#59;"


@pytest.mark.unit
def test_escape_mermaid__one_pass_never_re_escapes_its_output():
    # the '#' and ';' of "#35;"/"#59;" would be escaped again by a naive loop
    assert esc_mermaid("#35;") == "#35;35#59;"
    assert esc_mermaid("#lt;") == "#35;lt#59;"
    assert esc_mermaid("#") == "#35;"


@pytest.mark.unit
@pytest.mark.parametrize(("case_id", "src", "want"), MERMAID_ROWS)
def test_escape_mermaid__table_rows(case_id, src, want):
    assert esc_mermaid(src) == want


@pytest.mark.unit
def test_escape_mermaid__empty_and_plain_unchanged():
    assert esc_mermaid("") == ""
    assert esc_mermaid("participant-1") == "participant-1"


@pytest.mark.unit
def test_escape_plantuml__quoted_string_becomes_entity():
    # deviation kept from the JS port (escape.py comment, DESIGN.md appendix):
    # the pinned plantuml.jar rejects ~" so " becomes &#34;
    assert esc_plantuml('"') == "&#34;"
    assert esc_plantuml('say "hi"') == "say &#34;hi&#34;"


@pytest.mark.unit
@pytest.mark.parametrize(("case_id", "src", "want"), PLANTUML_ROWS)
def test_escape_plantuml__table_rows(case_id, src, want):
    assert esc_plantuml(src) == want


@pytest.mark.unit
def test_escape_plantuml__tilde_prefix_not_reprocessed():
    # "~*" must not become "~~~*"... it does: '~' -> '~~' and '*' -> '~*';
    # what must NOT happen is re-escaping inside the emitted '~*'
    assert esc_plantuml("*") == "~*"
    assert esc_plantuml("~*") == "~~~*"
    assert esc_plantuml("//") == "~/~/"  # each '/' escaped exactly once


@pytest.mark.unit
def test_escape_plantuml__markup_words_survive():
    assert esc_plantuml("participant") == "participant"
    assert esc_plantuml("a->b") == "a~->b"  # '-' escaped, '>' kept


@pytest.mark.unit
def test_escape_plantuml__backslash_and_brackets():
    assert esc_plantuml(r"\n[x]") == r"~\n~[x]"


@pytest.mark.unit
def test_escape_empty_is_identity_for_all_three():
    assert esc_plantuml("") == ""
    assert esc_mermaid("") == ""
    assert esc_html("") == ""


@pytest.mark.unit
def test_escape__surrogate_pairs_pass_through_untouched():
    # unit strings: surrogate code units are not special in any table
    unit_emoji = "\ud83d\ude00"
    assert esc_html(unit_emoji) == unit_emoji
    assert esc_mermaid(unit_emoji) == unit_emoji
    assert esc_plantuml(unit_emoji) == unit_emoji


@pytest.mark.unit
def test_escape_html__mermaid_and_plantuml_do_not_share_tables():
    # a character escaped by one table is kept by another (tables are distinct)
    assert esc_mermaid("'") == "'"
    assert esc_html("'") == "&#39;"
    assert esc_html("&") == "&amp;"
    assert esc_mermaid("&") == "&"
    assert esc_plantuml(">") == ">"
    assert esc_html(">") == "&gt;"
