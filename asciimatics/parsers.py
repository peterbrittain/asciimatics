
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

    #: Command to change active colour tuple.  Parameters are the 3-tuple of (fg, attr, bg)
    CHANGE_COLOURS = 1
    #: Command to move cursor to abs position.  Parameters are (x, y) where each are absolute positions.
    MOVE_ABSOLUTE = 2
    #: Command to move cursor to relative position.  Parameters are (x, y) where each are relative positions.
    MOVE_RELATIVE = 3
    #: Command to delete part of the current line. Params are 0, 1 and 2 for end, start, all.
    DELETE_LINE = 4

    def __init__(self):
        """
        Initialize the parser.
        """
        self._raw_text = ""
        self._attributes = None
        self._result = []

    def reset(self, text, colours):
        """
        Reset the parser to analyze the supplied raw text.

        :param text: raw text to process.
        :param colours: colour tuple to initialise the colour map.
        """
        self._raw_text = text
        self._attributes = colours
        self._result = []
        if colours:
            self._result.append((None, 0, Parser.CHANGE_COLOURS, colours))

    def parse(self):
        """
        Generator to return coloured text from raw text.

        Generally returns a stream of text/color tuple/offset tuples.  If there is a colour update with no
        visible text, the first element of the tuple may be None.

        :returns: a 4-tuple of (the displayable text, start offset in raw text, command, parameters)
        """
        for element in self._result:
            yield tuple(element)


class ControlCodeParser(Parser):
    """
    Parser to replace all control codes with a readable version - e.g. "^M" for \\r.
    """

    def reset(self, text, colours=None):
        """
        Reset the parser to analyze the supplied raw text.

        :param text: raw text to process.
        :param colours: colour tuple to initialise the colour map.
        """
        super(ControlCodeParser, self).reset(text, colours)
        for i, letter in enumerate(text):
            if ord(letter) < 32:
                self._result.append(("^" + chr(ord("@") + ord(letter)), i, None, None))
            else:
                self._result.append((letter, i, None, None))


class AsciimaticsParser(Parser):
    """
    Parser to handle Asciimatics rendering escape strings.
    """

    # Regular expression for use to find colour sequences in multi-colour text.
    # It should match ${n}, ${m,n} or ${m,n,o}
    _colour_sequence = re.compile(constants.COLOUR_REGEX)

    def reset(self, text, colours):
        """
        Reset the parser to analyze the supplied raw text.

        :param text: raw text to process.
        :param colours: colour tuple to initialise the colour map.
        """
        super(AsciimaticsParser, self).reset(text, colours)
        offset = last_offset = 0
        text = self._raw_text
        while len(text) > 0:
            match = self._colour_sequence.match(str(text))
            if match is None:
                self._result.append((text[0], last_offset, None, None))
                text = text[1:]
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
                self._result.append((None, last_offset, Parser.CHANGE_COLOURS, attributes))
                offset += 3 + len(match.group(1))
                text = match.group(8)


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
        state = _DotDict()
        state.attributes = [x for x in self._attributes] if self._attributes else [None, None, None]
        state.offset = 0
        state.last_offset = 0
        state.cursor = 0
        state.text = self._raw_text

        def _handle_escape(st):
            match = self._colour_sequence.match(str(st.text))
            if match is None:
                # Check for OS commands
                match = self._os_cmd.match(str(st.text))
                if match:
                    return len(match.group(1))

                # Unknown escape - ignore next char as a minimal way to handle many sequences
                return 2
            else:
                if match.group(3) == "m":
                    # We have found a SGR escape sequence ( CSI ... m ).  These have zero or more
                    # embedded arguments, so create a simple FSM to process the parameter stream.
                    in_set_mode = False
                    in_index_mode = False
                    in_rgb_mode = False
                    skip_size = 0
                    attribute_index = 0
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
                            else:
                                logger.debug("Ignoring parameter: %s", parameter)
                    self._result.append((None, st.last_offset, Parser.CHANGE_COLOURS, tuple(st.attributes)))
                elif match.group(3) == "K":
                    # This is a line delete sequence.  Parameter defines which parts to delete.
                    param = match.group(2)
                    if param in ("", "0"):
                        # Delete to end of line
                        self._result.append((None, state.last_offset, Parser.DELETE_LINE, 0))
                    elif param == "1":
                        # Delete from start of line
                        self._result.append((None, state.last_offset, Parser.DELETE_LINE, 1))
                    elif param == "2":
                        # Delete whole line
                        self._result.append((None, state.last_offset, Parser.DELETE_LINE, 2))
                elif match.group(3) == "P":
                    # This is a character delete sequence.  Parameter defines how many to delete.
                    param = 1 if match.group(2) == "" else int(match.group(2))
                    # TODO: delete next N chars st.result = st.result[:st.cursor] + st.result[st.cursor + param:]
                elif match.group(3) == "A":
                    # Move cursor up.  Parameter defines how far to move..
                    param = 1 if match.group(2) == "" else int(match.group(2))
                    self._result.append((None, state.last_offset, Parser.MOVE_RELATIVE, (0, -param)))
                elif match.group(3) == "B":
                    # Move cursor down.  Parameter defines how far to move..
                    param = 1 if match.group(2) == "" else int(match.group(2))
                    self._result.append((None, state.last_offset, Parser.MOVE_RELATIVE, (0, param)))
                elif match.group(3) == "C":
                    # Move cursor forwards.  Parameter defines how far to move..
                    param = 1 if match.group(2) == "" else int(match.group(2))
                    self._result.append((None, state.last_offset, Parser.MOVE_RELATIVE, (param, 0)))
                elif match.group(3) == "D":
                    # Move cursor backwards.  Parameter defines how far to move..
                    param = 1 if match.group(2) == "" else int(match.group(2))
                    self._result.append((None, state.last_offset, Parser.MOVE_RELATIVE, (-param, 0)))
                elif match.group(3) == "H":
                    # Move cursor to specified position.
                    x, y = 0, 0
                    params = match.group(2).split(";")
                    y = int(params[0]) - 1 if params[0] != "" else 0
                    if len(params) > 1:
                        x = int(params[1]) - 1 if params[1] != "" else 0
                    self._result.append((None, state.last_offset, Parser.MOVE_ABSOLUTE, (x, y)))
                else:
                    logger.debug("Ignoring control: %s", match.group(1))
                return len(match.group(1))

        while len(state.text) > 0:
            char = ord(state.text[0])
            new_offset = 1
            if char > 31:
                self._result.append((state.text[0], state.last_offset, None, None))
                state.last_offset = state.offset + 1
            elif char == 8:
                # Back space
                self._result.append((None, state.last_offset, Parser.MOVE_RELATIVE, (-1, 0)))
            elif char == 13:
                # Carriage return
                self._result.append((None, state.last_offset, Parser.MOVE_ABSOLUTE, (0, None)))
            elif char == 27:
                new_offset = _handle_escape(state)
            else:
                logger.debug("Ignoring character: %d", char)
            state.offset += new_offset
            state.text = state.text[new_offset:]
