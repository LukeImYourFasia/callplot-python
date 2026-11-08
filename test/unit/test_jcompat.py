"""Unit tests for the jcompat helpers (DESIGN.md section 3.5).

The fmtD rows and the javaSplit edge cases were confirmed against the
reference JVM (OpenJDK 1.8.0_504) when the golden corpus was generated;
see reference/JDK_VERSION.
"""

import re

import unittest

from callplot.jcompat import (fmtI, fmtD, idiv, parseJavaInt, javaTrim,
                             javaSplit, tokenize, CharBuf, CallplotError,
                             NumberFormatError, IndexError, ArithmeticError,
                             NegativeArraySizeError)

SLASH_RE = re.compile(r"(?<=[^\\])/")
PLAIN_SLASH_RE = re.compile(r"/")


class Jcompat(unittest.TestCase):
    __test__ = True

    def test_unit_fmtI_prints_integers_with_no_decimal_point(self):
        self.assertEqual(fmtI(0), "0")
        self.assertEqual(fmtI(-42), "-42")
        self.assertEqual(fmtI(1000001), "1000001")
        with self.assertRaises(CallplotError):
            fmtI(1.5)

    def test_unit_fmtD_matches_the_section_3_5_table(self):
        cases = [
            (50, "50.0"),
            (0, "0.0"),
            (-0.0, "-0.0"),
            (10.2, "10.2"),
            (-0.4, "-0.4"),
            (1.6 * 2 * 14, "44.800000000000004"),
            (0.001, "0.001"),
            (0.0001, "1.0E-4"),
            (9999999, "9999999.0"),
            (1e7, "1.0E7"),
            (12345678, "1.2345678E7"),
            (float("inf"), "Infinity"),
            (float("-inf"), "-Infinity"),
            (float("nan"), "NaN"),
            (0.2 + 15, "15.2"),
            (-0.2 + 9, "8.8"),
            (1.6 * 3 * 14, "67.20000000000002"),
            (16.0 / 6 + 0.25, "2.9166666666666665"),
            (-1 * 21 / 6, "-3.5"),
        ]
        for x, want in cases:
            self.assertEqual(fmtD(x), want, "fmtD(%r)" % x)

    def test_unit_idiv_truncates_toward_zero_and_throws_on_div_0(self):
        self.assertEqual(idiv(7, 2), 3)
        self.assertEqual(idiv(-7, 2), -3)
        self.assertEqual(idiv(14 * 100, 100), 14)
        with self.assertRaises(ArithmeticError) as ctx:
            idiv(1, 0)
        self.assertRegex(str(ctx.exception), r"/ by zero")

    def test_unit_parseJavaInt_is_strict_and_accepts_plus_5(self):
        self.assertEqual(parseJavaInt("5"), 5)
        self.assertEqual(parseJavaInt("+5"), 5)
        self.assertEqual(parseJavaInt("-5"), -5)
        self.assertEqual(parseJavaInt("0"), 0)
        self.assertEqual(parseJavaInt("2147483647"), 2147483647)
        self.assertEqual(parseJavaInt("-2147483648"), -2147483648)
        for bad in ["2147483648", " 5", "5 ", "", "5.0", "0x5"]:
            with self.assertRaises(NumberFormatError):
                parseJavaInt(bad)

    def test_unit_javaTrim_strips_only_code_points_below_0x20(self):
        self.assertEqual(javaTrim(" \t x \r\n"), "x")
        # NBSP kept
        self.assertEqual(javaTrim("\u00a0x\u00a0"), "\u00a0x\u00a0")
        self.assertEqual(javaTrim("a b"), "a b")
        self.assertEqual(javaTrim("\u0000x"), "x")

    def test_unit_javaSplit_follows_Java_exactly(self):
        self.assertEqual(javaSplit("a->b/x/y", SLASH_RE), ["a->b", "x", "y"])
        self.assertEqual(javaSplit("a->b/x\\/y", SLASH_RE), ["a->b", "x\\/y"])
        # trailing empty dropped
        self.assertEqual(javaSplit("guy/a/", SLASH_RE), ["guy", "a"])
        # position 0 never splits (there is no preceding char)
        self.assertEqual(javaSplit("/", SLASH_RE), ["/"])
        self.assertEqual(javaSplit("//", SLASH_RE), ["/"])
        self.assertEqual(javaSplit("///", SLASH_RE), ["/"])
        self.assertEqual(javaSplit("a/b/c", PLAIN_SLASH_RE), ["a", "b", "c"])
        self.assertEqual(javaSplit("a/b/", PLAIN_SLASH_RE), ["a", "b"])
        # Java length-0 array
        self.assertEqual(javaSplit("//", PLAIN_SLASH_RE), [])
        self.assertEqual(javaSplit("/", PLAIN_SLASH_RE), [])
        self.assertEqual(javaSplit("/a", PLAIN_SLASH_RE), ["", "a"])
        self.assertEqual(javaSplit("a//b", PLAIN_SLASH_RE), ["a", "", "b"])
        # no match -> [s]
        self.assertEqual(javaSplit("abc", PLAIN_SLASH_RE), ["abc"])
        self.assertEqual(javaSplit("", PLAIN_SLASH_RE), [""])

    def test_unit_tokenize_drops_empty_tokens(self):
        self.assertEqual(tokenize("^^a^"), ["a"])
        self.assertEqual(tokenize(""), [])
        self.assertEqual(tokenize("a^b"), ["a", "b"])
        self.assertEqual(tokenize("x^^y"), ["x", "y"])

    def test_unit_CharBuf_throws_IndexError_outside_the_buffer(self):
        b = CharBuf(3)
        b.set(0, "x")
        self.assertEqual(b.get(0), "x")
        with self.assertRaises(IndexError):
            b.get(3)
        with self.assertRaises(IndexError):
            b.get(-1)
        with self.assertRaises(IndexError):
            b.set(3, "y")
        with self.assertRaises(NegativeArraySizeError):
            CharBuf(-1)

    def test_unit_CharBuf_copyIn_checks_the_whole_range_before_writing(self):
        b = CharBuf(4)
        b.copyIn("ab", 1, 2)  # legal: fills indices 1..2
        with self.assertRaises(IndexError):
            b.copyIn("abcd", 1, 4)  # 1+4 > 4
        with self.assertRaises(IndexError):
            b.copyIn("ab", -1, 2)
        with self.assertRaises(IndexError):
            b.copyIn("ab", 0, -1)
