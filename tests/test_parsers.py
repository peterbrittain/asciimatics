import unittest
from asciimatics.parsers import AsciimaticsParser, AnsiTerminalParser, ControlCodeParser, Parser
import asciimatics.constants as constants


class TestParsers(unittest.TestCase):

    def test_controlcode_parser(self):
        """
        Check ControlCodeParser  works as expected
        """
        parser = ControlCodeParser()
        parser.reset("\0\b\ra[", colours=(1, 2, 3))
        tokens = parser.parse()
        self.assertEqual(next(tokens), (0, Parser.CHANGE_COLOURS, (1, 2, 3)))
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "^@"))
        self.assertEqual(next(tokens), (1, Parser.DISPLAY_TEXT, "^H"))
        self.assertEqual(next(tokens), (2, Parser.DISPLAY_TEXT, "^M"))
        self.assertEqual(next(tokens), (3, Parser.DISPLAY_TEXT, "a"))
        self.assertEqual(next(tokens), (4, Parser.DISPLAY_TEXT, "["))

    def test_asciimatics_parser(self):
        """
        Check AsciimaticsParser works as expected.
        """
        parser = AsciimaticsParser()
        parser.reset("a${1}b${2,1}c${3,2,4}de${7}", None)
        tokens = parser.parse()
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "a"))
        self.assertEqual(next(tokens), (1, Parser.CHANGE_COLOURS, (1, 0, None)))
        self.assertEqual(next(tokens), (1, Parser.DISPLAY_TEXT, "b"))
        self.assertEqual(next(tokens), (6, Parser.CHANGE_COLOURS, (2, 1, None)))
        self.assertEqual(next(tokens), (6, Parser.DISPLAY_TEXT, "c"))
        self.assertEqual(next(tokens), (13, Parser.CHANGE_COLOURS, (3, 2, 4)))
        self.assertEqual(next(tokens), (13, Parser.DISPLAY_TEXT, "d"))
        self.assertEqual(next(tokens), (22, Parser.DISPLAY_TEXT, "e"))
        self.assertEqual(next(tokens), (23, Parser.CHANGE_COLOURS, (7, 0, None)))
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
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "a"))

        # Unknown escape code
        self.assertEqual(next(tokens), (1, Parser.DISPLAY_TEXT, "b"))

        # Reset
        self.assertEqual(next(tokens), (7, Parser.CHANGE_COLOURS, (7, constants.A_NORMAL, 0)))
        self.assertEqual(next(tokens), (7, Parser.DISPLAY_TEXT, "c"))

        # Bold
        self.assertEqual(next(tokens), (12, Parser.CHANGE_COLOURS, (7, constants.A_BOLD, 0)))
        self.assertEqual(next(tokens), (12, Parser.DISPLAY_TEXT, "d"))

        # Normal
        self.assertEqual(next(tokens), (17, Parser.CHANGE_COLOURS, (7, constants.A_NORMAL, 0)))
        self.assertEqual(next(tokens), (17, Parser.DISPLAY_TEXT, "e"))

        # Inverse
        self.assertEqual(next(tokens), (22, Parser.CHANGE_COLOURS, (7, constants.A_REVERSE, 0)))
        self.assertEqual(next(tokens), (22, Parser.DISPLAY_TEXT, "f"))

        # Unset inverse
        self.assertEqual(next(tokens), (27, Parser.CHANGE_COLOURS, (7, constants.A_NORMAL, 0)))
        self.assertEqual(next(tokens), (27, Parser.DISPLAY_TEXT, "g"))

        # Standard colours, using multiple parameters
        self.assertEqual(next(tokens), (33, Parser.CHANGE_COLOURS, (constants.COLOUR_RED, constants.A_NORMAL, constants.COLOUR_GREEN)))
        self.assertEqual(next(tokens), (33, Parser.DISPLAY_TEXT, "h"))

        # Final escape sequence with no visible text is returned with no text.
        self.assertEqual(next(tokens), (42, Parser.CHANGE_COLOURS, (constants.COLOUR_WHITE, constants.A_NORMAL, constants.COLOUR_BLACK)))

        with self.assertRaises(StopIteration):
            next(tokens)

    def test_ansi_terminal_parser_def_colours(self):
        """
        Check AnsiTerminalParser default colours work as expected.
        """
        parser = AnsiTerminalParser()
        parser.reset("a\x1B[39mb\x1B[49mc", None)
        tokens = parser.parse()

        # Normal text
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "a"))

        # Default foreground colour
        self.assertEqual(next(tokens), (1, Parser.CHANGE_COLOURS, (constants.COLOUR_DEFAULT, None, None)))
        self.assertEqual(next(tokens), (1, Parser.DISPLAY_TEXT, "b"))

        # Default background colour
        self.assertEqual(next(tokens), (7, Parser.CHANGE_COLOURS, (constants.COLOUR_DEFAULT, None, constants.COLOUR_DEFAULT)))
        self.assertEqual(next(tokens), (7, Parser.DISPLAY_TEXT, "c"))

    def test_ansi_terminal_parser_palette(self):
        """
        Check AnsiTerminalParser colour palettes work as expected.
        """
        parser = AnsiTerminalParser()
        parser.reset(
            "\x1B[38;1ma\x1B[38;5;17mb\x1B[48;2;1;2;3mc\x1B[48;5;54md\x1B[999me\x1B[93m\x1B[104m", None)
        tokens = parser.parse()

        # Bad colour scheme - ignore
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "a"))

        # Standard colour palette
        self.assertEqual(next(tokens), (8, Parser.CHANGE_COLOURS, (17, None, None)))
        self.assertEqual(next(tokens), (8, Parser.DISPLAY_TEXT, "b"))

        # RGB colour scheme - ignore
        self.assertEqual(next(tokens), (19, Parser.DISPLAY_TEXT, "c"))

        # Standard colour palette
        self.assertEqual(next(tokens), (33, Parser.CHANGE_COLOURS, (17, None, 54)))
        self.assertEqual(next(tokens), (33, Parser.DISPLAY_TEXT, "d"))

        # Unknown parameter
        self.assertEqual(next(tokens), (44, Parser.DISPLAY_TEXT, "e"))

        # Intense colour palette
        self.assertEqual(next(tokens), (51, Parser.CHANGE_COLOURS, (11, None, 54)))
        self.assertEqual(next(tokens), (51, Parser.CHANGE_COLOURS, (11, None, 12)))

    def test_ansi_terminal_parser_cursor(self):
        """
        Check AnsiTerminalParser cursor movement work as expected.
        """
        parser = AnsiTerminalParser()
        parser.reset("aa\x08b\rc\x1B[Cdd\x1B[De\x1B[A\x1B[B\x1B[1;2H\x1B[?25h\x1B[?25l\r", None)
        tokens = parser.parse()

        # Normal text...
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "a"))
        self.assertEqual(next(tokens), (1, Parser.DISPLAY_TEXT, "a"))

        # Backspace and overwrite.
        self.assertEqual(next(tokens), (2, Parser.MOVE_RELATIVE, (-1, 0)))
        self.assertEqual(next(tokens), (2, Parser.DISPLAY_TEXT, "b"))

        # Carriage return and overwrite
        self.assertEqual(next(tokens), (4, Parser.MOVE_ABSOLUTE, (0, None)))
        self.assertEqual(next(tokens), (4, Parser.DISPLAY_TEXT, "c"))

        # Move cursor forwards and append.
        self.assertEqual(next(tokens), (6, Parser.MOVE_RELATIVE, (1, 0)))
        self.assertEqual(next(tokens), (6, Parser.DISPLAY_TEXT, "d"))
        self.assertEqual(next(tokens), (10, Parser.DISPLAY_TEXT, "d"))

        # Move cursor backwards and overwrite.
        self.assertEqual(next(tokens), (11, Parser.MOVE_RELATIVE, (-1, 0)))
        self.assertEqual(next(tokens), (11, Parser.DISPLAY_TEXT, "e"))

        # Move cursor up and down.
        self.assertEqual(next(tokens), (15, Parser.MOVE_RELATIVE, (0, -1)))
        self.assertEqual(next(tokens), (15, Parser.MOVE_RELATIVE, (0, 1)))

        # Move cursor to location
        self.assertEqual(next(tokens), (15, Parser.MOVE_ABSOLUTE, (1, 0)))

        # Show/hide cursor
        self.assertEqual(next(tokens), (15, Parser.SHOW_CURSOR, True))
        self.assertEqual(next(tokens), (15, Parser.SHOW_CURSOR, False))

        # Trailing Carriage return
        self.assertEqual(next(tokens), (15, Parser.MOVE_ABSOLUTE, (0, None)))

    def test_ansi_terminal_parser_delete(self):
        """
        Check AnsiTerminalParser delete operations work as expected.
        """
        parser = AnsiTerminalParser()

        # Delete to end of line
        parser.reset("abcde\x08\x08\x08\x1B[K", None)
        tokens = parser.parse()
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "a"))
        self.assertEqual(next(tokens), (1, Parser.DISPLAY_TEXT, "b"))
        self.assertEqual(next(tokens), (2, Parser.DISPLAY_TEXT, "c"))
        self.assertEqual(next(tokens), (3, Parser.DISPLAY_TEXT, "d"))
        self.assertEqual(next(tokens), (4, Parser.DISPLAY_TEXT, "e"))
        self.assertEqual(next(tokens), (5, Parser.MOVE_RELATIVE, (-1, 0)))
        self.assertEqual(next(tokens), (5, Parser.MOVE_RELATIVE, (-1, 0)))
        self.assertEqual(next(tokens), (5, Parser.MOVE_RELATIVE, (-1, 0)))
        self.assertEqual(next(tokens), (5, Parser.DELETE_LINE, 0))
        with self.assertRaises(StopIteration):
            next(tokens)

        # Delete to start of line
        parser.reset("abcde\x1B[1K", None)
        tokens = parser.parse()
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "a"))
        self.assertEqual(next(tokens), (1, Parser.DISPLAY_TEXT, "b"))
        self.assertEqual(next(tokens), (2, Parser.DISPLAY_TEXT, "c"))
        self.assertEqual(next(tokens), (3, Parser.DISPLAY_TEXT, "d"))
        self.assertEqual(next(tokens), (4, Parser.DISPLAY_TEXT, "e"))
        self.assertEqual(next(tokens), (5, Parser.DELETE_LINE, 1))
        with self.assertRaises(StopIteration):
            next(tokens)

        # Delete line
        parser.reset("abcde\x1B[2K", None)
        tokens = parser.parse()
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "a"))
        self.assertEqual(next(tokens), (1, Parser.DISPLAY_TEXT, "b"))
        self.assertEqual(next(tokens), (2, Parser.DISPLAY_TEXT, "c"))
        self.assertEqual(next(tokens), (3, Parser.DISPLAY_TEXT, "d"))
        self.assertEqual(next(tokens), (4, Parser.DISPLAY_TEXT, "e"))
        self.assertEqual(next(tokens), (5, Parser.DELETE_LINE, 2))
        with self.assertRaises(StopIteration):
            next(tokens)

        # Delete char
        parser.reset("abcde\x08\x08\x08\x1B[P", None)
        tokens = parser.parse()
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "a"))
        self.assertEqual(next(tokens), (1, Parser.DISPLAY_TEXT, "b"))
        self.assertEqual(next(tokens), (2, Parser.DISPLAY_TEXT, "c"))
        self.assertEqual(next(tokens), (3, Parser.DISPLAY_TEXT, "d"))
        self.assertEqual(next(tokens), (4, Parser.DISPLAY_TEXT, "e"))
        self.assertEqual(next(tokens), (5, Parser.MOVE_RELATIVE, (-1, 0)))
        self.assertEqual(next(tokens), (5, Parser.MOVE_RELATIVE, (-1, 0)))
        self.assertEqual(next(tokens), (5, Parser.MOVE_RELATIVE, (-1, 0)))
        self.assertEqual(next(tokens), (5, Parser.DELETE_CHARS, 1))
        with self.assertRaises(StopIteration):
            next(tokens)

    def test_ansi_terminal_parser_errors(self):
        """
        Check AnsiTerminalParser handles unsupported encodings gracefully.
        """
        parser = AnsiTerminalParser()
        parser.reset("a\x1BZb\x01c", None)
        tokens = parser.parse()

        # Ignore unknown escape and next letter
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "a"))
        self.assertEqual(next(tokens), (1, Parser.DISPLAY_TEXT, "b"))

        # ANSI art uses control codes for special characters - check we just blank them.
        self.assertEqual(next(tokens), (4, Parser.DISPLAY_TEXT, " "))

        # Back to normal.
        self.assertEqual(next(tokens), (5, Parser.DISPLAY_TEXT, "c"))

    def test_ansi_terminal_parser_tab(self):
        """
        Check AnsiTerminalParser handles tabs.
        """
        parser = AnsiTerminalParser()
        parser.reset("\x09", None)
        tokens = parser.parse()
        self.assertEqual(next(tokens), (0, Parser.NEXT_TAB, None))

    def test_ansi_terminal_parser_clear(self):
        """
        Check AnsiTerminalParser clears screen.
        """
        parser = AnsiTerminalParser()
        parser.reset("\x1B[2J", None)
        tokens = parser.parse()
        self.assertEqual(next(tokens), (0, Parser.CLEAR_SCREEN, None))

    def test_ansi_terminal_parser_os_cmd(self):
        """
        Check AnsiTerminalParser removes OS commands.
        """
        parser = AnsiTerminalParser()
        parser.reset("a\x1B]do something;stuff:to^ignore\x07b", None)
        tokens = parser.parse()
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "a"))
        self.assertEqual(next(tokens), (1, Parser.DISPLAY_TEXT, "b"))

    def test_ansi_terminal_parser_bell(self):
        """
        Check AnsiTerminalParser handles bell.
        """
        parser = AnsiTerminalParser()
        parser.reset("\x07", None)
        tokens = parser.parse()
        with self.assertRaises(StopIteration):
            next(tokens)

    def test_ansi_terminal_parser_start_colour(self):
        """
        Check AnsiTerminalParser uses the starting colours.
        """
        parser = AnsiTerminalParser()
        parser.reset("a", colours=(1,2,3))
        tokens = parser.parse()
        self.assertEqual(next(tokens), (0, Parser.CHANGE_COLOURS, (1, 2, 3)))
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "a"))

    def test_ansi_terminal_parser_unknown(self):
        """
        Check AnsiTerminalParser ignores unknown codes.
        """
        parser = AnsiTerminalParser()
        parser.reset("a\x1B[2345£", None)
        tokens = parser.parse()
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "a"))
        with self.assertRaises(StopIteration):
            next(tokens)

        parser.reset("a\x1B", None)
        tokens = parser.parse()
        self.assertEqual(next(tokens), (0, Parser.DISPLAY_TEXT, "a"))
        with self.assertRaises(StopIteration):
            next(tokens)

