import unittest
from asciimatics.strings import ColouredText
from asciimatics.parsers import AsciimaticsParser


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
        sep_space = ColouredText(" ", AsciimaticsParser(), colour=(2, 1, 0))
        ct_joined = sep_space.join(
            iter([
                ColouredText("Hello", AsciimaticsParser()),
                ColouredText("${3}World", AsciimaticsParser())]))
        self.assertEqual(ct_joined.raw_text, "Hello ${3}World")
        self.assertEqual(ct_joined.first_colour, (2, 1, 0))
        self.assertEqual(ct_joined.last_colour, (3, 0, None))
        sep_dash = ColouredText("-", AsciimaticsParser(), colour=(2, 1, 0))
        list_joined = sep_dash.join(["a", "b", "c"])
        self.assertEqual(list_joined.raw_text, "a-b-c")
        self.assertEqual(list_joined.colour_map, [(2, 1, 0)] * 5)
        iter_joined = sep_dash.join(x for x in ["a", "b", "c"])
        self.assertEqual(iter_joined.raw_text, "a-b-c")
        self.assertEqual(iter_joined.colour_map, [(2, 1, 0)] * 5)
        empty_joined = sep_dash.join(iter([]))
        self.assertEqual(empty_joined.raw_text, "")
        self.assertEqual(empty_joined.colour_map, [])

        # Bad data comparisons
        self.assertNotEqual(ct, 1)
        self.assertFalse(ct == "Some text")

        # Startswith
        self.assertTrue(ct.startswith("Some"))
