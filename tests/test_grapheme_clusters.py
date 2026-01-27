"""Tests for grapheme cluster handling with wcwidth."""
import unittest
from wcwidth import wcswidth
from asciimatics.widgets.utilities import (
    _enforce_width, _find_min_start, _get_offset, _split_text,
)
from asciimatics.renderers import SpeechBubble

FLAG_CA = "\U0001F1E8\U0001F1E6"
FLAG_US = "\U0001F1FA\U0001F1F8"
FAMILY = "\U0001F468\u200D\U0001F469\u200D\U0001F467"
WAVE_SKIN = "\U0001F44B\U0001F3FB"
CAFE = "cafe\u0301"
CJK = "\u4E2D\u6587"
HEART_VS16 = "\u2764\uFE0F"
HEART = "\u2764"


class TestEnforceWidth(unittest.TestCase):
    """Tests for _enforce_width utility function."""

    def test_ascii_and_cjk(self):
        self.assertEqual(_enforce_width("Hello World", 5), "Hello")
        self.assertEqual(_enforce_width("Short", 10), "Short")
        self.assertEqual(_enforce_width(CJK + "test", 4), CJK)
        self.assertEqual(_enforce_width(CJK, 3), "\u4E2D")

    def test_preserves_grapheme_clusters(self):
        self.assertEqual(_enforce_width("Hi" + FAMILY + "!", 4), "Hi" + FAMILY)
        self.assertEqual(_enforce_width("A" + FLAG_CA + "B", 3), "A" + FLAG_CA)
        self.assertEqual(_enforce_width(CAFE, 4), CAFE)
        self.assertEqual(
            _enforce_width("A" + WAVE_SKIN + "B", 3), "A" + WAVE_SKIN)

    def test_variation_selectors(self):
        self.assertEqual(_enforce_width("A" + HEART_VS16, 3), "A" + HEART_VS16)
        self.assertEqual(_enforce_width("A" + HEART + "B", 2), "A" + HEART)


class TestSplitText(unittest.TestCase):
    """Tests for _split_text utility function."""

    def setUp(self):
        _split_text.cache_clear()

    def test_basic_wrapping(self):
        self.assertEqual(_split_text("hello world", 6, 3), ["hello", "world"])
        self.assertEqual(len(_split_text("line1\nline2", 10, 3)), 2)

    def test_ellipsis_and_long_words(self):
        result = _split_text("line1 line2 line3 line4", 6, 2)
        self.assertEqual(len(result), 2)
        self.assertTrue(result[1].endswith("..."))
        for line in _split_text("superlongword", 5, 3):
            self.assertLessEqual(len(line), 5)

    def test_cjk_width(self):
        for line in _split_text(CJK + CJK + CJK, 4, 10):
            self.assertLessEqual(wcswidth(line), 4)

    def test_preserves_grapheme_clusters(self):
        for line in _split_text(FAMILY + " " + FAMILY, 3, 3):
            if FAMILY[0] in line:
                self.assertIn(FAMILY, line)
        for line in _split_text(FLAG_CA + " " + FLAG_US, 3, 3):
            if "\U0001F1E8" in line:
                self.assertIn(FLAG_CA, line)
            if "\U0001F1FA" in line:
                self.assertIn(FLAG_US, line)


class TestFindMinStart(unittest.TestCase):
    """Tests for _find_min_start utility function."""

    def test_ascii_and_cjk(self):
        self.assertEqual(_find_min_start("Hello", 3), 2)
        self.assertEqual(_find_min_start("Hello", 5), 0)
        self.assertEqual(_find_min_start(CJK, 2), 1)

    def test_preserves_grapheme_clusters(self):
        text = "A" + FAMILY + "B"
        remaining = text[_find_min_start(text, 3):]
        self.assertLessEqual(wcswidth(remaining), 3)
        if FAMILY[0] in remaining:
            self.assertIn(FAMILY, remaining)

    def test_zwj_not_split(self):
        text = "ABC" + FAMILY + "D"
        remaining = text[_find_min_start(text, 3):]
        self.assertNotIn("\u200D", remaining.rstrip(FAMILY + "D"))

    def test_flag_not_split(self):
        text = "ABC" + FLAG_CA + "D"
        remaining = text[_find_min_start(text, 3):]
        for ri in ["\U0001F1E8", "\U0001F1E6"]:
            if ri in remaining:
                self.assertIn(FLAG_CA, remaining)

    def test_cluster_at_start_not_split(self):
        text = FAMILY + "ABCD"
        remaining = text[_find_min_start(text, 4):]
        self.assertNotEqual(remaining[0] if remaining else '', '\u200D')
        text = FLAG_CA + "ABCD"
        remaining = text[_find_min_start(text, 4):]
        self.assertNotEqual(remaining[0] if remaining else '', '\U0001F1E6')


class TestGetOffset(unittest.TestCase):
    """Tests for _get_offset utility function."""

    def test_ascii_and_cjk(self):
        self.assertEqual(_get_offset("Hello", 3), 3)
        self.assertEqual(_get_offset("Hello", 5), 5)
        self.assertEqual(_get_offset(CJK, 2), 1)
        self.assertEqual(_get_offset(CJK, 4), 2)

    def test_preserves_grapheme_clusters(self):
        text = "A" + FAMILY + "B"
        self.assertLessEqual(wcswidth(text[:_get_offset(text, 3)]), 3)

    def test_zwj_not_split(self):
        text = "A" + FAMILY + "B"
        prefix = text[:_get_offset(text, 2)]
        if '\u200D' in prefix:
            self.assertIn(FAMILY, prefix)

    def test_flag_not_split(self):
        text = "A" + FLAG_CA + "B"
        prefix = text[:_get_offset(text, 2)]
        if '\U0001F1E8' in prefix:
            self.assertIn(FLAG_CA, prefix)

    def test_variation_selectors(self):
        text = "A" + HEART_VS16 + "B"
        self.assertLessEqual(wcswidth(text[:_get_offset(text, 3)]), 3)
        text = "A" + HEART + "B"
        self.assertEqual(_get_offset(text, 2), 2)


class TestSpeechBubbleGrapheme(unittest.TestCase):
    """Tests for SpeechBubble with grapheme clusters."""

    def test_alignment(self):
        for text in [FAMILY + "\nHi", CJK + "\nAB"]:
            lines = repr(SpeechBubble(text)).split("\n")
            self.assertEqual(wcswidth(lines[1]), wcswidth(lines[2]))

    def test_mixed_width(self):
        lines = repr(SpeechBubble("Hello\n" + FAMILY + CJK)).split("\n")
        for line in lines[1:-1]:
            if line.startswith("|"):
                self.assertTrue(line.endswith("|"))


if __name__ == "__main__":
    unittest.main()
