
"""
This module is just a collection of simple helper functions.
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from datetime import date, datetime
from logging import getLogger


# Diagnostic logging
logger = getLogger(__name__)


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
    Unicode string-like object to store text and colour maps, using a parser to convert the raw text
    passed in into visible text and an associated colour map.
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
        """
        Return the processed (displayable) text.
        """
        return self._text

    def __len__(self):
        """
        Returns the length of the processed (displayable) text.
        """
        return len(self._text)

    def __getitem__(self, item):
        """
        Slice magic method.
        """
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
        """
        Addition magic method.
        """
        return ColouredText(self._raw_text + other.raw_text, parser=self._parser, colour=self._init_colour)

    def __eq__(self, other):
        """
        Equals magic method.
        """
        if isinstance(other, ColouredText):
            return self.raw_text == other.raw_text
        return NotImplemented

    def __ne__(self, other):
        """
        Not equals magic method.
        """
        x = self.__eq__(other)
        if x is not NotImplemented:
            return not x
        return NotImplemented

    def join(self, others):
        """
        Join the list of ColouredObjects using this ColouredObject.

        :param others: the list of other objects to join.
        """
        return ColouredText(self._raw_text.join([x.raw_text for x in others]),
                            parser=self._parser,
                            colour=self._init_colour)

    @property
    def colour_map(self):
        """
        Colour map for the processed text (for use with `paint` method).
        """
        return self._colour_map

    @property
    def raw_text(self):
        """
        Raw (unprocessed) text for this object.
        """
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

