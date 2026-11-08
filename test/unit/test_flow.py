"""Unit tests for options + layout (DESIGN.md sections 3.3, 3.4.0)."""

import os
import unittest

from callplot.parser import parse
from callplot.jcompat import IllegalArgumentError, NumberFormatError, JavaRuntimeException

FIXTURES = os.path.join("test", "fixtures")


def laidOut(name):
    with open(os.path.join(FIXTURES, name), "rb") as fh:
        text = fh.read().decode("utf-8")
    f = parse(text)
    f.layout()
    return f


def readFixture(name):
    with open(os.path.join(FIXTURES, name), "rb") as fh:
        return fh.read().decode("utf-8")


class Flow(unittest.TestCase):
    __test__ = True

    def test_unit_s_fred_layout_W_55_H_29_message_lines_5_to_25_step_4(self):
        f = laidOut("s_fred")
        self.assertEqual(f.getTotalWidth(), 55)
        self.assertEqual(f.getTotalHeight(), 29)
        self.assertEqual([m.line for m in f.messages], [5, 9, 13, 17, 21, 25])
        self.assertEqual([p.column for p in f.players], [10, 25])  # pitch 15

    def test_unit_fred2_layout_G_3_startLine_7_H_31(self):
        f = laidOut("s_fred2")
        self.assertEqual(f.getHeaderHeight(), 3)
        self.assertEqual([m.line for m in f.messages], [7, 11, 15, 19, 23, 27])
        self.assertEqual(f.getTotalHeight(), 31)
        self.assertEqual(f.getTotalWidth(), 55)

    def test_unit_tall_caption_caption_length_at_least_linePitch_shifts_later_lines(self):
        # linePitch 2 -> a 5-line caption: +4
        # player a has 5 caption lines (G=5) -> startLine 4+5=9; one message
        # (length 1) sits at line 9; height 9+2=11
        f = laidOut("tall_caption")
        self.assertEqual([m.line for m in f.messages], [9])
        self.assertEqual(f.getTotalHeight(), 11)

    def test_unit_linePitch_clamps_below_2(self):
        f = laidOut("pitch_clamp")  # linePitch 1 -> 2
        self.assertEqual(f.linePitch, 2)

    def test_unit_option_errors_bad_bool_and_bad_int_throw(self):
        badBool = parse(readFixture("bad_bool"))
        with self.assertRaisesRegex(JavaRuntimeException,
                                    "Bad value for boolean option"):
            badBool.layout()
        badInt = parse(readFixture("bad_int"))
        with self.assertRaisesRegex(NumberFormatError, "For input string"):
            badInt.layout()

    def test_unit_stagger_drives_defaults_startLine_7_and_width_160(self):
        f = laidOut("stagger")
        self.assertEqual(f.stagger, True)
        self.assertEqual(f.getStartLine(), 8)  # 7 (stagger default) + G (1)
        self.assertEqual(f.vmlBoxWidthPercentage, "160")

    def test_unit_labels_labelLine_top_and_bottom_indexes(self):
        f = laidOut("labels_both")  # G=3, top+bottom
        self.assertEqual(f.labelLine(0), 0)
        self.assertEqual(f.labelLine(2), 2)
        self.assertEqual(f.labelLine(3), -1)
        H = f.getTotalHeight()
        self.assertEqual(f.labelLine(H - 1), 1)
        self.assertEqual(f.labelLine(H - 2), 0)
        self.assertEqual(f.labelLine(H - 3), -1)

    def test_unit_labels_none_no_top_or_bottom_labels_anywhere(self):
        f = laidOut("labels_none")
        for y in range(0, f.getTotalHeight() + 1):
            self.assertEqual(f.labelLine(y), -1)

    def test_unit_columnOf_first_match_wins_unknown_throws(self):
        f = laidOut("dup_alias")  # two players named a
        self.assertEqual(f.columnOf("a"), f.players[0].column)
        g = laidOut("s_fred")
        self.assertEqual(g.columnOf("b"), 25)
        with self.assertRaisesRegex(IllegalArgumentError, "no player named z"):
            g.columnOf("z")

    def test_unit_nextMessageNumber_minus_1_without_numbering_then_1_2_3(self):
        plain = laidOut("s_fred")
        self.assertEqual(plain.nextMessageNumber(), -1)
        numbered = laidOut("s_fred_annot")
        numbered.startMessageNumbers()  # renders call this first (Flow.java:317/451)
        self.assertEqual(numbered.nextMessageNumber(), 1)
        self.assertEqual(numbered.nextMessageNumber(), 2)
        self.assertEqual(numbered.nextMessageNumber(), 3)
        numbered.startMessageNumbers()  # per-render reset
        self.assertEqual(numbered.nextMessageNumber(), 1)

    def test_unit_start_overrides_startLine_0_startColumn_20(self):
        f = laidOut("start_overrides")
        self.assertEqual(f.startColumn, 20)
        self.assertEqual(f.startLine, 1)  # 0 + G(1)
        self.assertEqual([m.line for m in f.messages], [1, 5])
        self.assertEqual(f.getTotalHeight(), 9)  # 5 + 4
        self.assertEqual(f.getTotalWidth(), 50)  # 2*10 + 20 + 10

    def test_unit_vmlTextStyle_sentinel_builds_from_font_and_size(self):
        dflt = laidOut("s_fred")
        self.assertEqual(dflt.getVMLTextStyle(),
                         'style=\'FONT-FAMILY:"courier new";'
                         "FONT-SIZE:9pt;V-TEXT-ALIGN:left'")
        self.assertEqual(dflt.getVMLBoxTextStyle(),
                         'style=\'FONT-FAMILY:"courier new";'
                         "FONT-SIZE:9pt;V-TEXT-ALIGN:center'")
        vml = laidOut("vml_styles")
        self.assertEqual(vml.getVMLTextStyle(), "FONT-FAMILY:Custom;FONT-SIZE:8pt")
        self.assertEqual(vml.vmlFont, "Impact")  # vmlFont is a field; Java has no getter
