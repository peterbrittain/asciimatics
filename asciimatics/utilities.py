
"""
This module is just a collection of simple helper functions.
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import re

from future.utils import with_metaclass
from datetime import date, datetime
from abc import ABCMeta, abstractmethod
from logging import getLogger


# Diagnostic logging
logger = getLogger(__name__)

#: Attribute conversion table for the ${c,a} form of attributes for
#: :py:obj:`~.Screen.paint`.
# TODO: Fix duplication in renderers and circular references in Screen
ATTRIBUTES = {
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
}


def readable_mem(mem):
    """
    :param mem: An integer number of bytes to convert to human-readable form.
    :return: A human-readable string representation of the number.
    """
    for suffix in ["", "K", "M", "G", "T"]:
        if mem < 10000:
            return "{}{}".format(int(mem), suffix)
        mem /= 1024
    return "{}P".format(int(mem))


def readable_timestamp(stamp):
    """
    :param stamp: A floating point number representing the POSIX file timestamp.
    :return: A short human-readable string representation of the timestamp.
    """
    if date.fromtimestamp(stamp) == date.today():
        return str(datetime.fromtimestamp(stamp).strftime("%I:%M:%S%p"))
    else:
        return str(date.fromtimestamp(stamp))


class _DotDict(dict):
    """
    Modified dictionary to allow dot notation access.

    This can be used for quick and easy structures.  See https://stackoverflow.com/q/2352181/4994021
    """

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class ColouredText(object):
    """
    Unicode string-like object to store text and colour maps
    """

    def __init__(self, text, parser, colour=None):
        """
        :param text: The raw unicode string to be processed
        :param parser: The parser to process the text
        :param colour: Optional starting colour tuple to use for this text.
        """
        super(ColouredText, self).__init__()
        self._raw_text = text
        self._raw_offsets = []
        self._parser = parser
        self._colour_map = None
        self._last_colour = self._init_colour = colour
        self._colour_map = []
        self._text = ""
        for text, colour, offset in self._parser.parse(self._raw_text, self._init_colour):
            for i, _ in enumerate(text):
                self._colour_map.append(colour)
                self._raw_offsets.append(offset + i)
            self._text += text
            self._last_colour = colour

    def __repr__(self):
        return self._text

    def __len__(self):
        return len(self._text)

    def __getitem__(self, item):
        if isinstance(item, int):
            start = self._raw_offsets[item]
            stop = None if item == len(self._raw_offsets) - 1 else self._raw_offsets[item + 1]
            step = 1
            colour_index = max(0, item - 1)
        else:
            try:
                start = None if item.start is None else self._raw_offsets[slice(item.start, None, None)][0]
            except IndexError:
                start = len(self._raw_text)
            try:
                stop = None if item.stop is None else self._raw_offsets[slice(item.stop, None, None)][0]
            except IndexError:
                stop = None
            step = item.step
            colour_index = max(0, item.start - 1 if item.start else 0)
        try:
            colour = self._colour_map[colour_index]
        except Exception:
            colour = self._init_colour
        return ColouredText(self._raw_text[slice(start, stop, step)],
                            parser=self._parser,
                            colour=colour)

    def __add__(self, other):
        return ColouredText(self._raw_text + other.raw_text, parser=self._parser, colour=self._init_colour)

    def __eq__(self, other):
        if isinstance(other, ColouredText):
            return self.raw_text == other.raw_text
        return NotImplemented

    def __ne__(self, other):
        x = self.__eq__(other)
        if x is not NotImplemented:
            return not x
        return NotImplemented

    def join(self, others):
        return ColouredText(self._raw_text.join([x.raw_text for x in others]), parser=self._parser, colour=self._init_colour)

    @property
    def colour_map(self):
        return self._colour_map

    @property
    def raw_text(self):
        return self._raw_text

    @property
    def first_colour(self):
        """
        First colour triplet used for this text.
        """
        return self._init_colour

    @property
    def last_colour(self):
        """
        Last colour triplet used for this text.
        """
        return self._last_colour


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
    # TODO: Sort out duplication here and in renderers.py
    _colour_esc_code = r"^\$\{((\d+),(\d+),(\d+)|(\d+),(\d+)|(\d+))\}(.*)"
    _colour_sequence = re.compile(_colour_esc_code)

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
                                  ATTRIBUTES[match.group(3)],
                                  int(match.group(4)))
                elif match.group(5) is not None:
                    attributes = (int(match.group(5)),
                                  ATTRIBUTES[match.group(6)],
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
                                # TODO - fix hard-coded constant
                                attributes[1] = 1
                            elif parameter in (2, 22):
                                # Faint/normal
                                # TODO: Are these SGR modes really the same?  And fix constant
                                attributes[1] = 2
                            elif parameter == 7:
                                # Inverse
                                # TODO - fix hard-coded constant
                                attributes[1] = 3
                            elif parameter == 27:
                                # Inverse off
                                # TODO - fix hard-coded constant.  Also what about bold/inverse?
                                attributes[1] = 0
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
