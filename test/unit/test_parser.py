"""Unit tests for the parser state machine (DESIGN.md sections 3.1, 3.2)."""

import os
import time
import unittest

from callplot.parser import parse
from callplot.jcompat import IndexError, NullPointerError

FIXTURES = os.path.join("test", "fixtures")


def readFixture(name):
    with open(os.path.join(FIXTURES, name), "rb") as fh:
        return fh.read().decode("utf-8")


class Parser(unittest.TestCase):
    __test__ = True

    def test_unit_s_fred_2_players_6_messages_with_correct_flags(self):
        f = parse(readFixture("s_fred"))
        self.assertEqual(len(f.players), 2)
        self.assertEqual(f.players[0].name, "f")
        self.assertEqual(f.players[0].caption, ["Fred"])
        self.assertEqual(f.players[1].caption, ["Barney"])
        self.assertEqual(len(f.messages), 6)
        p, n, s, r, t, w = f.messages
        self.assertEqual([p.from_, p.to, p.filler, p.arrowFrom, p.arrowTo],
                         ["f", "b", "-", False, True])
        self.assertEqual([n.from_, n.to, n.filler, n.arrowFrom, n.arrowTo],
                         ["b", "b", " ", False, False])
        self.assertEqual([r.from_, r.to, r.filler], ["b", "f", "."])
        self.assertEqual(r.repeatLabel, False)
        self.assertEqual([t.from_, t.to, t.filler], ["f", "b", "-"])  # Thank You
        self.assertEqual(w.arrowTo, True)
        self.assertEqual([w.from_, w.to], ["b", "f"])  # You're Welcome
        self.assertEqual(w.caption, ["You're Welcome"])
        self.assertEqual(t.caption, ["Thank You"])
        self.assertEqual(r.caption, ["RTP"])
        self.assertEqual(s.caption, ["Stuff"])
        self.assertEqual(n.caption, ["Gives bowling ball"])

    def test_unit_dummy_prefix_hidden_note_line_dummy_carries_to_next_message(self):
        f = parse(readFixture("dummy_prefix"))
        self.assertEqual([m.caption[0] for m in f.messages],
                         ["shown", "next", "after"])
        shown = f.messages[0]
        self.assertEqual(shown.comments, ["lost"])
        self.assertEqual(shown.notes, [])
        # hidnote was created with dummy and never pushed; its comment/note lost

    def test_unit_dummy_on_guy_dash_on_guy_line_hides_the_next_message(self):
        f = parse(readFixture("dummy_on_guy"))
        self.assertEqual([p.name for p in f.players], ["c", "a", "b"])
        self.assertEqual([m.caption[0] for m in f.messages], ["y"])

    def test_unit_escapes_backslash_slash_survives_inside_a_field(self):
        f = parse(readFixture("escapes"))
        self.assertEqual(f.messages[0].caption, ["GET home/away"])
        self.assertEqual(f.messages[1].caption, ["200 OK"])
        self.assertEqual([f.messages[1].from_, f.messages[1].to], ["b", "a"])
        self.assertEqual(f.messages[2].caption, ["x/y"])  # note/b/x\/y
        self.assertEqual(f.opts["vmlBoxStyle"], "fillcolor='blue'")

    def test_unit_consecutive_slash_empty_first_caption_kept(self):
        f = parse(readFixture("consecutive_slash"))
        self.assertEqual(len(f.messages), 2)
        # empty caption field digests to no tokens
        self.assertEqual(f.messages[0].caption, [])
        self.assertEqual(f.messages[1].caption, ["second"])

    def test_unit_missing_field_guy_a_throws_IndexError(self):
        with self.assertRaises(IndexError):
            parse(readFixture("missing_field"))

    def test_unit_comment_first_comment_before_any_message_throws(self):
        with self.assertRaises(NullPointerError):
            parse(readFixture("comment_first"))

    def test_unit_leading_ws_whitespace_disables_guy_but_not_arrow_lines(self):
        f = parse(readFixture("leading_ws"))
        self.assertEqual([p.name for p in f.players], ["b", "c"])  # "  guy" never matches
        self.assertEqual(len(f.messages), 1)
        self.assertEqual([f.messages[0].from_, f.messages[0].to], ["b", "c"])

    def test_unit_no_caption_arrow_line_without_fields_creates_no_message(self):
        f = parse(readFixture("no_caption"))
        self.assertEqual(len(f.messages), 0)

    def test_unit_caret_edges_tokenizer_drops_empty_tokens(self):
        f = parse(readFixture("caret_edges"))
        self.assertEqual(f.players[0].caption, ["A"])
        self.assertEqual(f.messages[0].caption, ["x", "y"])
        self.assertEqual(f.messages[0].captionString, 'x" "y')

    def test_unit_option_case_last_put_wins_names_are_case_sensitive(self):
        f = parse(readFixture("option_case"))
        self.assertEqual(f.opts["columnPitch"], "14")
        # lower-case s: an unknown option, but kept in the Map
        self.assertIn("picXsize", f.opts)
        self.assertNotIn("picXSize", f.opts)

    def test_unit_opt_values_are_not_trimmed(self):
        f = parse(readFixture("bad_int"))
        self.assertEqual(f.opts["linePitch"], " 3")

    def test_unit_crlf_and_cr_only_parse_like_s_fred(self):
        for name in ["crlf", "cr_only"]:
            f = parse(readFixture(name))
            self.assertEqual(len(f.players), 2)
            self.assertEqual(len(f.messages), 6)

    def test_unit_self_msg_self_arrow_keeps_arrow_to_and_isSelf(self):
        f = parse(readFixture("self_msg"))
        m = f.messages[0]
        self.assertEqual([m.from_, m.to], ["a", "a"])
        self.assertEqual([m.arrowFrom, m.arrowTo], [False, True])

    def test_unit_dashdash_sets_repeatLabel_dot_does_not_both_fillers_dot(self):
        f = parse(readFixture("dashdash"))
        self.assertEqual([[m.from_, m.to, m.repeatLabel, m.filler]
                          for m in f.messages],
                         [["a", "d", True, "."],
                          ["b", "c", True, "."],
                          ["a", "d", False, "."]])
        self.assertEqual(f.messages[1].caption, ["x", "y"])

    def test_unit_s_fred_annot_notes_and_comments_attach_to_the_last_message(self):
        f = parse(readFixture("s_fred_annot"))
        please = f.messages[0]
        self.assertEqual(please.comments, ['Fred: "Please"'])
        self.assertEqual(please.notes,
                        ["Fred is asking Barney for his bowling ball nicely."])
        self.assertEqual(f.opts["messageNumbering"], "on")
        self.assertEqual(f.opts["links"], "on")

    def test_unit_one_100_000_character_line_parses_in_under_1_s(self):
        text = "guy/a/A\nguy/b/B\na->b/" + "x" * 100000 + "\n"
        t0 = time.time()
        parse(text)
        self.assertLess(time.time() - t0, 1.0, "parse time under 1 s")
