# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import unittest
from asciimatics.parsers import AsciimaticsParser, AnsiTerminalParser, ControlCodeParser
import asciimatics.constants as constants


class TestParsers(unittest.TestCase):

    def test_controlcode_parser(self):
        """
        Check ControlCodeParser  works as expected
        """
        parser = ControlCodeParser()
        tokens = parser.parse('\0\b\ra[')
        self.assertEquals(next(tokens), "^@")
        self.assertEquals(next(tokens), "^H")
        self.assertEquals(next(tokens), "^M")
        self.assertEquals(next(tokens), "a")
        self.assertEquals(next(tokens), "[")

    def test_asciimatics_parser(self):
        """
        Check AsciimaticsParser works as expected.
        """
        parser = AsciimaticsParser()
        parser.reset("a${1}b${2,1}c${3,2,4}de${7}", None)
        self.assertEquals(parser.normalize(), "a${1}b${2,1}c${3,2,4}de${7}")
        tokens = parser.parse()
        self.assertEquals(next(tokens), ("a", (None, None, None), 0))
        self.assertEquals(next(tokens), ("b", (1, 0, None), 1))
        self.assertEquals(next(tokens), ("c", (2, 1, None), 6))
        self.assertEquals(next(tokens), ("d", (3, 2, 4), 13))
        self.assertEquals(next(tokens), ("e", (3, 2, 4), 22))
        self.assertEquals(next(tokens), (None, (7, 0, None), 23))
        with self.assertRaises(StopIteration):
            next(tokens)

    def test_ansi_terminal_parser_colours(self):
        """
        Check AnsiTerminalParser basic colours work as expected.
        """
        parser = AnsiTerminalParser()
        parser.reset("a\x1B[23ab\x1B[0mc\x1B[1md\x1B[2me\x1B[7mf\x1B[27mg\x1B[31;42mh\x1B[m", None)
        tokens = parser.parse()

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

    def test_ansi_terminal_parser_palette(self):
        """
        Check AnsiTerminalParser colour palettes work as expected.
        """
        parser = AnsiTerminalParser()
        parser.reset("\x1B[38;1ma\x1B[38;5;17mb\x1B[48;2;1;2;3mc\x1B[48;5;54md\x1B[999me", None)
        tokens = parser.parse()

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

    def test_ansi_terminal_parser_cursor(self):
        """
        Check AnsiTerminalParser cursor movement work as expected.
        """
        parser = AnsiTerminalParser()
        parser.reset("aa\x08b\rc\x1B[Cdd\x1B[De\r", None)
        tokens = parser.parse()

        # Carriage return and overwrite
        self.assertEquals(next(tokens), ("c", (None, None, None), 4))

        # Backspace and overwrite.
        self.assertEquals(next(tokens), ("b", (None, None, None), 2))

        # Move cursor forwards and append.
        self.assertEquals(next(tokens), ("d", (None, None, None), 6))

        # Move cursor backwards and overwrite.
        self.assertEquals(next(tokens), ("e", (None, None, None), 11))

        # Normalize returns correct linear form - complete with accurate cursor location.
        self.assertEqual(parser.normalize(), "cbde\x1B[4D")

    def test_ansi_terminal_parser_delete(self):
        """
        Check AnsiTerminalParser delete operations work as expected.
        """
        parser = AnsiTerminalParser()

        # Delete to end of line
        parser.reset("abcde\x08\x08\x08\x1B[K", None)
        tokens = parser.parse()
        self.assertEquals(next(tokens), ("a", (None, None, None), 0))
        self.assertEquals(next(tokens), ("b", (None, None, None), 1))
        self.assertEquals(next(tokens), (None, (None, None, None), 5))
        with self.assertRaises(StopIteration):
            next(tokens)

        # Delete to start of line
        parser.reset("abcde\x08\x08\x08\x1B[1K", None)
        tokens = parser.parse()
        self.assertEquals(next(tokens), (" ", (None, None, None), 8))
        self.assertEquals(next(tokens), (" ", (None, None, None), 8))
        self.assertEquals(next(tokens), ("c", (None, None, None), 2))
        self.assertEquals(next(tokens), ("d", (None, None, None), 3))
        self.assertEquals(next(tokens), ("e", (None, None, None), 4))
        self.assertEquals(next(tokens), (None, (None, None, None), 5))
        with self.assertRaises(StopIteration):
            next(tokens)

        # Delete line
        parser.reset("abcde\x08\x08\x08\x1B[2K", None)
        tokens = parser.parse()
        self.assertEquals(next(tokens), (" ", (None, None, None), 8))
        self.assertEquals(next(tokens), (" ", (None, None, None), 8))
        self.assertEquals(next(tokens), (None, (None, None, None), 5))
        with self.assertRaises(StopIteration):
            next(tokens)

        # Delete char
        parser.reset("abcde\x08\x08\x08\x1B[P", None)
        tokens = parser.parse()
        self.assertEquals(next(tokens), ("a", (None, None, None), 0))
        self.assertEquals(next(tokens), ("b", (None, None, None), 1))
        self.assertEquals(next(tokens), ("d", (None, None, None), 3))
        self.assertEquals(next(tokens), ("e", (None, None, None), 4))
        self.assertEquals(next(tokens), (None, (None, None, None), 5))
        with self.assertRaises(StopIteration):
            next(tokens)

    def test_ansi_terminal_parser_normalization(self):
        """
        Check AnsiTerminalParser normalization works as expected.
        """
        parser = AnsiTerminalParser()

        # SGR0 sets black and white normal text.
        parser.reset("\x1B[ma", None)
        self.assertEquals(parser.normalize(), "\x1B[38;5;7;2;48;5;0ma")

        # SGR1 sets bold and SGR7 reverse video.
        parser.reset("\x1B[1ma\x1B[7mb", None)
        self.assertEquals(parser.normalize(), "\x1B[1ma\x1B[7mb")

    def test_ansi_terminal_parser_errors(self):
        """
        Check AnsiTerminalParser handles unsupported encodings gracefully.
        """
        parser = AnsiTerminalParser()
        parser.reset("a\x1BZb\x07c", None)
        tokens = parser.parse()

        # Ignore unknown escape and next letter
        self.assertEquals(next(tokens), ("a", (None, None, None), 0))
        self.assertEquals(next(tokens), ("b", (None, None, None), 1))

        # Ignore unknown control char
        self.assertEquals(next(tokens), ("c", (None, None, None), 4))
