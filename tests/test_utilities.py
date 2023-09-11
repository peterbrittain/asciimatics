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
        self.assertEqual("9999", readable_mem(9999))
        self.assertEqual("10K", readable_mem(10240))
        self.assertEqual("1024K", readable_mem(1024*1024))
        self.assertEqual("10M", readable_mem(1024*1024*10))
        self.assertEqual("10G", readable_mem(1024*1024*1024*10))
        self.assertEqual("10T", readable_mem(1024*1024*1024*1024*10))
        self.assertEqual("10P", readable_mem(1024*1024*1024*1024*1024*10))

    def test_readable_timestamp(self):
        """
        Check readable_timestamp works as expected.
        """
        # Check formatting works as expected.
        self.assertEqual("12:01:02AM", readable_timestamp(
            time.mktime(datetime.now().replace(hour=0, minute=1, second=2).timetuple())))
        self.assertEqual("1999-01-02", readable_timestamp(
            time.mktime(datetime.now().replace(year=1999, month=1, day=2).timetuple())))


    def test_boxtool(self):
        # SINGLE_LINE
        tool = BoxTool(True)
        self.assertEqual("┌───┐", tool.box_top(5))
        self.assertEqual("└───┘", tool.box_bottom(5))
        self.assertEqual("│   │", tool.box_line(5))

        self.assertEqual(
            tool.box(5, 3),
            "┌───┐\n" +
            "│   │\n" +
            "└───┘\n")

        # DOUBLE_LINE
        tool.style = DOUBLE_LINE
        self.assertEqual("╔═══╗", tool.box_top(5))
        self.assertEqual("╚═══╝", tool.box_bottom(5))
        self.assertEqual("║   ║", tool.box_line(5))

        self.assertEqual(
            tool.box(5, 3),
            "╔═══╗\n" +
            "║   ║\n" +
            "╚═══╝\n")

        # ASCII_LINE
        tool = BoxTool(False)
        self.assertEqual("+---+", tool.box_top(5))
        self.assertEqual("+---+", tool.box_bottom(5))
        self.assertEqual("|   |", tool.box_line(5))

        self.assertEqual(
            tool.box(5, 3),
            "+---+\n" +
            "|   |\n" +
            "+---+\n")
