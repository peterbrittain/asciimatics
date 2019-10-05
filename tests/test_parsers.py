# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import unittest
from asciimatics.parsers import AsciimaticsParser, AnsiTerminalParser, SanitizeParser
import asciimatics.constants as constants


class TestParsers(unittest.TestCase):

    def test_sanitize_parser(self):
        """
        Check SanitizeParser works as expected
        """
        parser = SanitizeParser()
        tokens = parser.parse('a${1}\r${2,3,4}d', None)
        self.assertEquals(next(tokens), ("a", (None, None, None), 0))
        self.assertEquals(next(tokens), ("^", (None, None, None), 1))
        self.assertEquals(next(tokens), ("M", (None, None, None), 6))
        self.assertEquals(next(tokens), ("d", (None, None, None), 7))


    def test_asciimatics_parser(self):
        """
        Check AsciimaticsParser works as expected.
        """
        parser = AsciimaticsParser()
        tokens = parser.parse("a${1}b${2,1}c${3,2,4}de", None)
        self.assertEquals(next(tokens), ("a", (None, None, None), 0))
        self.assertEquals(next(tokens), ("b", (1, 0, None), 1))
        self.assertEquals(next(tokens), ("c", (2, 1, None), 6))
        self.assertEquals(next(tokens), ("d", (3, 2, 4), 13))
        self.assertEquals(next(tokens), ("e", (3, 2, 4), 22))
        with self.assertRaises(StopIteration):
            next(tokens)

    def test_ansi_terminal_parser(self):
        """
        Check AnsiTerminalParser works as expected.
        """
        parser = AnsiTerminalParser()
        tokens = parser.parse("a\x1B[23ab\x1B[0mc\x1B[1md\x1B[2me\x1B[7mf\x1B[27mg\x1B[31;42mh\x1B[m", None)

        # Normal text
        self.assertEquals(next(tokens), ("a", (None, None, None), 0))

        # Unknown escape code
        self.assertEquals(next(tokens), ("b", (None, None, None), 1))

        # Reset
        self.assertEquals(next(tokens), ("c", (7, constants.A_NORMAL, 0), 7))

        # Bold
        self.assertEquals(next(tokens), ("d", (7, constants.A_BOLD, 0), 12))

        # Normal
        self.assertEquals(next(tokens), ("e", (7, constants.A_NORMAL, 0), 17))

        # Inverse
        self.assertEquals(next(tokens), ("f", (7, constants.A_REVERSE, 0), 22))

        # Unset inverse
        self.assertEquals(next(tokens), ("g", (7, constants.A_NORMAL, 0), 27))

        # Standard colours, using multiple parameters
        self.assertEquals(next(tokens), ("h", (constants.COLOUR_RED, constants.A_NORMAL, constants.COLOUR_GREEN), 33))

        # Final escape sequence with no visible text is returned with no text.
        self.assertEquals(next(tokens), (None, (constants.COLOUR_WHITE, constants.A_NORMAL, constants.COLOUR_BLACK), 42))

        with self.assertRaises(StopIteration):
            next(tokens)

        # Special case colour specifications
        tokens = parser.parse("\x1B[38;1ma\x1B[38;5;17mb\x1B[48;2;1;2;3mc\x1B[48;5;54md\x1B[999me", None)

        # Bad colour scheme - ignore
        self.assertEquals(next(tokens), ("a", (None, None, None), 0))

        # Standard colour palette
        self.assertEquals(next(tokens), ("b", (17, None, None), 8))

        # RGB colour scheme - ignore
        self.assertEquals(next(tokens), ("c", (17, None, None), 19))

        # Standard colour palette
        self.assertEquals(next(tokens), ("d", (17, None, 54), 33))

        # Unknown parameter
        self.assertEquals(next(tokens), ("e", (17, None, 54), 44))
