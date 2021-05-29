
"""
This module provides parsers to create ColouredText objects from embedded control strings.
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import re
from builtins import str
from future.utils import with_metaclass
from abc import ABCMeta, abstractmethod
from logging import getLogger
import asciimatics.constants as constants
from asciimatics.utilities import _DotDict


# Diagnostic logging
logger = getLogger(__name__)


class Parser(with_metaclass(ABCMeta, object)):
    """
    Abstract class to represent text parsers that extract colour control codes from raw text and
    convert them to displayable text and associated colour maps.
    """

    #: Command to display some text.  Parameter is the text to display
    DISPLAY_TEXT = 0
    #: Command to change active colour tuple.  Parameters are the 3-tuple of (fg, attr, bg)
    CHANGE_COLOURS = 1
    #: Command to move cursor to abs position.  Parameters are (x, y) where each are absolute positions.
    MOVE_ABSOLUTE = 2
    #: Command to move cursor to relative position.  Parameters are (x, y) where each are relative positions.
    MOVE_RELATIVE = 3
    #: Command to delete part of the current line. Params are 0, 1 and 2 for end, start, all.
    DELETE_LINE = 4
    #: Command to delete next N characters from this line.
    DELETE_CHARS = 5
    #: Next tab stop
    NEXT_TAB = 6
    #: Set cursor visibility.  Param is boolean setting True=visible
    SHOW_CURSOR = 7
    #: Clear the screen.  No parameters.
    CLEAR_SCREEN = 8
    #: Save the cursor position.  No parameters.
    SAVE_CURSOR = 9
    #: Restore the cursor position.  No parameters.
    RESTORE_CURSOR = 10

    def __init__(self):
        """
        Initialize the parser.
        """
        self._state = None

    def reset(self, text, colours):
        """
        Reset the parser to analyze the supplied raw text.

        :param text: raw text to process.
        :param colours: colour tuple to initialise the colour map.
        """
        self._state = _DotDict()
        self._state.text = text
        self._state.attributes = colours

    @abstractmethod
    def parse(self):
        """
        Generator to return coloured text from raw text.

        Generally returns a stream of text/color tuple/offset tuples.  If there is a colour update with no
        visible text, the first element of the tuple may be None.

        :returns: a 3-tuple of (start offset in raw text, command to execute, parameters)
        """

    def append(self, text):
        """
        Append more text to the current text being processed.

        :param text: raw text to process.
        """
        self._state.text += text


class ControlCodeParser(Parser):
    """
    Parser to replace all control codes with a readable version - e.g. "^M" for carriage return.
    """

    def parse(self):
        """
        Generator to return coloured text from raw text.

        :returns: a 3-tuple of (start offset in raw text, command to execute, parameters)
        """
        if self._state.attributes:
            yield (0, Parser.CHANGE_COLOURS, self._attributes)
        offset = 0
        while len(self._state.text) > 0:
            letter = self._state.text[0]
            if ord(letter) < 32:
                yield (offset, Parser.DISPLAY_TEXT, "^" + chr(ord("@") + ord(letter)))
            else:
                yield (offset, Parser.DISPLAY_TEXT, letter)
            offset += 1
            self._state.text = self._state.text[1:]


class AsciimaticsParser(Parser):
    """
    Parser to handle Asciimatics rendering escape strings.
    """

    # Regular expression for use to find colour sequences in multi-colour text.
    # It should match ${n}, ${m,n} or ${m,n,o}
    _colour_sequence = re.compile(constants.COLOUR_REGEX)

    def parse(self):
        """
        Generator to return coloured text from raw text.

        :returns: a 3-tuple of (start offset in raw text, command to execute, parameters)
        """
        if self._state.attributes:
            yield (0, Parser.CHANGE_COLOURS, self._attributes)
        offset = last_offset = 0
        while len(self._state.text) > 0:
            match = self._colour_sequence.match(str(self._state.text))
            if match is None:
                yield (last_offset, Parser.DISPLAY_TEXT, self._state.text[0])
                self._state.text = self._state.text[1:]
                offset += 1
                last_offset = offset
            else:
                # The regexp either matches:
                # - 2,3,4 for ${c,a,b}
                # - 5,6 for ${c,a}
                # - 7 for ${c}.
                if match.group(2) is not None:
                    attributes = (int(match.group(2)),
                                  constants.MAPPING_ATTRIBUTES[match.group(3)],
                                  int(match.group(4)))
                elif match.group(5) is not None:
                    attributes = (int(match.group(5)),
                                  constants.MAPPING_ATTRIBUTES[match.group(6)],
                                  None)
                else:
                    attributes = (int(match.group(7)), 0, None)
                yield (last_offset, Parser.CHANGE_COLOURS, attributes)
                offset += 3 + len(match.group(1))
                self._state.text = match.group(8)


class AnsiTerminalParser(Parser):
    """
    Parser to handle ANSI terminal escape codes.
    """

    # Regular expression for use to find colour sequences in multi-colour text.
    _colour_sequence = re.compile(r"^(\x1B\[([^@-~]*)([@-~]))(.*)")
    _os_cmd = re.compile(r"^(\x1B].*\x07)(.*)")

    def reset(self, text, colours):
        """
        Reset the parser to analyze the supplied raw text.

        :param text: raw text to process.
        :param colours: colour tuple to initialise the colour map.
        """
        super(AnsiTerminalParser, self).reset(text, colours)
        if self._state.attributes is None:
            self._state.init_colours = False
            self._state.attributes = [None, None, None]
        else:
            self._state.init_colours = True
        self._state.offset = 0
        self._state.last_offset = 0
        self._state.cursor = 0

    def parse(self):
        def _handle_escape(st):
            match = self._colour_sequence.match(str(st.text))
            if match is None:
                # Not a CSI sequence... Check for some other options.
                match = self._os_cmd.match(str(st.text))
                if match:
                    # OS command - just swallow it.
                    return len(match.group(1)), None
                elif len(st.text) > 1 and st.text[1] == "M":
                    # Reverse Index - i.e. move up/scroll
                    return 2, [(st.last_offset, Parser.MOVE_RELATIVE, (0, -1))]

                # Unknown escape - guess how many characters to ignore - most likely just the next char
                # unless we can see the start of a new sequence.
                logger.debug("Ignoring: %s", st.text[0:2])
                if len(st.text) < 2:
                    return -1, None
                if st.text[1] in ("[", "]"):
                    return -1, None
                return (2, None) if st.text[1] != "(" else (3, None)
            else:
                # CSI sequence - look for the various options...
                results = []
                if match.group(3) == "m":
                    # We have found a SGR escape sequence ( CSI ... m ).  These have zero or more
                    # embedded arguments, so create a simple FSM to process the parameter stream.
                    in_set_mode = False
                    in_index_mode = False
                    in_rgb_mode = False
                    skip_size = 0
                    attribute_index = 0
                    last_attributes = tuple(st.attributes)
                    for parameter in match.group(2).split(";"):
                        try:
                            parameter = int(parameter)
                        except ValueError:
                            parameter = 0
                        if in_set_mode:
                            # We are processing a set fore/background colour code
                            if parameter == 5:
                                in_index_mode = True
                            elif parameter == 2:
                                in_rgb_mode = True
                                skip_size = 3
                            else:
                                logger.info(("Unexpected colour setting", parameter))
                                break
                            in_set_mode = False
                        elif in_index_mode:
                            # We are processing a 5;n sequence for colour indeces
                            st.attributes[attribute_index] = parameter
                            in_index_mode = False
                        elif in_rgb_mode:
                            # We are processing a 2;r;g;b sequence for RGB colours - just ignore.
                            skip_size -= 1
                            if skip_size <= 0:
                                in_rgb_mode = False
                        else:
                            # top-level stream processing
                            if parameter == 0:
                                # Reset
                                st.attributes = [constants.COLOUR_WHITE,
                                                 constants.A_NORMAL,
                                                 constants.COLOUR_BLACK]
                            elif parameter == 1:
                                # Bold
                                st.attributes[1] = constants.A_BOLD
                            elif parameter in (2, 22):
                                # Faint/normal - faint not supported so treat as normal
                                st.attributes[1] = constants.A_NORMAL
                            elif parameter == 7:
                                # Inverse
                                st.attributes[1] = constants.A_REVERSE
                            elif parameter == 27:
                                # Inverse off - assume that means normal
                                st.attributes[1] = constants.A_NORMAL
                            elif parameter in range(30, 38):
                                # Standard foreground colours
                                st.attributes[0] = parameter - 30
                            elif parameter in range(40, 48):
                                # Standard background colours
                                st.attributes[2] = parameter - 40
                            elif parameter == 38:
                                # Set foreground colour - next parameter is either 5 (index) or 2 (RGB color)
                                in_set_mode = True
                                attribute_index = 0
                            elif parameter == 48:
                                # Set background colour - next parameter is either 5 (index) or 2 (RGB color)
                                in_set_mode = True
                                attribute_index = 2
                            elif parameter in range(90, 98):
                                # Bright foreground colours
                                st.attributes[0] = parameter - 82
                            elif parameter in range(100, 108):
                                # Bright background colours
                                st.attributes[2] = parameter - 92
                            else:
                                logger.debug("Ignoring parameter: %s", parameter)
                    new_attributes = tuple(st.attributes)
                    if last_attributes != new_attributes:
                        results.append((st.last_offset, Parser.CHANGE_COLOURS, new_attributes))
                elif match.group(3) == "K":
                    # This is a line delete sequence.  Parameter defines which parts to delete.
                    param = match.group(2)
                    if param in ("", "0"):
                        # Delete to end of line
                        results.append((self._state.last_offset, Parser.DELETE_LINE, 0))
                    elif param == "1":
                        # Delete from start of line
                        results.append((self._state.last_offset, Parser.DELETE_LINE, 1))
                    elif param == "2":
                        # Delete whole line
                        results.append((self._state.last_offset, Parser.DELETE_LINE, 2))
                elif match.group(3) == "P":
                    # This is a character delete sequence.  Parameter defines how many to delete.
                    param = 1 if match.group(2) == "" else int(match.group(2))
                    results.append((self._state.last_offset, Parser.DELETE_CHARS, param))
                elif match.group(3) == "A":
                    # Move cursor up.  Parameter defines how far to move..
                    param = 1 if match.group(2) == "" else int(match.group(2))
                    results.append((self._state.last_offset, Parser.MOVE_RELATIVE, (0, -param)))
                elif match.group(3) == "B":
                    # Move cursor down.  Parameter defines how far to move..
                    param = 1 if match.group(2) == "" else int(match.group(2))
                    results.append((self._state.last_offset, Parser.MOVE_RELATIVE, (0, param)))
                elif match.group(3) == "C":
                    # Move cursor forwards.  Parameter defines how far to move..
                    param = 1 if match.group(2) == "" else int(match.group(2))
                    results.append((self._state.last_offset, Parser.MOVE_RELATIVE, (param, 0)))
                elif match.group(3) == "D":
                    # Move cursor backwards.  Parameter defines how far to move..
                    param = 1 if match.group(2) == "" else int(match.group(2))
                    results.append((self._state.last_offset, Parser.MOVE_RELATIVE, (-param, 0)))
                elif match.group(3) == "H":
                    # Move cursor to specified position.
                    x, y = 0, 0
                    params = match.group(2).split(";")
                    y = int(params[0]) - 1 if params[0] != "" else 0
                    if len(params) > 1:
                        x = int(params[1]) - 1 if params[1] != "" else 0
                    results.append((self._state.last_offset, Parser.MOVE_ABSOLUTE, (x, y)))
                elif match.group(3) == "h" and match.group(2) == "?25":
                    # Various DEC private mode commands - look for cursor visibility, ignore others.
                    results.append((self._state.last_offset, Parser.SHOW_CURSOR, True))
                elif match.group(3) == "l" and match.group(2) == "?25":
                    # Various DEC private mode commands - look for cursor visibility, ignore others.
                    results.append((self._state.last_offset, Parser.SHOW_CURSOR, False))
                elif match.group(3) == "h" and match.group(2) == "?1049":
                    # This should really create an alternate screen, but clearing is a close
                    # approximation
                    results.append((self._state.last_offset, Parser.CLEAR_SCREEN, None))
                elif match.group(3) == "l" and match.group(2) == "?1049":
                    # This should really return to the normal screen, but clearing is a close
                    # approximation
                    results.append((self._state.last_offset, Parser.CLEAR_SCREEN, None))
                elif match.group(3) == "J" and match.group(2) == "2":
                    # Clear the screen.
                    results.append((self._state.last_offset, Parser.CLEAR_SCREEN, None))
                elif match.group(3) == "s":
                    # Save cursor pos
                    results.append((self._state.last_offset, Parser.SAVE_CURSOR, None))
                elif match.group(3) == "u":
                    # Restore cursor pos
                    results.append((self._state.last_offset, Parser.RESTORE_CURSOR, None))
                else:
                    logger.debug("Ignoring control: %s", match.group(1))
                return len(match.group(1)), results

        if self._state.init_colours:
            self._state.init_colours = False
            yield (0, Parser.CHANGE_COLOURS, self._state.attributes)
        while len(self._state.text) > 0:
            char = ord(self._state.text[0])
            new_offset = 1
            if char > 31:
                yield (self._state.last_offset, Parser.DISPLAY_TEXT, self._state.text[0])
                self._state.last_offset = self._state.offset + 1
            elif char == 8:
                # Back space
                yield (self._state.last_offset, Parser.MOVE_RELATIVE, (-1, 0))
            elif char == 9:
                # Tab
                yield (self._state.last_offset, Parser.NEXT_TAB, None)
            elif char == 13:
                # Carriage return
                yield (self._state.last_offset, Parser.MOVE_ABSOLUTE, (0, None))
            elif char == 27:
                new_offset, results = _handle_escape(self._state)
                if new_offset == -1:
                    break
                if results is not None:
                    for result in results:
                        yield result
            else:
                logger.debug("Ignoring character: %d", char)
                yield (self._state.last_offset, Parser.DISPLAY_TEXT, " ")
                self._state.last_offset = self._state.offset + 1
            self._state.offset += new_offset
            self._state.text = self._state.text[new_offset:]
