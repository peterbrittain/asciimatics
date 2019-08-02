# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from datetime import datetime
import time
import unittest
from asciimatics.utilities import readable_mem, readable_timestamp, ColouredText
from asciimatics.parsers import AsciimaticsParser


class TestUtilities(unittest.TestCase):

    def test_readable_mem(self):
        """
        Check readable_mem works as expected.
        """
        # Check formatting works as expected.
        self.assertEquals("9999", readable_mem(9999))
        self.assertEquals("10K", readable_mem(10240))
        self.assertEquals("1024K", readable_mem(1024*1024))
        self.assertEquals("10M", readable_mem(1024*1024*10))
        self.assertEquals("10G", readable_mem(1024*1024*1024*10))
        self.assertEquals("10T", readable_mem(1024*1024*1024*1024*10))
        self.assertEquals("10P", readable_mem(1024*1024*1024*1024*1024*10))

    def test_readable_timestamp(self):
        """
        Check readable_timestamp works as expected.
        """
        # Check formatting works as expected.
        self.assertEquals("12:01:02AM", readable_timestamp(
            time.mktime(datetime.now().replace(hour=0, minute=1, second=2).timetuple())))
        self.assertEquals("1999-01-02", readable_timestamp(
            time.mktime(datetime.now().replace(year=1999, month=1, day=2).timetuple())))

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

        # Adding
        self.assertEquals(
            ColouredText("Some ", AsciimaticsParser()) +
            ColouredText("${3}Text", AsciimaticsParser()),
            ColouredText("Some ${3}Text", AsciimaticsParser()))
