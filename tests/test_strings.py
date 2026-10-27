import unittest
from asciimatics.strings import ColouredText
from asciimatics.parsers import AsciimaticsParser, AnsiTerminalParser


class TestUtilities(unittest.TestCase):

    def test_coloured_text(self):
        """
        Check ColouredText works as expected.
        """
        # No specified start colour
        ct = ColouredText("Some ${1}text", AsciimaticsParser())
        self.assertEqual(str(ct), "Some text")
        self.assertEqual(ct.raw_text, "Some ${1}text")
        self.assertEqual(len(ct), 9)
        self.assertEqual(ct.first_colour, None)
        self.assertEqual(ct.last_colour, (1, 0, None))
        self.assertEqual(ct.colour_map[0], (None, None, None))
        
        # Specified start colour
        ct = ColouredText("Some ${1}text", AsciimaticsParser(), colour=(2, 1, 0))
        self.assertEqual(str(ct), "Some text")
        self.assertEqual(ct.raw_text, "Some ${1}text")
        self.assertEqual(len(ct), 9)
        self.assertEqual(ct.first_colour, (2, 1, 0))
        self.assertEqual(ct.last_colour, (1, 0, None))
        self.assertEqual(ct.colour_map[0], (2, 1, 0))

        # Slicing
        self.assertEqual(ct[0], ColouredText("S", AsciimaticsParser()))
        self.assertEqual(ct[1:-1], ColouredText("ome ${1}tex", AsciimaticsParser()))
        self.assertNotEqual(ct[1:-1], ColouredText("ome tex", AsciimaticsParser()))
        self.assertEqual(ct[100:101], ColouredText("", AsciimaticsParser()))

        # Adding
        self.assertEqual(
            ColouredText("Some ", AsciimaticsParser()) +
            ColouredText("${3}Text", AsciimaticsParser()),
            ColouredText("Some ${3}Text", AsciimaticsParser()))

        # Joining
        self.assertEqual(ColouredText(" ", AsciimaticsParser()).join([
            ColouredText("Hello", AsciimaticsParser()),
            ColouredText("${3}World", AsciimaticsParser())]),
            ColouredText("Hello ${3}World", AsciimaticsParser()))

        # Bad data comparisons
        self.assertNotEqual(ct, 1)
        self.assertFalse(ct == "Some text")

        # Startswith
        self.assertTrue(ct.startswith("Some"))


    def test_negative_coloured_text_indices(self):
        """Negative indices preserve the same raw text and colours as positive ones."""
        cases = [
            ("plain", AsciimaticsParser),
            ("${1}abc", AsciimaticsParser),
            ("a${1}b${2}c", AsciimaticsParser),
            ("${1}x", AsciimaticsParser),
            ("\x1b[31mabc", AnsiTerminalParser),
            ("a\x1b[31mb\x1b[32mc", AnsiTerminalParser),
        ]
        for raw, parser in cases:
            text = ColouredText(raw, parser())
            for index in range(1, len(text) + 1):
                with self.subTest(raw=raw, index=-index):
                    actual = text[-index]
                    expected = text[len(text) - index]
                    self.assertEqual(actual.raw_text, expected.raw_text)
                    self.assertEqual(str(actual), str(expected))
                    self.assertEqual(actual.colour_map, expected.colour_map)
                    self.assertEqual(actual.first_colour, expected.first_colour)
                    self.assertEqual(actual.last_colour, expected.last_colour)
                    self.assertEqual((actual + "!").raw_text,
                                     (expected + "!").raw_text)
                    self.assertEqual(str(actual + "!"), str(expected) + "!")

    def test_coloured_text_index_bounds(self):
        """Normalizing negative indices does not wrap out-of-range values."""
        for raw in ("", "${1}abc"):
            text = ColouredText(raw, AsciimaticsParser())
            for index in (len(text), -len(text) - 1):
                with self.subTest(raw=raw, index=index):
                    with self.assertRaises(IndexError):
                        text[index]
