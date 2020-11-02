# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from datetime import datetime
import time
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
        self.assertEquals(str(ct), "Some text")
        self.assertEquals(ct.raw_text, "Some ${1}text")
        self.assertEquals(len(ct), 9)
        self.assertEquals(ct.first_colour, None)
        self.assertEquals(ct.last_colour, (1, 0, None))
        self.assertEquals(ct.colour_map[0], (None, None, None))
        
        # Specified start colour
        ct = ColouredText("Some ${1}text", AsciimaticsParser(), colour=(2, 1, 0))
        self.assertEquals(str(ct), "Some text")
        self.assertEquals(ct.raw_text, "Some ${1}text")
        self.assertEquals(len(ct), 9)
        self.assertEquals(ct.first_colour, (2, 1, 0))
        self.assertEquals(ct.last_colour, (1, 0, None))
        self.assertEquals(ct.colour_map[0], (2, 1, 0))

        # Slicing
        self.assertEquals(ct[0], ColouredText("S", AsciimaticsParser()))
        self.assertEquals(ct[1:-1], ColouredText("ome ${1}tex", AsciimaticsParser()))
        self.assertNotEquals(ct[1:-1], ColouredText("ome tex", AsciimaticsParser()))
        self.assertEquals(ct[100:101], ColouredText("", AsciimaticsParser()))

        # Adding
        self.assertEquals(
            ColouredText("Some ", AsciimaticsParser()) +
            ColouredText("${3}Text", AsciimaticsParser()),
            ColouredText("Some ${3}Text", AsciimaticsParser()))

        # Joining
        self.assertEquals(ColouredText(" ", AsciimaticsParser()).join([
            ColouredText("Hello", AsciimaticsParser()),
            ColouredText("${3}World", AsciimaticsParser())]),
            ColouredText("Hello ${3}World", AsciimaticsParser()))

        # Bad data comparisons
        self.assertNotEquals(ct, 1)
        self.assertFalse(ct == "Some text")

        # Startswith
        self.assertTrue(ct.startswith("Some"))
