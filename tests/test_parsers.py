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
        parser.reset("\0\b\ra[", None)
        tokens = parser.parse()
        self.assertEquals(next(tokens), ("^@", 0, None, None))
        self.assertEquals(next(tokens), ("^H", 1, None, None))
        self.assertEquals(next(tokens), ("^M", 2, None, None))
        self.assertEquals(next(tokens), ("a", 3, None, None))
        self.assertEquals(next(tokens), ("[", 4, None, None))

    def test_asciimatics_parser(self):
        """
        Check AsciimaticsParser works as expected.
        """
        parser = AsciimaticsParser()
        parser.reset("a${1}b${2,1}c${3,2,4}de${7}", None)
        tokens = parser.parse()
        self.assertEquals(next(tokens), ("a", 0, None, None))
        self.assertEquals(next(tokens), (None, 1, 1, (1, 0, None)))
        self.assertEquals(next(tokens), ("b", 1, None, None))
        self.assertEquals(next(tokens), (None, 6, 1, (2, 1, None)))
        self.assertEquals(next(tokens), ("c", 6, None, None))
        self.assertEquals(next(tokens), (None, 13, 1, (3, 2, 4)))
        self.assertEquals(next(tokens), ("d", 13, None, None))
        self.assertEquals(next(tokens), ("e", 22, None, None))
        self.assertEquals(next(tokens), (None, 23, 1, (7, 0, None)))
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
        self.assertEquals(next(tokens), ("a", 0, None, None))

        # Unknown escape code
        self.assertEquals(next(tokens), ("b", 1, None, None))

        # Reset
        self.assertEquals(next(tokens), (None, 7, 1, (7, constants.A_NORMAL, 0)))
        self.assertEquals(next(tokens), ("c", 7, None, None))

        # Bold
        self.assertEquals(next(tokens), (None, 12, 1, (7, constants.A_BOLD, 0)))
        self.assertEquals(next(tokens), ("d", 12, None, None))

        # Normal
        self.assertEquals(next(tokens), (None, 17, 1, (7, constants.A_NORMAL, 0)))
        self.assertEquals(next(tokens), ("e", 17, None, None))

        # Inverse
        self.assertEquals(next(tokens), (None, 22, 1, (7, constants.A_REVERSE, 0)))
        self.assertEquals(next(tokens), ("f", 22, None, None))

        # Unset inverse
        self.assertEquals(next(tokens), (None, 27, 1, (7, constants.A_NORMAL, 0)))
        self.assertEquals(next(tokens), ("g", 27, None, None))

        # Standard colours, using multiple parameters
        self.assertEquals(next(tokens), (None, 33, 1, (constants.COLOUR_RED, constants.A_NORMAL, constants.COLOUR_GREEN)))
        self.assertEquals(next(tokens), ("h", 33, None, None))

        # Final escape sequence with no visible text is returned with no text.
        self.assertEquals(next(tokens), (None, 42, 1, (constants.COLOUR_WHITE, constants.A_NORMAL, constants.COLOUR_BLACK)))

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
        self.assertEquals(next(tokens), ("a", 0, None, None))

        # Standard colour palette
        self.assertEquals(next(tokens), (None, 8, 1, (17, None, None)))
        self.assertEquals(next(tokens), ("b", 8, None, None))

        # RGB colour scheme - ignore
        self.assertEquals(next(tokens), ("c", 19, None, None))

        # Standard colour palette
        self.assertEquals(next(tokens), (None, 33, 1, (17, None, 54)))
        self.assertEquals(next(tokens), ("d", 33, None, None))

        # Unknown parameter
        self.assertEquals(next(tokens), ("e", 44, None, None))

    def test_ansi_terminal_parser_cursor(self):
        """
        Check AnsiTerminalParser cursor movement work as expected.
        """
        parser = AnsiTerminalParser()
        parser.reset("aa\x08b\rc\x1B[Cdd\x1B[De\r", None)
        tokens = parser.parse()

        # Normal text...
        self.assertEquals(next(tokens), ("a", 0, None, None))
        self.assertEquals(next(tokens), ("a", 1, None, None))

        # Backspace and overwrite.
        self.assertEquals(next(tokens), (None, 2, 3, (-1, 0)))
        self.assertEquals(next(tokens), ("b", 2, None, None))

        # Carriage return and overwrite
        self.assertEquals(next(tokens), (None, 4, 2, (0, None)))
        self.assertEquals(next(tokens), ("c", 4, None, None))

        # Move cursor forwards and append.
        self.assertEquals(next(tokens), (None, 6, 3, (1, 0)))
        self.assertEquals(next(tokens), ("d", 6, None, None))
        self.assertEquals(next(tokens), ("d", 10, None, None))

        # Move cursor backwards and overwrite.
        self.assertEquals(next(tokens), (None, 11, 3, (-1, 0)))
        self.assertEquals(next(tokens), ("e", 11, None, None))

        # Trailing Carriage return
        self.assertEquals(next(tokens), (None, 15, 2, (0, None)))

    def test_ansi_terminal_parser_delete(self):
        """
        Check AnsiTerminalParser delete operations work as expected.
        """
        parser = AnsiTerminalParser()

        # Delete to end of line
        parser.reset("abcde\x08\x08\x08\x1B[K", None)
        tokens = parser.parse()
        self.assertEquals(next(tokens), ("a", 0, None, None))
        self.assertEquals(next(tokens), ("b", 1, None, None))
        self.assertEquals(next(tokens), ("c", 2, None, None))
        self.assertEquals(next(tokens), ("d", 3, None, None))
        self.assertEquals(next(tokens), ("e", 4, None, None))
        self.assertEquals(next(tokens), (None, 5, 3, (-1, 0)))
        self.assertEquals(next(tokens), (None, 5, 3, (-1, 0)))
        self.assertEquals(next(tokens), (None, 5, 3, (-1, 0)))
        self.assertEquals(next(tokens), (None, 5, 4, 0))
        with self.assertRaises(StopIteration):
            next(tokens)

        # Delete to start of line
        parser.reset("abcde\x08\x08\x08\x1B[1K", None)
        tokens = parser.parse()
        self.assertEquals(next(tokens), ("a", 0, None, None))
        self.assertEquals(next(tokens), ("b", 1, None, None))
        self.assertEquals(next(tokens), ("c", 2, None, None))
        self.assertEquals(next(tokens), ("d", 3, None, None))
        self.assertEquals(next(tokens), ("e", 4, None, None))
        self.assertEquals(next(tokens), (None, 5, 3, (-1, 0)))
        self.assertEquals(next(tokens), (None, 5, 3, (-1, 0)))
        self.assertEquals(next(tokens), (None, 5, 3, (-1, 0)))
        self.assertEquals(next(tokens), (None, 5, 4, 1))
        with self.assertRaises(StopIteration):
            next(tokens)

        # Delete line
        parser.reset("abcde\x08\x08\x08\x1B[2K", None)
        tokens = parser.parse()
        self.assertEquals(next(tokens), ("a", 0, None, None))
        self.assertEquals(next(tokens), ("b", 1, None, None))
        self.assertEquals(next(tokens), ("c", 2, None, None))
        self.assertEquals(next(tokens), ("d", 3, None, None))
        self.assertEquals(next(tokens), ("e", 4, None, None))
        self.assertEquals(next(tokens), (None, 5, 3, (-1, 0)))
        self.assertEquals(next(tokens), (None, 5, 3, (-1, 0)))
        self.assertEquals(next(tokens), (None, 5, 3, (-1, 0)))
        self.assertEquals(next(tokens), (None, 5, 4, 2))
        with self.assertRaises(StopIteration):
            next(tokens)

        # Delete char
        parser.reset("abcde\x08\x08\x08\x1B[P", None)
        tokens = parser.parse()
        self.assertEquals(next(tokens), ("a", 0, None, None))
        self.assertEquals(next(tokens), ("b", 1, None, None))
        self.assertEquals(next(tokens), ("c", 2, None, None))
        self.assertEquals(next(tokens), ("d", 3, None, None))
        self.assertEquals(next(tokens), ("e", 4, None, None))
        self.assertEquals(next(tokens), (None, 5, 3, (-1, 0)))
        self.assertEquals(next(tokens), (None, 5, 3, (-1, 0)))
        self.assertEquals(next(tokens), (None, 5, 3, (-1, 0)))
        self.assertEquals(next(tokens), (None, 5, 5, 1))
        with self.assertRaises(StopIteration):
            next(tokens)

    def test_ansi_terminal_parser_errors(self):
        """
        Check AnsiTerminalParser handles unsupported encodings gracefully.
        """
        parser = AnsiTerminalParser()
        parser.reset("a\x1BZb\x07c", None)
        tokens = parser.parse()

        # Ignore unknown escape and next letter
        self.assertEquals(next(tokens), ("a", 0, None, None))
        self.assertEquals(next(tokens), ("b", 1, None, None))

        # Ignore unknown control char
        self.assertEquals(next(tokens), ("c", 4, None, None))
