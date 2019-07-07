
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

    def __init__(self, text, parser, colour_map=None):
        """
        :param text: The raw unicode string to be processed
        :param parser: The parser to process the text
        :param colour_map: Optional pre-calculated colour map to use for this text.
        """
        super(ColouredText, self).__init__()
        self._raw_text = text
        self._raw_map = colour_map
        self._raw_offsets = []
        self._parser = parser
        self._colour_map = None
        self._create_colour_map()

    def _create_colour_map(self):
        """
        Create the colour map for the current text
        """
        if self._parser is None:
            self._colour_map = self._raw_map
            self._text = self._raw_text
            self._raw_offsets = [x for x in range(len(self._text))]
        else:
            self._colour_map = []
            self._text = ""
            for text, colour, offset in self._parser.parse(self._raw_text):
                for i, _ in enumerate(text):
                    self._colour_map.append(colour)
                    self._raw_offsets.append(offset + i)
                self._text += text

    def __repr__(self):
        logger.debug("Str: {}".format(self._text))
        return self._text

    def __len__(self):
        logger.debug("Len: {}".format(len(self._text)))
        return len(self._text)

    def __getitem__(self, item):
        logger.debug("Item: {}".format((item, self._raw_text)))
        if isinstance(item, int):
            start = self._raw_offsets[item]
            stop = None if item == len(self._raw_offsets) - 1 else self._raw_offsets[item + 1]
            step = 1
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
        logger.debug("Slice: '{}'".format((self._raw_text[slice(start, stop, step)], start, stop)))
        return ColouredText(self._raw_text[slice(start, stop, step)], parser=self._parser)

    def __add__(self, other):
        logger.debug("Add: '{}' '{}'".format(self._raw_text, other.raw_text))
        return ColouredText(self._raw_text + other.raw_text, parser=self._parser)


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
        logger.debug("Join: '{}' {}".format(self._raw_text, others))
        return ColouredText(self._raw_text.join([x.raw_text for x in others]), parser=self._parser)

    @property
    def colour_map(self):
        return self._colour_map

    @property
    def raw_text(self):
        return self._raw_text


class Parser(with_metaclass(ABCMeta, object)):
    """
    Abstract class to represent text parsers for text colouring.
    """

    @abstractmethod
    def parse(self, text):
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

    def parse(self, text):
        attributes = (None, None, None)
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
