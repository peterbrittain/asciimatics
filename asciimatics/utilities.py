
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
        else:
            self._colour_map = []
            self._text = ""
            for text, colour in self._parser.parse(self._raw_text):
                for _ in text:
                    self._colour_map.append(colour)
                self._text += text

    def __repr__(self):
        return self._text

    def __len__(self):
        return len(self._text)

    def __getitem__(self, item):
        return self._text[item]

    def __add__(self, other):
        return ColouredText(self._text + str(other), parser=self._parser)

    def encode(self, encoding):
        return self._text.encode(encoding)

    @property
    def colour_map(self):
        return self._colour_map


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
        while len(text) > 0:
            match = self._colour_sequence.match(str(text))
            if match is None:
                yield text[0], attributes
                text = text[1:]
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
                text = match.group(8)
