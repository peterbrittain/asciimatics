# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from datetime import datetime
import time
import unittest
from asciimatics.constants import ASCII_LINE, SINGLE_LINE, DOUBLE_LINE
from asciimatics.utilities import readable_mem, readable_timestamp, BoxTool


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


    def test_boxtool(self):
        # SINGLE_LINE
        tool = BoxTool(True)
        self.assertEquals("┌───┐", tool.box_top(5))
        self.assertEquals("└───┘", tool.box_bottom(5))
        self.assertEquals("│   │", tool.box_line(5))

        self.assertEquals(
            tool.box(5, 3),
            "┌───┐\n" +
            "│   │\n" +
            "└───┘\n")

        # DOUBLE_LINE
        tool.style = DOUBLE_LINE
        self.assertEquals("╔═══╗", tool.box_top(5))
        self.assertEquals("╚═══╝", tool.box_bottom(5))
        self.assertEquals("║   ║", tool.box_line(5))

        self.assertEquals(
            tool.box(5, 3),
            "╔═══╗\n" +
            "║   ║\n" +
            "╚═══╝\n")

        # ASCII_LINE
        tool = BoxTool(False)
        self.assertEquals("+---+", tool.box_top(5))
        self.assertEquals("+---+", tool.box_bottom(5))
        self.assertEquals("|   |", tool.box_line(5))

        self.assertEquals(
            tool.box(5, 3),
            "+---+\n" +
            "|   |\n" +
            "+---+\n")
