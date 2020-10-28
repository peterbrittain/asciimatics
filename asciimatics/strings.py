"""
This module provides classes to handle embedded control strings for widgets.
"""
from asciimatics.parsers import Parser


class ColouredText(object):
    """
    Unicode string-like object to store text and colour maps, using a parser to convert the raw text
    passed in into visible text and an associated colour map.  This only handles simple colour
    change commands and will ignore more complex commands).
    """

    def __init__(self, raw_text, parser, colour=None, colour_map=None, offsets=None, text=None):
        """
        :param raw_text: The raw unicode string to be processed
        :param parser: The parser to process the text
        :param colour: Optional starting colour tuple to use for this text.
        :param colour_map: Optional ready parsed colour map for this text.
        :param offsets: Optional ready parsed offsets for this text.
        :param text: Optional ready parsed text for this text.

        The colour_map, offsets and text options are to optimize creation of substrings from an
        existing ColouredText object and should not be used in general.
        """
        super(ColouredText, self).__init__()
        self._raw_text = raw_text
        self._raw_offsets = []
        self._parser = parser
        self._colour_map = None
        self._last_colour = colour if colour else (None, None, None)
        self._init_colour = colour
        self._colour_map = []
        self._text = ""
        if colour_map:
            self._colour_map = colour_map
            self._last_colour = colour_map[-1]
            self._raw_offsets = offsets
            self._text = text
        else:
            self._parser.reset(self._raw_text, self._init_colour)
            for text_matched, offset, command, params in self._parser.parse():
                if text_matched is not None:
                    self._colour_map.append(self._last_colour)
                    self._raw_offsets.append(offset)
                    self._text += text_matched
                elif command == Parser.CHANGE_COLOURS:
                    self._last_colour = params

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
            base = self._raw_offsets[item]
            offsets = [0]
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
                base = self._raw_offsets[item][0]
                offsets = [x - base for x in self._raw_offsets[item]]
            except IndexError:
                base = 0
                offsets = []
        try:
            colour = self._colour_map[colour_index]
        except IndexError:
            colour = self._init_colour
        return ColouredText(self._raw_text[slice(start, stop, step)],
                            parser=self._parser,
                            colour=colour,
                            text=self._text[item],
                            colour_map=self._colour_map[item],
                            offsets=offsets)

    def __add__(self, other):
        """
        Addition magic method.
        """
        if hasattr(other, "raw_text"):
            new_text = self._raw_text + other.raw_text
        else:
            new_text = self._raw_text + str(other)
        return ColouredText(new_text, parser=self._parser, colour=self._init_colour)

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

    def startswith(self, text):
        """
        Check whether parsed (i.e. displayed) text starts woth specified string.
        """
        return self._text.startswith(text)

    def join(self, others):
        """
        Join the list of ColouredObjects using this ColouredObject.

        :param others: the list of other objects to join.
        """
        try:
            return ColouredText(self._raw_text.join([x.raw_text for x in others]),
                                parser=self._parser,
                                colour=self._init_colour)
        except AttributeError:
            return ColouredText(self._raw_text.join(others),
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
