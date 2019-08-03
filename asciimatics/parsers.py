
"""
This module is just a collection of simple helper functions.
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import re
from future.utils import with_metaclass
from abc import ABCMeta, abstractmethod
from logging import getLogger
import asciimatics.constants as constants


# Diagnostic logging
logger = getLogger(__name__)


class Parser(with_metaclass(ABCMeta, object)):
    """
    Abstract class to represent text parsers for text colouring.
    """

    @abstractmethod
    def parse(self, text, colours):
        """
        Generator to return coloured text
        :return:
        """


class AsciimaticsParser(Parser):
    # Regular expression for use to find colour sequences in multi-colour text.
    # It should match ${n}, ${m,n} or ${m,n,o}
    _colour_sequence = re.compile(constants.COLOUR_REGEX)

    """
    Parser to handle Asciimatics' rendering escape strings 
    """
    def __init__(self):
        super(AsciimaticsParser, self).__init__()

    def parse(self, text, colours):
        attributes = colours if colours else (None, None, None)
        offset = last_offset = 0
        while len(text) > 0:
            match = self._colour_sequence.match(str(text))
            if match is None:
                yield text[0], attributes, last_offset
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
                offset += 3 + len(match.group(1))
                text = match.group(8)


class AnsiTerminalParser(Parser):
    # Regular expression for use to find colour sequences in multi-colour text.
    _colour_sequence = re.compile(r"^(\x1B\[([^@-~]*)([@-~]))(.*)")

    """
    Parser to handle ANSI terminal escape codes. 
    """
    def __init__(self):
        super(AnsiTerminalParser, self).__init__()

    def parse(self, text, colours):
        attributes = [x for x in colours] if colours else [None, None, None]
        offset = last_offset = 0
        while len(text) > 0:
            match = self._colour_sequence.match(str(text))
            if match is None:
                yield text[0], tuple(attributes), last_offset
                text = text[1:]
                offset += 1
                last_offset = offset
            else:
                # The regex matches general CSI sequences.  Look for colour codes (i.e. 'CSI ... m').  These
                # can have embedded arguments, so create a simple FSM to process the parameter stream.
                if match.group(3) == "m":
                    in_set_mode = False
                    in_index_mode = False
                    in_rgb_mode = False
                    skip_size = 0
                    attribute_index = 0
                    for parameter in match.group(2).split(";"):
                        parameter = int(parameter)
                        if in_set_mode:
                            # We are processing a set fore/background colour code
                            if parameter == 5:
                                in_index_mode = True
                            elif parameter == 5:
                                in_rgb_mode = True
                                skip_size = 3
                            else:
                                logger.info(("Unexpected colour setting", parameter))
                            in_set_mode = False
                        elif in_index_mode:
                            # We are processing a 5;n sequence for colour indeces
                            attributes[attribute_index] = parameter
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
                                attributes = [7, 0, 0]
                            elif parameter == 1:
                                # Bold
                                attributes[1] = constants.A_BOLD
                            elif parameter in (2, 22):
                                # Faint/normal - faint not supported so treat as normal
                                attributes[1] = constants.A_NORMAL
                            elif parameter == 7:
                                # Inverse
                                attributes[1] = constants.A_REVERSE
                            elif parameter == 27:
                                # Inverse off - assume that means normal
                                attributes[1] = constants.A_NORMAL
                            elif parameter in range(30, 38):
                                # Standard foreground colours
                                attributes[0] = parameter - 30
                            elif parameter in range(40, 48):
                                # Standard background colours
                                attributes[2] = parameter - 40
                            elif parameter == 38:
                                # Set foreground colour - next parameter is either 5 (index) or 2 (RGB color)
                                in_set_mode = True
                                attribute_index = 0
                            elif parameter == 38:
                                # Set background colour - next parameter is either 5 (index) or 2 (RGB color)
                                in_set_mode = True
                                attribute_index = 2
                            else:
                                logger.debug("Ignoring parameter:", parameter)
                else:
                    logger.debug("Ignoring control:", match.group(3))
                offset += len(match.group(1))
                text = match.group(4)
