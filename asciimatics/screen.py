# -*- coding: utf-8 -*-
"""
This module defines common screen output function.  For more details, see
http://asciimatics.readthedocs.io/en/latest/io.html
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
import signal
import struct
import sys
import time
from abc import ABCMeta, abstractmethod
from locale import getlocale, getdefaultlocale
from logging import getLogger
from math import sqrt

from builtins import object
from builtins import range
from builtins import ord
from builtins import chr
from future.utils import with_metaclass
from wcwidth import wcwidth, wcswidth

from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.exceptions import ResizeScreenError, StopApplication, NextScene
from asciimatics.utilities import _DotDict

logger = getLogger(__name__)

# Looks like pywin32 is missing some Windows constants
ENABLE_EXTENDED_FLAGS = 0x0080
ENABLE_QUICK_EDIT_MODE = 0x0040


class _DoubleBuffer(object):
    """
    Pure python Screen buffering.
    """
    def __init__(self, height, width):
        """
        :param height: Height of the buffer to create.
        :param width: Width of the buffer to create.
        """
        super(_DoubleBuffer, self).__init__()
        self._height = height
        self._width = width
        self._double_buffer = None
        line = [(ord(u" "), Screen.COLOUR_WHITE, 0, 0, 1) for _ in range(self._width)]
        self._screen_buffer = [line[:] for _ in range(self._height)]
        self.clear(Screen.COLOUR_WHITE, 0, 0)

    def clear(self, fg, attr, bg):
        """
        Clear the double-buffer.

        This does not clear the screen buffer and so the next call to deltas will still show all changes.

        :param fg: The foreground colour to use for the new buffer.
        :param attr: The attribute value to use for the new buffer.
        :param bg: The background colour to use for the new buffer.
        """
        line = [(ord(u" "), fg, attr, bg, 1) for _ in range(self._width)]
        self._double_buffer = [line[:] for _ in range(self._height)]

    def get(self, x, y):
        """
        Get the cell value from the specified location

        :param x: The column (x coord) of the character.
        :param y: The row (y coord) of the character.

        :return: A 5-tuple of (unicode, foreground, attributes, background, width).
        """
        return self._double_buffer[y][x]

    def set(self, x, y, value):
        """
        Set the cell value from the specified location

        :param x: The column (x coord) of the character.
        :param y: The row (y coord) of the character.
        :param value: A 5-tuple of (unicode, foreground, attributes, background, width).
        """
        self._double_buffer[y][x] = value

    def deltas(self, start, height):
        """
        Return a list-like (i.e. iterable) object of (y, x) tuples
        """
        for y in range(start, min(start + height, self._height)):
            for x in range(self._width):
                    old_cell = self._screen_buffer[y][x]
                    new_cell = self._double_buffer[y][x]
                    if old_cell != new_cell:
                        yield y, x

    def invalidate(self, y1, y2):
        """
        Invalidate the required lines for redisplay on the next call to deltas().
        """
        line = [(None, None, None, None, 1) for _ in range(self._width)]
        for y in range(y1, y2):
            self._screen_buffer[y] = line[:]

    def sync(self):
        """
        Synchronize the screen buffer with the double buffer.
        """
        # We're copying an array of tuples, so only need to copy the 2-D array (as the tuples are immutable).
        # This is way faster than a deep copy (which is INCREDIBLY slow).
        self._screen_buffer = [row[:] for row in self._double_buffer]


class _AbstractCanvas(with_metaclass(ABCMeta, object)):
    """
    Abstract class to handle screen buffering.
    """

    # Characters for anti-aliasing line drawing.
    _line_chars = " ''^.|/7.\\|Ywbd#"
    _uni_line_chars = " ▘▝▀▖▌▞▛▗▚▐▜▄▙▟█"

    #  Colour palette for 8/16 colour terminals
    _8_palette = [
        0x00, 0x00, 0x00,
        0x80, 0x00, 0x00,
        0x00, 0x80, 0x00,
        0x80, 0x80, 0x00,
        0x00, 0x00, 0x80,
        0x80, 0x00, 0x80,
        0x00, 0x80, 0x80,
        0xc0, 0xc0, 0xc0,
    ] + [0x00 for _ in range(248 * 3)]

    # Colour palette for 256 colour terminals
    _256_palette = [
        0x00, 0x00, 0x00,
        0x80, 0x00, 0x00,
        0x00, 0x80, 0x00,
        0x80, 0x80, 0x00,
        0x00, 0x00, 0x80,
        0x80, 0x00, 0x80,
        0x00, 0x80, 0x80,
        0xc0, 0xc0, 0xc0,
        0x80, 0x80, 0x80,
        0xff, 0x00, 0x00,
        0x00, 0xff, 0x00,
        0xff, 0xff, 0x00,
        0x00, 0x00, 0xff,
        0xff, 0x00, 0xff,
        0x00, 0xff, 0xff,
        0xff, 0xff, 0xff,
        0x00, 0x00, 0x00,
        0x00, 0x00, 0x5f,
        0x00, 0x00, 0x87,
        0x00, 0x00, 0xaf,
        0x00, 0x00, 0xd7,
        0x00, 0x00, 0xff,
        0x00, 0x5f, 0x00,
        0x00, 0x5f, 0x5f,
        0x00, 0x5f, 0x87,
        0x00, 0x5f, 0xaf,
        0x00, 0x5f, 0xd7,
        0x00, 0x5f, 0xff,
        0x00, 0x87, 0x00,
        0x00, 0x87, 0x5f,
        0x00, 0x87, 0x87,
        0x00, 0x87, 0xaf,
        0x00, 0x87, 0xd7,
        0x00, 0x87, 0xff,
        0x00, 0xaf, 0x00,
        0x00, 0xaf, 0x5f,
        0x00, 0xaf, 0x87,
        0x00, 0xaf, 0xaf,
        0x00, 0xaf, 0xd7,
        0x00, 0xaf, 0xff,
        0x00, 0xd7, 0x00,
        0x00, 0xd7, 0x5f,
        0x00, 0xd7, 0x87,
        0x00, 0xd7, 0xaf,
        0x00, 0xd7, 0xd7,
        0x00, 0xd7, 0xff,
        0x00, 0xff, 0x00,
        0x00, 0xff, 0x5f,
        0x00, 0xff, 0x87,
        0x00, 0xff, 0xaf,
        0x00, 0xff, 0xd7,
        0x00, 0xff, 0xff,
        0x5f, 0x00, 0x00,
        0x5f, 0x00, 0x5f,
        0x5f, 0x00, 0x87,
        0x5f, 0x00, 0xaf,
        0x5f, 0x00, 0xd7,
        0x5f, 0x00, 0xff,
        0x5f, 0x5f, 0x00,
        0x5f, 0x5f, 0x5f,
        0x5f, 0x5f, 0x87,
        0x5f, 0x5f, 0xaf,
        0x5f, 0x5f, 0xd7,
        0x5f, 0x5f, 0xff,
        0x5f, 0x87, 0x00,
        0x5f, 0x87, 0x5f,
        0x5f, 0x87, 0x87,
        0x5f, 0x87, 0xaf,
        0x5f, 0x87, 0xd7,
        0x5f, 0x87, 0xff,
        0x5f, 0xaf, 0x00,
        0x5f, 0xaf, 0x5f,
        0x5f, 0xaf, 0x87,
        0x5f, 0xaf, 0xaf,
        0x5f, 0xaf, 0xd7,
        0x5f, 0xaf, 0xff,
        0x5f, 0xd7, 0x00,
        0x5f, 0xd7, 0x5f,
        0x5f, 0xd7, 0x87,
        0x5f, 0xd7, 0xaf,
        0x5f, 0xd7, 0xd7,
        0x5f, 0xd7, 0xff,
        0x5f, 0xff, 0x00,
        0x5f, 0xff, 0x5f,
        0x5f, 0xff, 0x87,
        0x5f, 0xff, 0xaf,
        0x5f, 0xff, 0xd7,
        0x5f, 0xff, 0xff,
        0x87, 0x00, 0x00,
        0x87, 0x00, 0x5f,
        0x87, 0x00, 0x87,
        0x87, 0x00, 0xaf,
        0x87, 0x00, 0xd7,
        0x87, 0x00, 0xff,
        0x87, 0x5f, 0x00,
        0x87, 0x5f, 0x5f,
        0x87, 0x5f, 0x87,
        0x87, 0x5f, 0xaf,
        0x87, 0x5f, 0xd7,
        0x87, 0x5f, 0xff,
        0x87, 0x87, 0x00,
        0x87, 0x87, 0x5f,
        0x87, 0x87, 0x87,
        0x87, 0x87, 0xaf,
        0x87, 0x87, 0xd7,
        0x87, 0x87, 0xff,
        0x87, 0xaf, 0x00,
        0x87, 0xaf, 0x5f,
        0x87, 0xaf, 0x87,
        0x87, 0xaf, 0xaf,
        0x87, 0xaf, 0xd7,
        0x87, 0xaf, 0xff,
        0x87, 0xd7, 0x00,
        0x87, 0xd7, 0x5f,
        0x87, 0xd7, 0x87,
        0x87, 0xd7, 0xaf,
        0x87, 0xd7, 0xd7,
        0x87, 0xd7, 0xff,
        0x87, 0xff, 0x00,
        0x87, 0xff, 0x5f,
        0x87, 0xff, 0x87,
        0x87, 0xff, 0xaf,
        0x87, 0xff, 0xd7,
        0x87, 0xff, 0xff,
        0xaf, 0x00, 0x00,
        0xaf, 0x00, 0x5f,
        0xaf, 0x00, 0x87,
        0xaf, 0x00, 0xaf,
        0xaf, 0x00, 0xd7,
        0xaf, 0x00, 0xff,
        0xaf, 0x5f, 0x00,
        0xaf, 0x5f, 0x5f,
        0xaf, 0x5f, 0x87,
        0xaf, 0x5f, 0xaf,
        0xaf, 0x5f, 0xd7,
        0xaf, 0x5f, 0xff,
        0xaf, 0x87, 0x00,
        0xaf, 0x87, 0x5f,
        0xaf, 0x87, 0x87,
        0xaf, 0x87, 0xaf,
        0xaf, 0x87, 0xd7,
        0xaf, 0x87, 0xff,
        0xaf, 0xaf, 0x00,
        0xaf, 0xaf, 0x5f,
        0xaf, 0xaf, 0x87,
        0xaf, 0xaf, 0xaf,
        0xaf, 0xaf, 0xd7,
        0xaf, 0xaf, 0xff,
        0xaf, 0xd7, 0x00,
        0xaf, 0xd7, 0x5f,
        0xaf, 0xd7, 0x87,
        0xaf, 0xd7, 0xaf,
        0xaf, 0xd7, 0xd7,
        0xaf, 0xd7, 0xff,
        0xaf, 0xff, 0x00,
        0xaf, 0xff, 0x5f,
        0xaf, 0xff, 0x87,
        0xaf, 0xff, 0xaf,
        0xaf, 0xff, 0xd7,
        0xaf, 0xff, 0xff,
        0xd7, 0x00, 0x00,
        0xd7, 0x00, 0x5f,
        0xd7, 0x00, 0x87,
        0xd7, 0x00, 0xaf,
        0xd7, 0x00, 0xd7,
        0xd7, 0x00, 0xff,
        0xd7, 0x5f, 0x00,
        0xd7, 0x5f, 0x5f,
        0xd7, 0x5f, 0x87,
        0xd7, 0x5f, 0xaf,
        0xd7, 0x5f, 0xd7,
        0xd7, 0x5f, 0xff,
        0xd7, 0x87, 0x00,
        0xd7, 0x87, 0x5f,
        0xd7, 0x87, 0x87,
        0xd7, 0x87, 0xaf,
        0xd7, 0x87, 0xd7,
        0xd7, 0x87, 0xff,
        0xd7, 0xaf, 0x00,
        0xd7, 0xaf, 0x5f,
        0xd7, 0xaf, 0x87,
        0xd7, 0xaf, 0xaf,
        0xd7, 0xaf, 0xd7,
        0xd7, 0xaf, 0xff,
        0xd7, 0xd7, 0x00,
        0xd7, 0xd7, 0x5f,
        0xd7, 0xd7, 0x87,
        0xd7, 0xd7, 0xaf,
        0xd7, 0xd7, 0xd7,
        0xd7, 0xd7, 0xff,
        0xd7, 0xff, 0x00,
        0xd7, 0xff, 0x5f,
        0xd7, 0xff, 0x87,
        0xd7, 0xff, 0xaf,
        0xd7, 0xff, 0xd7,
        0xd7, 0xff, 0xff,
        0xff, 0x00, 0x00,
        0xff, 0x00, 0x5f,
        0xff, 0x00, 0x87,
        0xff, 0x00, 0xaf,
        0xff, 0x00, 0xd7,
        0xff, 0x00, 0xff,
        0xff, 0x5f, 0x00,
        0xff, 0x5f, 0x5f,
        0xff, 0x5f, 0x87,
        0xff, 0x5f, 0xaf,
        0xff, 0x5f, 0xd7,
        0xff, 0x5f, 0xff,
        0xff, 0x87, 0x00,
        0xff, 0x87, 0x5f,
        0xff, 0x87, 0x87,
        0xff, 0x87, 0xaf,
        0xff, 0x87, 0xd7,
        0xff, 0x87, 0xff,
        0xff, 0xaf, 0x00,
        0xff, 0xaf, 0x5f,
        0xff, 0xaf, 0x87,
        0xff, 0xaf, 0xaf,
        0xff, 0xaf, 0xd7,
        0xff, 0xaf, 0xff,
        0xff, 0xd7, 0x00,
        0xff, 0xd7, 0x5f,
        0xff, 0xd7, 0x87,
        0xff, 0xd7, 0xaf,
        0xff, 0xd7, 0xd7,
        0xff, 0xd7, 0xff,
        0xff, 0xff, 0x00,
        0xff, 0xff, 0x5f,
        0xff, 0xff, 0x87,
        0xff, 0xff, 0xaf,
        0xff, 0xff, 0xd7,
        0xff, 0xff, 0xff,
        0x08, 0x08, 0x08,
        0x12, 0x12, 0x12,
        0x1c, 0x1c, 0x1c,
        0x26, 0x26, 0x26,
        0x30, 0x30, 0x30,
        0x3a, 0x3a, 0x3a,
        0x44, 0x44, 0x44,
        0x4e, 0x4e, 0x4e,
        0x58, 0x58, 0x58,
        0x62, 0x62, 0x62,
        0x6c, 0x6c, 0x6c,
        0x76, 0x76, 0x76,
        0x80, 0x80, 0x80,
        0x8a, 0x8a, 0x8a,
        0x94, 0x94, 0x94,
        0x9e, 0x9e, 0x9e,
        0xa8, 0xa8, 0xa8,
        0xb2, 0xb2, 0xb2,
        0xbc, 0xbc, 0xbc,
        0xc6, 0xc6, 0xc6,
        0xd0, 0xd0, 0xd0,
        0xda, 0xda, 0xda,
        0xe4, 0xe4, 0xe4,
        0xee, 0xee, 0xee,
    ]

    def __init__(self, height, width, buffer_height, colours, unicode_aware):
        """
        :param height: The buffer height for this object.
        :param width: The buffer width for this object.
        :param buffer_height: The buffer height for this object.
        :param colours: Number of colours for this object.
        :param unicode_aware: Force use of unicode options for this object.
        """
        super(_AbstractCanvas, self).__init__()

        # Can we handle unicode environments?
        self._unicode_aware = unicode_aware

        # Create screen buffers.
        self.height = height
        self.width = width
        self.colours = colours
        self._buffer_height = buffer_height
        self._buffer = None
        self._start_line = 0
        self._x = 0
        self._y = 0

        # dictionary cache for colour blending
        self._blends = {}

        # Reset the screen ready to go...
        self.reset()

    def clear_buffer(self, fg, attr, bg):
        """
        Clear the current double-buffer used by this object.

        :param fg: The foreground colour to use for the new buffer.
        :param attr: The attribute value to use for the new buffer.
        :param bg: The background colour to use for the new buffer.
        """
        self._buffer.clear(fg, attr, bg)

    def reset(self):
        """
        Reset the internal buffers for the abstract canvas.
        """
        # Reset our screen buffer
        self._start_line = 0
        self._x = self._y = None
        self._buffer = _DoubleBuffer(self._buffer_height, self.width)
        self._reset()

    def scroll(self):
        """
        Scroll the abstract canvas up one line.
        """
        self._start_line += 1

    def scroll_to(self, line):
        """
        Scroll the abstract canvas to make a specific line.

        :param line: The line to scroll to.
        """
        self._start_line = line

    @abstractmethod
    def _reset(self):
        """
        Internal implementation required to reset underlying drawing interface.
        """

    @abstractmethod
    def refresh(self):
        """
        Refresh this object - this will draw to the underlying display interface.
        """

    def get_from(self, x, y):
        """
        Get the character at the specified location.

        :param x: The column (x coord) of the character.
        :param y: The row (y coord) of the character.

        :return: A 4-tuple of (ascii code, foreground, attributes, background)
                 for the character at the location.
        """
        if y < 0 or y >= self._buffer_height or x < 0 or x >= self.width:
            return None
        cell = self._buffer.get(x, y)
        return cell[0], cell[1], cell[2], cell[3]

    def print_at(self, text, x, y, colour=7, attr=0, bg=0, transparent=False):
        """
        Print the text at the specified location using the specified colour and attributes.

        :param text: The (single line) text to be printed.
        :param x: The column (x coord) for the start of the text.
        :param y: The line (y coord) for the start of the text.
        :param colour: The colour of the text to be displayed.
        :param attr: The cell attribute of the text to be displayed.
        :param bg: The background colour of the text to be displayed.
        :param transparent: Whether to print spaces or not, thus giving a
            transparent effect.

        The colours and attributes are the COLOUR_xxx and A_yyy constants
        defined in the Screen class.
        """
        # Trim text to the buffer vertically.  Don't trim horizontally as we don't know whether any
        # of these characters are dual-width yet.  Handle it on the fly below...
        if y < 0 or y >= self._buffer_height or x > self.width:
            return

        if len(text) > 0:
            j = 0
            for i, c in enumerate(text):
                # Handle under-run and overrun of double-width glyphs now.
                #
                # Note that wcwidth uses significant resources, so only call when we have a
                # unicode aware application.  The rest of the time assume ASCII.
                width = wcwidth(c) if self._unicode_aware else 1
                if x + i + j < 0:
                    x += (width - 1)
                    continue
                if x + i + j + width > self.width:
                    return

                # Now handle the update.
                if c != " " or not transparent:
                    # Fix up orphaned double-width glyphs that we've just bisected.
                    if x + i + j - 1 >= 0 and self._buffer.get(x + i + j - 1, y)[4] == 2:
                        self._buffer.set(x + i + j - 1, y, (ord("x"), 0, 0, 0, 1))

                    self._buffer.set(x + i + j, y, (ord(c), colour, attr, bg, width))
                    if width == 2:
                        j += 1
                        if x + i + j < self.width:
                            self._buffer.set(x + i + j, y, (ord(c), colour, attr, bg, 0))

                    # Now fix up any glyphs we may have bisected the other way.
                    if x + i + j + 1 < self.width and self._buffer.get(x + i + j + 1, y)[4] == 0:
                        self._buffer.set(x + i + j + 1, y, (ord("x"), 0, 0, 0, 1))

    @property
    def start_line(self):
        """
        :return: The start line of the top of the canvas.
        """
        return self._start_line

    @property
    def unicode_aware(self):
        """
        :return: Whether unicode input/output is supported or not.
        """
        return self._unicode_aware

    @property
    def dimensions(self):
        """
        :return: The full dimensions of the canvas as a (height, width) tuple.
        """
        return self.height, self.width

    @property
    def palette(self):
        """
        :return: A palette compatible with the PIL.
        """
        if self.colours < 256:
            # Use the ANSI colour set.
            return self._8_palette
        else:
            return self._256_palette

    def centre(self, text, y, colour=7, attr=0, colour_map=None):
        """
        Centre the text on the specified line (y) using the optional colour and attributes.

        :param text: The (single line) text to be printed.
        :param y: The line (y coord) for the start of the text.
        :param colour: The colour of the text to be displayed.
        :param attr: The cell attribute of the text to be displayed.
        :param colour_map: Colour/attribute list for multi-colour text.

        The colours and attributes are the COLOUR_xxx and A_yyy constants
        defined in the Screen class.
        """
        if self._unicode_aware:
            x = (self.width - wcswidth(text)) // 2
        else:
            x = (self.width - len(text)) // 2
        self.paint(text, x, y, colour, attr, colour_map=colour_map)

    def paint(self, text, x, y, colour=7, attr=0, bg=0, transparent=False,
              colour_map=None):
        """
        Paint multi-colour text at the defined location.

        :param text: The (single line) text to be printed.
        :param x: The column (x coord) for the start of the text.
        :param y: The line (y coord) for the start of the text.
        :param colour: The default colour of the text to be displayed.
        :param attr: The default cell attribute of the text to be displayed.
        :param bg: The default background colour of the text to be displayed.
        :param transparent: Whether to print spaces or not, thus giving a
            transparent effect.
        :param colour_map: Colour/attribute list for multi-colour text.

        The colours and attributes are the COLOUR_xxx and A_yyy constants
        defined in the Screen class.
        colour_map is a list of tuples (foreground, attribute, background) that
        must be the same length as the passed in text (or None if no mapping is
        required).
        """
        if colour_map is None:
            self.print_at(text, x, y, colour, attr, bg, transparent)
        else:
            offset = 0
            for i, c in enumerate(text):
                if len(colour_map[i]) > 0 and colour_map[i][0] is not None:
                    colour = colour_map[i][0]
                if len(colour_map[i]) > 1 and colour_map[i][1] is not None:
                    attr = colour_map[i][1]
                if len(colour_map[i]) > 2 and colour_map[i][2] is not None:
                    bg = colour_map[i][2]
                self.print_at(c, x + offset, y, colour, attr, bg, transparent)
                offset += wcwidth(c)

    def _blend(self, new, old, ratio):
        """
        Blend the new colour with the old according to the ratio.

        :param new: The new colour (or None if not required).
        :param old: The old colour.
        :param ratio: The ratio to blend new and old
        :returns: the new colour index to use for the required blend.
        """
        # Don't bother blending if none is required.
        if new is None:
            return old

        # Check colour blend cache for a quick answer.
        key = (min(new, old), max(new, old))
        if key in self._blends:
            return self._blends[key]

        # No quick answer - do it the long way...  First lookup the RGB values
        # for both colours and blend.
        (r1, g1, b1) = self.palette[new * 3:new * 3 + 3]
        (r2, g2, b2) = self.palette[old * 3:old * 3 + 3]

        # Helper function to blend RGB values.
        def f(c1, c2):
            return ((c1 * ratio) + (c2 * (100 - ratio))) // 100

        r = f(r1, r2)
        g = f(g1, g2)
        b = f(b1, b2)

        # Now do the reverse lookup...
        nearest = (256 ** 2) * 3
        match = 0
        for c in range(self.colours):
            (rc, gc, bc) = self.palette[c * 3:c * 3 + 3]
            diff = sqrt(((rc - r) * 0.3) ** 2 + ((gc - g) * 0.59) ** 2 +
                        ((bc - b) * 0.11) ** 2)
            if diff < nearest:
                nearest = diff
                match = c

        # Save off the answer and return it
        self._blends[key] = match
        return match

    def highlight(self, x, y, w, h, fg=None, bg=None, blend=100):
        """
        Highlight a specified section of the screen.

        :param x: The column (x coord) for the start of the highlight.
        :param y: The line (y coord) for the start of the highlight.
        :param w: The width of the highlight (in characters).
        :param h: The height of the highlight (in characters).
        :param fg: The foreground colour of the highlight.
        :param bg: The background colour of the highlight.
        :param blend: How much (as a percentage) to take of the new colour
            when blending.

        The colours and attributes are the COLOUR_xxx and A_yyy constants
        defined in the Screen class.  If fg or bg are None that means don't
        change the foreground/background as appropriate.
        """
        for i in range(w):
            if x + i >= self.width or x + i < 0:
                continue

            for j in range(h):
                if y + j >= self._buffer_height or y + j < 0:
                    continue

                old = self._buffer.get(x + i, y + j)
                new_bg = self._blend(bg, old[3], blend)
                new_fg = self._blend(fg, old[1], blend)
                self._buffer.set(x + i, y + j, (old[0], new_fg, old[2], new_bg, old[4]))

    def is_visible(self, x, y):
        """
        Return whether the specified location is on the visible screen.

        :param x: The column (x coord) for the location to check.
        :param y: The line (y coord) for the location to check.
        """
        return ((x >= 0) and
                (x <= self.width) and
                (y >= self._start_line) and
                (y < self._start_line + self.height))

    def move(self, x, y):
        """
        Move the drawing cursor to the specified position.

        :param x: The column (x coord) for the location to check.
        :param y: The line (y coord) for the location to check.
        """
        self._x = int(round(x * 2, 0))
        self._y = int(round(y * 2, 0))

    def draw(self, x, y, char=None, colour=7, bg=0, thin=False):
        """
        Draw a line from drawing cursor to the specified position.

        This uses a modified Bressenham algorithm, interpolating twice as many points to
        render down to anti-aliased characters when no character is specified,
        or uses standard algorithm plotting with the specified character.

        :param x: The column (x coord) for the location to check.
        :param y: The line (y coord) for the location to check.
        :param char: Optional character to use to draw the line.
        :param colour: Optional colour for plotting the line.
        :param bg: Optional background colour for plotting the line.
        :param thin: Optional width of anti-aliased line.
        """
        # Decide what type of line drawing to use.
        line_chars = (self._uni_line_chars if self._unicode_aware else
                      self._line_chars)

        # Define line end points.
        x0 = self._x
        y0 = self._y
        x1 = int(round(x * 2, 0))
        y1 = int(round(y * 2, 0))

        # Remember last point for next line.
        self._x = x1
        self._y = y1

        # Don't bother drawing anything if we're guaranteed to be off-screen
        if ((x0 < 0 and x1 < 0) or (x0 >= self.width * 2 and x1 >= self.width * 2) or
                (y0 < 0 and y1 < 0) or (y0 >= self.height * 2 and y1 >= self.height * 2)):
            return

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)

        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1

        def _get_start_char(cx, cy):
            needle = self.get_from(cx, cy)
            if needle is not None:
                letter, cfg, _, cbg = needle
                if colour == cfg and bg == cbg and chr(letter) in line_chars:
                    return line_chars.find(chr(letter))
            return 0

        def _fast_fill(start_x, end_x, iy):
            next_char = -1
            for ix in range(start_x, end_x):
                if ix % 2 == 0 or next_char == -1:
                    next_char = _get_start_char(ix // 2, iy // 2)
                next_char |= 2 ** abs(ix % 2) * 4 ** (iy % 2)
                if ix % 2 == 1:
                    self.print_at(line_chars[next_char], ix // 2, iy // 2, colour, bg=bg)
            if end_x % 2 == 1:
                self.print_at(line_chars[next_char], end_x // 2, iy // 2, colour, bg=bg)

        def _draw_on_x(ix, iy):
            err = dx
            px = ix - 2
            py = iy - 2
            next_char = 0
            while ix != x1:
                if ix < px or ix - px >= 2 or iy < py or iy - py >= 2:
                    px = ix & ~1
                    py = iy & ~1
                    next_char = _get_start_char(px // 2, py // 2)
                next_char |= 2 ** abs(ix % 2) * 4 ** (iy % 2)
                err -= 2 * dy
                if err < 0:
                    iy += sy
                    err += 2 * dx
                ix += sx

                if char is None:
                    self.print_at(line_chars[next_char],
                                  px // 2, py // 2, colour, bg=bg)
                else:
                    self.print_at(char, px // 2, py // 2, colour, bg=bg)

        def _draw_on_y(ix, iy):
            err = dy
            px = ix - 2
            py = iy - 2
            next_char = 0
            while iy != y1:
                if ix < px or ix - px >= 2 or iy < py or iy - py >= 2:
                    px = ix & ~1
                    py = iy & ~1
                    next_char = _get_start_char(px // 2, py // 2)
                next_char |= 2 ** abs(ix % 2) * 4 ** (iy % 2)
                err -= 2 * dx
                if err < 0:
                    ix += sx
                    err += 2 * dy
                iy += sy

                if char is None:
                    self.print_at(line_chars[next_char],
                                  px // 2, py // 2, colour, bg=bg)
                else:
                    self.print_at(char, px // 2, py // 2, colour, bg=bg)

        if dy == 0 and thin and char is None:
            # Fast-path for polygon filling
            _fast_fill(min(x0, x1), max(x0, x1), y0)
        elif dx > dy:
            _draw_on_x(x0, y0)
            if not thin:
                _draw_on_x(x0, y0 + 1)
        else:
            _draw_on_y(x0, y0)
            if not thin:
                _draw_on_y(x0 + 1, y0)

    def fill_polygon(self, polygons, colour=7, bg=0):
        """
        Draw a filled polygon.

        This function uses the scan line algorithm to create the polygon.  See
        https://www.cs.uic.edu/~jbell/CourseNotes/ComputerGraphics/PolygonFilling.html for details.

        :param polygons: A list of polygons (which are each a list of (x,y) coordinates for the
            points of the polygon) - i.e. nested list of 2-tuples.
        :param colour: The foreground colour to use for the polygon
        :param bg: The background colour to use for the polygon
        """
        def _add_edge(a, b):
            # Ignore horizontal lines - they are redundant
            if a[1] == b[1]:
                return

            # Ignore any edges that do not intersect the visible raster lines at all.
            if (a[1] < 0 and b[1] < 0) or (a[1] >= self.height and b[1] >= self.height):
                return

            # Save off the edge, always starting at the lowest value of y.
            new_edge = _DotDict()
            if a[1] < b[1]:
                new_edge.min_y = a[1]
                new_edge.max_y = b[1]
                new_edge.x = a[0]
                new_edge.dx = (b[0] - a[0]) / (b[1] - a[1]) / 2
            else:
                new_edge.min_y = b[1]
                new_edge.max_y = a[1]
                new_edge.x = b[0]
                new_edge.dx = (a[0] - b[0]) / (a[1] - b[1]) / 2
            edges.append(new_edge)

        # Create a table of all the edges in the polygon, sorted on smallest x.
        logger.debug("Processing polygon: %s", polygons)
        min_y = self.height
        max_y = -1
        edges = []
        last = None
        for polygon in polygons:
            # Ignore lines and polygons.
            if len(polygon) <= 2:
                continue

            # Ignore any polygons completely off the screen
            x, y = zip(*polygon)
            p_min_x = min(x)
            p_max_x = max(x)
            p_min_y = min(y)
            p_max_y = max(y)
            if p_max_x < 0 or p_min_x >= self.width or p_max_y < 0 or p_min_y > self.height:
                continue

            # Build up the edge list, maintaining bounding coordinates on the Y axis.
            min_y = min(p_min_y, min_y)
            max_y = max(p_max_y, max_y)
            for i, point in enumerate(polygon):
                if i != 0:
                    _add_edge(last, point)
                last = point
            _add_edge(polygon[0], polygon[-1])
            edges = sorted(edges, key=lambda e: e.x)

        # Check we still have something to do:
        if len(edges) == 0:
            return

        # Re-base all edges to visible Y coordinates of the screen.
        for edge in edges:
            if edge.min_y < 0:
                edge.x -= int(edge.min_y * 2) * edge.dx
                edge.min_y = 0
        min_y = max(0, min_y)
        max_y = min(max_y - min_y, self.height)

        logger.debug("Resulting edges: %s", edges)

        # Render each line in the bounding rectangle.
        for y in [min_y + (i / 2) for i in range(0, int(max_y) * 2)]:
            # Create a list of live edges (for drawing this raster line) and edges for next
            # iteration of the raster.
            live_edges = []
            new_edges = []
            for edge in edges:
                if edge.min_y <= y <= edge.max_y:
                    live_edges.append(edge)
                if y < edge.max_y:
                    new_edges.append(edge)

            # Draw the portions of the line that are inside the polygon.
            count = 0
            last_x = 0
            for edge in live_edges:
                # Draw the next segment
                if 0 <= y < self.height:
                    if edge.max_y != y:
                        count += 1
                        if count % 2 == 1:
                            last_x = edge.x
                        else:
                            # Don't bother drawing lines entirely off the screen.
                            if not ((last_x < 0 and edge.x < 0) or
                                    (last_x >= self.width and edge.x >= self.width)):
                                # Clip raster to screen width.
                                self.move(max(0, last_x), y)
                                self.draw(
                                    min(edge.x, self.width), y, colour=colour, bg=bg, thin=True)

                # Update the x location for this active edge.
                edge.x += edge.dx

            # Rely on the fact that we have the same dicts in both live_edges and new_edges, so
            # we just need to resort new_edges for the next iteration.
            edges = sorted(new_edges, key=lambda e: e.x)


class Canvas(_AbstractCanvas):
    """
    A Canvas is an object that can be used to draw to the screen. It maintains
    its own buffer that will be flushed to the screen when `refresh()` is
    called.
    """

    def __init__(self, screen, height, width, x=None, y=None):
        """
        :param screen: The underlying Screen that will be drawn to on refresh.
        :param height: The height of the screen buffer to be used.
        :param width: The width of the screen buffer to be used.
        :param x: The x position for the top left corner of the Canvas.
        :param y: The y position for the top left corner of the Canvas.

        If either of the x or y positions is not set, the Canvas will default
        to centring within the current Screen for that location.
        """
        # Save off the screen details.
        # TODO: Fix up buffer logic once and for all - wait for v2.0
        super(Canvas, self).__init__(
            height, width, 200, screen.colours, screen.unicode_aware)
        self._screen = screen
        self._dx = (screen.width - width) // 2 if x is None else x
        self._dy = (screen.height - height) // 2 if y is None else y

    def refresh(self):
        """
        Flush the canvas content to the underlying screen.
        """
        for y in range(self.height):
            for x in range(self.width):
                c = self._buffer.get(x, y + self._start_line)
                if c[4] != 0:
                    self._screen.print_at(chr(c[0]), x + self._dx, y + self._dy, c[1], c[2], c[3])

    def _reset(self):
        # Nothing needed for a Canvas
        pass

    @property
    def origin(self):
        """
        The location of top left corner of the canvas on the Screen.

        :returns: A tuple (x, y) of the location
        """
        return self._dx, self._dy


class Screen(with_metaclass(ABCMeta, _AbstractCanvas)):
    """
    Class to track basic state of the screen.  This constructs the necessary
    resources to allow us to do the ASCII animations.

    This is an abstract class that will build the correct concrete class for
    you when you call :py:meth:`.wrapper`.  If needed, you can use the
    :py:meth:`~.Screen.open` and :py:meth:`~.Screen.close` methods for finer
    grained control of the construction and tidy up.

    Note that you need to define the required height for your screen buffer.
    This is important if you plan on using any Effects that will scroll the
    screen vertically (e.g. Scroll).  It must be big enough to handle the
    full scrolling of your selected Effect.
    """

    # Text attributes for use when printing to the Screen.
    A_BOLD = 1
    A_NORMAL = 2
    A_REVERSE = 3
    A_UNDERLINE = 4

    # Text colours for use when printing to the Screen.
    COLOUR_BLACK = 0
    COLOUR_RED = 1
    COLOUR_GREEN = 2
    COLOUR_YELLOW = 3
    COLOUR_BLUE = 4
    COLOUR_MAGENTA = 5
    COLOUR_CYAN = 6
    COLOUR_WHITE = 7

    # Standard extended key codes.
    KEY_ESCAPE = -1
    KEY_F1 = -2
    KEY_F2 = -3
    KEY_F3 = -4
    KEY_F4 = -5
    KEY_F5 = -6
    KEY_F6 = -7
    KEY_F7 = -8
    KEY_F8 = -9
    KEY_F9 = -10
    KEY_F10 = -11
    KEY_F11 = -12
    KEY_F12 = -13
    KEY_F13 = -14
    KEY_F14 = -15
    KEY_F15 = -16
    KEY_F16 = -17
    KEY_F17 = -18
    KEY_F18 = -19
    KEY_F19 = -20
    KEY_F20 = -21
    KEY_F21 = -22
    KEY_F22 = -23
    KEY_F23 = -24
    KEY_F24 = -25
    KEY_PRINT_SCREEN = -100
    KEY_INSERT = -101
    KEY_DELETE = -102
    KEY_HOME = -200
    KEY_END = -201
    KEY_LEFT = -203
    KEY_UP = -204
    KEY_RIGHT = -205
    KEY_DOWN = -206
    KEY_PAGE_UP = -207
    KEY_PAGE_DOWN = -208
    KEY_BACK = -300
    KEY_TAB = -301
    KEY_BACK_TAB = -302
    KEY_NUMPAD0 = -400
    KEY_NUMPAD1 = -401
    KEY_NUMPAD2 = -402
    KEY_NUMPAD3 = -403
    KEY_NUMPAD4 = -404
    KEY_NUMPAD5 = -405
    KEY_NUMPAD6 = -406
    KEY_NUMPAD7 = -407
    KEY_NUMPAD8 = -408
    KEY_NUMPAD9 = -409
    KEY_MULTIPLY = -410
    KEY_ADD = -411
    KEY_SUBTRACT = -412
    KEY_DECIMAL = -413
    KEY_DIVIDE = -414
    KEY_CAPS_LOCK = -500
    KEY_NUM_LOCK = -501
    KEY_SCROLL_LOCK = -502
    KEY_SHIFT = -600
    KEY_CONTROL = -601
    KEY_MENU = -602

    def __init__(self, height, width, buffer_height, unicode_aware):
        """
        Don't call this constructor directly.
        """
        super(Screen, self).__init__(
            height, width, buffer_height, 0, unicode_aware)

        # Initialize base class variables - e.g. those used for drawing.
        self.height = height
        self.width = width
        self._last_start_line = 0

        # Set up internal state for colours - used by children to determine
        # changes to text colour when refreshing the screen.
        self._colour = 0
        self._attr = 0
        self._bg = 0

        # tracking of current cursor position - used in screen refresh.
        self._cur_x = 0
        self._cur_y = 0

        # Control variables for playing out a set of Scenes.
        self._scenes = []
        self._scene_index = 0
        self._frame = 0
        self._idle_frame_count = 0
        self._forced_update = False
        self._unhandled_input = self._unhandled_event_default

    @classmethod
    def open(cls, height=200, catch_interrupt=False, unicode_aware=None):
        """
        Construct a new Screen for any platform.  This will just create the
        correct Screen object for your environment.  See :py:meth:`.wrapper` for
        a function to create and tidy up once you've finished with the Screen.

        :param height: The buffer height for this window (if using scrolling).
        :param catch_interrupt: Whether to catch and prevent keyboard
            interrupts.  Defaults to False to maintain backwards compatibility.
        :param unicode_aware: Whether the application can use unicode or not.
            If None, try to detect from the environment if UTF-8 is enabled.
        """
        if sys.platform == "win32":
            # Clone the standard output buffer so that we can do whatever we
            # need for the application, but restore the buffer at the end.
            # Note that we need to resize the clone to ensure that it is the
            # same size as the original in some versions of Windows.
            old_out = win32console.PyConsoleScreenBufferType(
                win32file.CreateFile("CONOUT$",
                                     win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                                     win32file.FILE_SHARE_WRITE,
                                     None,
                                     win32file.OPEN_ALWAYS,
                                     0,
                                     None))
            try:
                info = old_out.GetConsoleScreenBufferInfo()
            except pywintypes.error:
                info = None
            win_out = win32console.CreateConsoleScreenBuffer()
            if info:
                win_out.SetConsoleScreenBufferSize(info['Size'])
            else:
                win_out.SetStdHandle(win32console.STD_OUTPUT_HANDLE)
            win_out.SetConsoleActiveScreenBuffer()

            # Get the standard input buffer.
            win_in = win32console.PyConsoleScreenBufferType(
                win32file.CreateFile("CONIN$",
                                     win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                                     win32file.FILE_SHARE_READ,
                                     None,
                                     win32file.OPEN_ALWAYS,
                                     0,
                                     None))
            win_in.SetStdHandle(win32console.STD_INPUT_HANDLE)

            # Hide the cursor.
            win_out.SetConsoleCursorInfo(1, 0)

            # Disable scrolling
            out_mode = win_out.GetConsoleMode()
            win_out.SetConsoleMode(
                out_mode & ~ win32console.ENABLE_WRAP_AT_EOL_OUTPUT)

            # Enable mouse input, disable quick-edit mode and disable ctrl-c
            # if needed.
            in_mode = win_in.GetConsoleMode()
            new_mode = (in_mode | win32console.ENABLE_MOUSE_INPUT |
                        ENABLE_EXTENDED_FLAGS)
            new_mode &= ~ENABLE_QUICK_EDIT_MODE
            if catch_interrupt:
                # Ignore ctrl-c handlers if specified.
                new_mode &= ~win32console.ENABLE_PROCESSED_INPUT
            win_in.SetConsoleMode(new_mode)

            screen = _WindowsScreen(win_out, win_in, height, old_out, in_mode,
                                    unicode_aware=unicode_aware)
        else:
            # Reproduce curses.wrapper()
            stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            stdscr.keypad(1)

            # Fed up with linters complaining about original curses code - trying to be a bit better...
            # noinspection PyBroadException
            # pylint: disable=broad-except
            try:
                curses.start_color()
            except Exception as e:
                logger.debug(e)
            screen = _CursesScreen(stdscr, height,
                                   catch_interrupt=catch_interrupt,
                                   unicode_aware=unicode_aware)

        return screen

    @abstractmethod
    def close(self, restore=True):
        """
        Close down this Screen and tidy up the environment as required.

        :param restore: whether to restore the environment or not.
        """

    @classmethod
    def wrapper(cls, func, height=200, catch_interrupt=False, arguments=None,
                unicode_aware=None):
        """
        Construct a new Screen for any platform.  This will initialize the
        Screen, call the specified function and then tidy up the system as
        required when the function exits.

        :param func: The function to call once the Screen has been created.
        :param height: The buffer height for this Screen (if using scrolling).
        :param catch_interrupt: Whether to catch and prevent keyboard
            interrupts.  Defaults to False to maintain backwards compatibility.
        :param arguments: Optional arguments list to pass to func (after the
            Screen object).
        :param unicode_aware: Whether the application can use unicode or not.
            If None, try to detect from the environment if UTF-8 is enabled.
        """
        screen = Screen.open(height,
                             catch_interrupt=catch_interrupt,
                             unicode_aware=unicode_aware)
        restore = True
        try:
            try:
                if arguments:
                    return func(screen, *arguments)
                else:
                    return func(screen)
            except ResizeScreenError:
                restore = False
                raise
        finally:
            screen.close(restore)

    def _reset(self):
        """
        Reset the Screen.
        """
        self._last_start_line = 0
        self._colour = None
        self._attr = None
        self._bg = None
        self._cur_x = None
        self._cur_y = None

    def refresh(self):
        """
        Refresh the screen.
        """
        # Scroll the screen as required to minimize redrawing.
        if self._last_start_line != self._start_line:
            self._scroll(self._start_line - self._last_start_line)
            if self._start_line > self._last_start_line:
                self._buffer.invalidate(self._last_start_line + self.height, self._start_line + self.height)
            else:
                self._buffer.invalidate(self._start_line, self._last_start_line)
            self._last_start_line = self._start_line

        # Now draw any deltas to the scrolled screen.  Note that CJK character sets sometimes
        # use double-width characters, so don't try to draw the next character if we hit one.
        for y, x in self._buffer.deltas(self._last_start_line, self.height):
            new_cell = self._buffer.get(x, y)
            self._change_colours(new_cell[1], new_cell[2], new_cell[3])
            self._print_at(chr(new_cell[0]), x, y - self._last_start_line, new_cell[4])

        # Resynch for next refresh.
        self._buffer.sync()

    def clear(self):
        """
        Clear the Screen of all content.

        Note that this will instantly clear the Screen and reset all buffers to the default state,
        without waiting for you to call :py:meth:`~.Screen.refresh`.
        """
        # Clear the actual terminal
        self.reset()
        self._change_colours(Screen.COLOUR_WHITE, 0, 0)
        self._clear()

    def get_key(self):
        """
        Check for a key without waiting.  This method is deprecated.  Use
        :py:meth:`.get_event` instead.
        """
        event = self.get_event()
        if event and isinstance(event, KeyboardEvent):
            return event.key_code
        return None

    @abstractmethod
    def get_event(self):
        """
        Check for any events (e.g. key-press or mouse movement) without waiting.

        :returns: A :py:obj:`.Event` object if anything was detected, otherwise
                  it returns None.
        """

    @staticmethod
    def ctrl(char):
        """
        Calculate the control code for a given key.  For example, this converts
        "a" to 1 (which is the code for ctrl-a).

        :param char: The key to convert to a control code.
        :return: The control code as an integer or None if unknown.
        """
        # Convert string to int... assuming any non-integer is a string.
        # TODO: Consider asserting a more rigorous test without falling back to past basestring.
        if not isinstance(char, int):
            char = ord(char.upper())

        # Only deal with the characters between '@' and '_'
        return char & 0x1f if 64 <= char <= 95 else None

    @abstractmethod
    def has_resized(self):
        """
        Check whether the screen has been re-sized.

        :returns: True when the screen has been re-sized since the last check.
        """

    def getch(self, x, y):
        """
        Get the character at a specified location.  This method is deprecated.
        Use :py:meth:`.get_from` instead.

        :param x: The x coordinate.
        :param y: The y coordinate.
        """
        return self.get_from(x, y)

    def putch(self, text, x, y, colour=7, attr=0, bg=0, transparent=False):
        """
        Print text at the specified location.  This method is deprecated.  Use
        :py:meth:`.print_at` instead.

        :param text: The (single line) text to be printed.
        :param x: The column (x coord) for the start of the text.
        :param y: The line (y coord) for the start of the text.
        :param colour: The colour of the text to be displayed.
        :param attr: The cell attribute of the text to be displayed.
        :param bg: The background colour of the text to be displayed.
        :param transparent: Whether to print spaces or not, thus giving a
            transparent effect.
        """
        self.print_at(text, x, y, colour, attr, bg, transparent)

    @staticmethod
    def _unhandled_event_default(event):
        """
        Default unhandled event handler for handling simple scene navigation.
        """
        if isinstance(event, KeyboardEvent):
            c = event.key_code
            if c in (ord("X"), ord("x"), ord("Q"), ord("q")):
                raise StopApplication("User terminated app")
            if c in (ord(" "), ord("\n"), ord("\r")):
                raise NextScene()

    def play(self, scenes, stop_on_resize=False, unhandled_input=None,
             start_scene=None, repeat=True, allow_int=False):
        """
        Play a set of scenes.

        This is effectively a helper function to wrap :py:meth:`.set_scenes` and
        :py:meth:`.draw_next_frame` to simplify animation for most applications.

        :param scenes: a list of :py:obj:`.Scene` objects to play.
        :param stop_on_resize: Whether to stop when the screen is resized.
            Default is to carry on regardless - which will typically result
            in an error. This is largely done for back-compatibility.
        :param unhandled_input: Function to call for any input not handled
            by the Scenes/Effects being played.  Defaults to a function that
            closes the application on "Q" or "X" being pressed.
        :param start_scene: The old Scene to start from.  This must have name
            that matches the name of one of the Scenes passed in.
        :param repeat: Whether to repeat the Scenes once it has reached the end.
            Defaults to True.
        :param allow_int: Allow input to interrupt frame rate delay.

        :raises ResizeScreenError: if the screen is resized (and allowed by
            stop_on_resize).

        The unhandled input function just takes one parameter - the input
        event that was not handled.
        """
        # Initialise the Screen for animation.
        self.set_scenes(
            scenes, unhandled_input=unhandled_input, start_scene=start_scene)

        # Mainline loop for animations
        try:
            while True:
                a = time.time()
                self.draw_next_frame(repeat=repeat)
                if self.has_resized():
                    if stop_on_resize:
                        self._scenes[self._scene_index].exit()
                        raise ResizeScreenError("Screen resized",
                                                self._scenes[self._scene_index])
                b = time.time()
                if b - a < 0.05:
                    if allow_int:
                        self._wait_for_input(a + 0.05 - b)
                    else:
                        time.sleep(a + 0.05 - b)
        except StopApplication:
            # Time to stop  - just exit the function.
            return

    def set_scenes(self, scenes, unhandled_input=None, start_scene=None):
        """
        Remember a set of scenes to be played.  This must be called before
        using :py:meth:`.draw_next_frame`.

        :param scenes: a list of :py:obj:`.Scene` objects to play.
        :param unhandled_input: Function to call for any input not handled
            by the Scenes/Effects being played.  Defaults to a function that
            closes the application on "Q" or "X" being pressed.
        :param start_scene: The old Scene to start from.  This must have name
            that matches the name of one of the Scenes passed in.

        :raises ResizeScreenError: if the screen is resized (and allowed by
            stop_on_resize).

        The unhandled input function just takes one parameter - the input
        event that was not handled.
        """
        # Save off the scenes now.
        self._scenes = scenes

        # Set up default unhandled input handler if needed.
        if unhandled_input is None:
            # Check that none of the Effects is incompatible with the default
            # handler.
            safe = True
            for scene in self._scenes:
                for effect in scene.effects:
                    safe &= effect.safe_to_default_unhandled_input
            if safe:
                unhandled_input = self._unhandled_event_default
        self._unhandled_input = unhandled_input

        # Find the starting scene.  Default to first if no match.
        self._scene_index = 0
        if start_scene is not None:
            for i, scene in enumerate(scenes):
                if scene.name == start_scene.name:
                    self._scene_index = i
                    break

        # Reset the Scene - this allows the original scene to pick up old
        # values on resizing.
        self._scenes[self._scene_index].reset(
            old_scene=start_scene, screen=self)

        # Reset other internal state for the animation
        self._frame = 0
        self._idle_frame_count = 0
        self._forced_update = False
        self.clear()

    def draw_next_frame(self, repeat=True):
        """
        Draw the next frame in the currently configured Scenes. You must call
        :py:meth:`.set_scenes` before using this for the first time.

        :param repeat: Whether to repeat the Scenes once it has reached the end.
            Defaults to True.

        :raises StopApplication: if the application should be terminated.
        """
        scene = self._scenes[self._scene_index]
        try:
            # Check for an event now and remember for refresh reasons.
            event = self.get_event()
            got_event = event is not None

            # Now process all the input events
            while event is not None:
                event = scene.process_event(event)
                if event is not None and self._unhandled_input is not None:
                    self._unhandled_input(event)
                event = self.get_event()

            # Only bother with a refresh if there was an event to process or
            # we have to refresh due to the refresh limit required for an
            # Effect.
            self._frame += 1
            self._idle_frame_count -= 1
            if got_event or self._idle_frame_count <= 0 or self._forced_update:
                self._forced_update = False
                self._idle_frame_count = 1000000
                for effect in scene.effects:
                    # Update the effect and delete if needed.
                    effect.update(self._frame)
                    if effect.delete_count is not None:
                        effect.delete_count -= 1
                        if effect.delete_count <= 0:
                            scene.remove_effect(effect)

                    # Sort out when we next _need_ to do a refresh.
                    if effect.frame_update_count > 0:
                        self._idle_frame_count = min(self._idle_frame_count,
                                                     effect.frame_update_count)
                self.refresh()

            if 0 < scene.duration <= self._frame:
                raise NextScene()
        except NextScene as e:
            # Tidy up the current scene.
            scene.exit()

            # Find the specified next Scene
            if e.name is None:
                # Just allow next iteration of loop
                self._scene_index += 1
                if self._scene_index >= len(self._scenes):
                    if repeat:
                        self._scene_index = 0
                    else:
                        raise StopApplication("Repeat disabled")
            else:
                # Find the required scene.
                for i, scene in enumerate(self._scenes):
                    if scene.name == e.name:
                        self._scene_index = i
                        break
                else:
                    raise RuntimeError(
                        "Could not find Scene: '{}'".format(e.name))

            # Reset the screen if needed.
            scene = self._scenes[self._scene_index]
            scene.reset()
            self._frame = 0
            self._idle_frame_count = 0
            if scene.clear:
                self.clear()

    @property
    def current_scene(self):
        """
        :return: The scene currently being rendered. To be used in conjunction
                 with :py:meth:`.draw_next_frame`.
        """
        return self._scenes[self._scene_index]

    def force_update(self):
        """
        Force the Screen to redraw the current Scene on the next call to
        draw_next_frame, overriding the frame_update_count value for all the
        Effects.
        """
        self._forced_update = True

    @abstractmethod
    def _change_colours(self, colour, attr, bg):
        """
        Change current colour if required.

        :param colour: New colour to use.
        :param attr: New attributes to use.
        :param bg: New background colour to use.
        """

    @abstractmethod
    def _wait_for_input(self, timeout):
        """
        Wait until there is some input or the timeout is hit.

        :param timeout: Time to wait for input in seconds (floating point).
        """

    @abstractmethod
    def _print_at(self, text, x, y, width):
        """
        Print string at the required location.

        :param text: The text string to print.
        :param x: The x coordinate
        :param y: The Y coordinate
        :param width: The width of the character (for dual-width glyphs in CJK languages).
        """

    @abstractmethod
    def _clear(self):
        """
        Clear the window.
        """

    @abstractmethod
    def _scroll(self, lines):
        """
        Scroll the window up or down.

        :param lines: Number of lines to scroll.  Negative numbers scroll down.
        """

    @abstractmethod
    def set_title(self, title):
        """
        Set the title for this terminal/console session.  This will typically
        change the text displayed in the window title bar.

        :param title: The title to be set.
        """


if sys.platform == "win32":
    import win32con
    import win32console
    import win32file
    import pywintypes

    class _WindowsScreen(Screen):
        """
        Windows screen implementation.
        """

        # Virtual key code mapping.
        _KEY_MAP = {
            win32con.VK_ESCAPE: Screen.KEY_ESCAPE,
            win32con.VK_F1: Screen.KEY_F1,
            win32con.VK_F2: Screen.KEY_F2,
            win32con.VK_F3: Screen.KEY_F3,
            win32con.VK_F4: Screen.KEY_F4,
            win32con.VK_F5: Screen.KEY_F5,
            win32con.VK_F6: Screen.KEY_F6,
            win32con.VK_F7: Screen.KEY_F7,
            win32con.VK_F8: Screen.KEY_F8,
            win32con.VK_F9: Screen.KEY_F9,
            win32con.VK_F10: Screen.KEY_F10,
            win32con.VK_F11: Screen.KEY_F11,
            win32con.VK_F12: Screen.KEY_F12,
            win32con.VK_F13: Screen.KEY_F13,
            win32con.VK_F14: Screen.KEY_F14,
            win32con.VK_F15: Screen.KEY_F15,
            win32con.VK_F16: Screen.KEY_F16,
            win32con.VK_F17: Screen.KEY_F17,
            win32con.VK_F18: Screen.KEY_F18,
            win32con.VK_F19: Screen.KEY_F19,
            win32con.VK_F20: Screen.KEY_F20,
            win32con.VK_F21: Screen.KEY_F21,
            win32con.VK_F22: Screen.KEY_F22,
            win32con.VK_F23: Screen.KEY_F23,
            win32con.VK_F24: Screen.KEY_F24,
            win32con.VK_PRINT: Screen.KEY_PRINT_SCREEN,
            win32con.VK_INSERT: Screen.KEY_INSERT,
            win32con.VK_DELETE: Screen.KEY_DELETE,
            win32con.VK_HOME: Screen.KEY_HOME,
            win32con.VK_END: Screen.KEY_END,
            win32con.VK_LEFT: Screen.KEY_LEFT,
            win32con.VK_UP: Screen.KEY_UP,
            win32con.VK_RIGHT: Screen.KEY_RIGHT,
            win32con.VK_DOWN: Screen.KEY_DOWN,
            win32con.VK_PRIOR: Screen.KEY_PAGE_UP,
            win32con.VK_NEXT: Screen.KEY_PAGE_DOWN,
            win32con.VK_BACK: Screen.KEY_BACK,
            win32con.VK_TAB: Screen.KEY_TAB
        }

        _EXTRA_KEY_MAP = {
            win32con.VK_NUMPAD0: Screen.KEY_NUMPAD0,
            win32con.VK_NUMPAD1: Screen.KEY_NUMPAD1,
            win32con.VK_NUMPAD2: Screen.KEY_NUMPAD2,
            win32con.VK_NUMPAD3: Screen.KEY_NUMPAD3,
            win32con.VK_NUMPAD4: Screen.KEY_NUMPAD4,
            win32con.VK_NUMPAD5: Screen.KEY_NUMPAD5,
            win32con.VK_NUMPAD6: Screen.KEY_NUMPAD6,
            win32con.VK_NUMPAD7: Screen.KEY_NUMPAD7,
            win32con.VK_NUMPAD8: Screen.KEY_NUMPAD8,
            win32con.VK_NUMPAD9: Screen.KEY_NUMPAD9,
            win32con.VK_MULTIPLY: Screen.KEY_MULTIPLY,
            win32con.VK_ADD: Screen.KEY_ADD,
            win32con.VK_SUBTRACT: Screen.KEY_SUBTRACT,
            win32con.VK_DECIMAL: Screen.KEY_DECIMAL,
            win32con.VK_DIVIDE: Screen.KEY_DIVIDE,
            win32con.VK_CAPITAL: Screen.KEY_CAPS_LOCK,
            win32con.VK_NUMLOCK: Screen.KEY_NUM_LOCK,
            win32con.VK_SCROLL: Screen.KEY_SCROLL_LOCK,
            win32con.VK_SHIFT: Screen.KEY_SHIFT,
            win32con.VK_CONTROL: Screen.KEY_CONTROL,
            win32con.VK_MENU: Screen.KEY_MENU,
        }

        # Foreground colour lookup table.
        _COLOURS = {
            Screen.COLOUR_BLACK: 0,
            Screen.COLOUR_RED: win32console.FOREGROUND_RED,
            Screen.COLOUR_GREEN: win32console.FOREGROUND_GREEN,
            Screen.COLOUR_YELLOW: (win32console.FOREGROUND_RED |
                                   win32console.FOREGROUND_GREEN),
            Screen.COLOUR_BLUE: win32console.FOREGROUND_BLUE,
            Screen.COLOUR_MAGENTA: (win32console.FOREGROUND_RED |
                                    win32console.FOREGROUND_BLUE),
            Screen.COLOUR_CYAN: (win32console.FOREGROUND_BLUE |
                                 win32console.FOREGROUND_GREEN),
            Screen.COLOUR_WHITE: (win32console.FOREGROUND_RED |
                                  win32console.FOREGROUND_GREEN |
                                  win32console.FOREGROUND_BLUE)
        }

        # Background colour lookup table.
        _BG_COLOURS = {
            Screen.COLOUR_BLACK: 0,
            Screen.COLOUR_RED: win32console.BACKGROUND_RED,
            Screen.COLOUR_GREEN: win32console.BACKGROUND_GREEN,
            Screen.COLOUR_YELLOW: (win32console.BACKGROUND_RED |
                                   win32console.BACKGROUND_GREEN),
            Screen.COLOUR_BLUE: win32console.BACKGROUND_BLUE,
            Screen.COLOUR_MAGENTA: (win32console.BACKGROUND_RED |
                                    win32console.BACKGROUND_BLUE),
            Screen.COLOUR_CYAN: (win32console.BACKGROUND_BLUE |
                                 win32console.BACKGROUND_GREEN),
            Screen.COLOUR_WHITE: (win32console.BACKGROUND_RED |
                                  win32console.BACKGROUND_GREEN |
                                  win32console.BACKGROUND_BLUE)
        }

        # Attribute lookup table
        _ATTRIBUTES = {
            0: lambda x: x,
            Screen.A_BOLD: lambda x: x | win32console.FOREGROUND_INTENSITY,
            Screen.A_NORMAL: lambda x: x,
            # Windows console uses a bitmap where background is the top nibble,
            # so we can reverse by swapping nibbles.
            Screen.A_REVERSE: lambda x: ((x & 15) * 16) + ((x & 240) // 16),
            Screen.A_UNDERLINE: lambda x: x
        }

        def __init__(self, stdout, stdin, buffer_height, old_out, old_in,
                     unicode_aware=False):
            """
            :param stdout: The win32console PyConsoleScreenBufferType object for
                stdout.
            :param stdin: The win32console PyConsoleScreenBufferType object for
                stdin.
            :param buffer_height: The buffer height for this window (if using
                scrolling).
            :param old_out: The original win32console PyConsoleScreenBufferType
                object for stdout that should be restored on exit.
            :param old_in: The original stdin state that should be restored on
                exit.
            :param unicode_aware: Whether this Screen can use unicode or not.
            """
            # Save off the screen details and set up the scrolling pad.
            info = stdout.GetConsoleScreenBufferInfo()['Window']
            width = info.Right - info.Left + 1
            height = info.Bottom - info.Top + 1

            # Detect UTF-8 if needed and then construct the Screen.
            if unicode_aware is None:
                # According to MSDN, 65001 is the Windows UTF-8 code page.
                unicode_aware = win32console.GetConsoleCP() == 65001
            super(_WindowsScreen, self).__init__(
                height, width, buffer_height, unicode_aware)

            # Save off the console details.
            self._stdout = stdout
            self._stdin = stdin
            self._last_width = width
            self._last_height = height
            self._old_out = old_out
            self._old_in = old_in

            # Windows is limited to the ANSI colour set.
            self.colours = 8

            # Opt for compatibility with Linux by default
            self._map_all = False

            # Set of keys currently pressed.
            self._keys = set()

        def close(self, restore=True):
            """
            Close down this Screen and tidy up the environment as required.

            :param restore: whether to restore the environment or not.
            """
            if restore:
                # Reset the original screen settings.
                self._old_out.SetConsoleActiveScreenBuffer()
                self._stdin.SetConsoleMode(self._old_in)

        def map_all_keys(self, state):
            """
            Switch on extended keyboard mapping for this Screen.

            :param state: Boolean flag where true means map all keys.

            Enabling this setting will allow Windows to tell you when any key
            is pressed, including metakeys (like shift and control) and whether
            the numeric keypad keys have been used.

            .. warning::

                Using this means your application will not be compatible across
                all platforms.
            """
            self._map_all = state

        def get_event(self):
            """
            Check for any event without waiting.
            """
            # Look for a new event and consume it if there is one.
            while len(self._stdin.PeekConsoleInput(1)) > 0:
                event = self._stdin.ReadConsoleInput(1)[0]
                if event.EventType == win32console.KEY_EVENT:
                    # Pasting unicode text appears to just generate key-up
                    # events (as if you had pressed the Alt keys plus the
                    # keypad code for the character), but the rest of the
                    # console input simply doesn't
                    # work with key up events - e.g. misses keyboard repeats.
                    #
                    # We therefore allow any key press (i.e. KeyDown) event and
                    # _any_ event that appears to have popped up from nowhere
                    # as long as the Alt key is present.
                    key_code = ord(event.Char)
                    logger.debug("Processing key: %x", key_code)
                    if (event.KeyDown or
                            (key_code > 0 and key_code not in self._keys and
                             event.VirtualKeyCode == win32con.VK_MENU)):
                        # Record any keys that were pressed.
                        if event.KeyDown:
                            self._keys.add(key_code)

                        # Translate keys into a KeyboardEvent object.
                        if event.VirtualKeyCode in self._KEY_MAP:
                            key_code = self._KEY_MAP[event.VirtualKeyCode]

                        # Sadly, we are limited to Linux terminal input and so
                        # can't return modifier states in a cross-platform way.
                        # If the user decided not to be cross-platform, so be
                        # it, otherwise map some standard bindings for extended
                        # keys.
                        if (self._map_all and
                                event.VirtualKeyCode in self._EXTRA_KEY_MAP):
                            key_code = self._EXTRA_KEY_MAP[event.VirtualKeyCode]
                        else:
                            if (event.VirtualKeyCode == win32con.VK_TAB and
                                    event.ControlKeyState &
                                    win32con.SHIFT_PRESSED):
                                key_code = Screen.KEY_BACK_TAB

                        # Don't return anything if we didn't have a valid
                        # mapping.
                        if key_code:
                            return KeyboardEvent(key_code)
                    else:
                        # Tidy up any key that was previously pressed.  At
                        # start-up, we may be mid-key, so can't assume this must
                        # always match up.
                        if key_code in self._keys:
                            self._keys.remove(key_code)

                elif event.EventType == win32console.MOUSE_EVENT:
                    # Translate into a MouseEvent object.
                    logger.debug("Processing mouse: %d, %d",
                                 event.MousePosition.X, event.MousePosition.Y)
                    button = 0
                    if event.EventFlags == 0:
                        # Button pressed - translate it.
                        if (event.ButtonState &
                                win32con.FROM_LEFT_1ST_BUTTON_PRESSED != 0):
                            button |= MouseEvent.LEFT_CLICK
                        if (event.ButtonState &
                                win32con.RIGHTMOST_BUTTON_PRESSED != 0):
                            button |= MouseEvent.RIGHT_CLICK
                    elif event.EventFlags & win32con.DOUBLE_CLICK != 0:
                        button |= MouseEvent.DOUBLE_CLICK

                    return MouseEvent(event.MousePosition.X,
                                      event.MousePosition.Y,
                                      button)

            # If we get here, we've fully processed the event queue and found
            # nothing interesting.
            return None

        def has_resized(self):
            """
            Check whether the screen has been re-sized.
            """
            # Get the current Window dimensions and check them against last
            # time.
            re_sized = False
            info = self._stdout.GetConsoleScreenBufferInfo()['Window']
            width = info.Right - info.Left + 1
            height = info.Bottom - info.Top + 1
            if width != self._last_width or height != self._last_height:
                re_sized = True
            return re_sized

        def _change_colours(self, colour, attr, bg):
            """
            Change current colour if required.

            :param colour: New colour to use.
            :param attr: New attributes to use.
            :param bg: New background colour to use.
            """
            # Change attribute first as this will reset colours when swapping
            # modes.
            if colour != self._colour or attr != self._attr or self._bg != bg:
                new_attr = self._ATTRIBUTES[attr](
                    self._COLOURS[colour] + self._BG_COLOURS[bg])
                self._stdout.SetConsoleTextAttribute(new_attr)
                self._attr = attr
                self._colour = colour
                self._bg = bg

        def _print_at(self, text, x, y, width):
            """
            Print string at the required location.

            :param text: The text string to print.
            :param x: The x coordinate
            :param y: The Y coordinate
            :param width: The width of the character (for dual-width glyphs in CJK languages).
            """
            # We can throw temporary errors on resizing, so catch and ignore
            # them on the assumption that we'll resize shortly.
            try:
                # Move the cursor if necessary
                if x != self._cur_x or y != self._cur_y:
                    self._stdout.SetConsoleCursorPosition(
                        win32console.PyCOORDType(x, y))

                # Print the text at the required location and update the current
                # position.
                self._stdout.WriteConsole(text)
                self._cur_x = x + width
                self._cur_y = y
            except pywintypes.error:
                pass

        def _wait_for_input(self, timeout):
            """
            Wait until there is some input or the timeout is hit.

            :param timeout: Time to wait for input in seconds (floating point).
            """
            # TODO: Fix up for Windows
            time.sleep(timeout)

        def _scroll(self, lines):
            """
            Scroll the window up or down.

            :param lines: Number of lines to scroll.  Negative numbers scroll
                down.
            """
            # Scroll the visible screen up by one line
            info = self._stdout.GetConsoleScreenBufferInfo()['Window']
            rectangle = win32console.PySMALL_RECTType(
                info.Left, info.Top + lines, info.Right, info.Bottom)
            new_pos = win32console.PyCOORDType(0, info.Top)
            self._stdout.ScrollConsoleScreenBuffer(
                rectangle, None, new_pos, " ", 0)

        def _clear(self):
            """
            Clear the terminal.
            """
            info = self._stdout.GetConsoleScreenBufferInfo()['Window']
            width = info.Right - info.Left + 1
            height = info.Bottom - info.Top + 1
            box_size = width * height
            self._stdout.FillConsoleOutputAttribute(
                0, box_size, win32console.PyCOORDType(0, 0))
            self._stdout.FillConsoleOutputCharacter(
                " ", box_size, win32console.PyCOORDType(0, 0))
            self._stdout.SetConsoleCursorPosition(
                win32console.PyCOORDType(0, 0))

        def set_title(self, title):
            """
            Set the title for this terminal/console session.  This will
            typically change the text displayed in the window title bar.

            :param title: The title to be set.
            """
            win32console.SetConsoleTitle(title)

else:
    # UNIX compatible platform - use curses
    import curses
    import select
    import termios

    class _CursesScreen(Screen):
        """
        Curses screen implementation.
        """

        # Virtual key code mapping.
        _KEY_MAP = {
            27: Screen.KEY_ESCAPE,
            curses.KEY_F1: Screen.KEY_F1,
            curses.KEY_F2: Screen.KEY_F2,
            curses.KEY_F3: Screen.KEY_F3,
            curses.KEY_F4: Screen.KEY_F4,
            curses.KEY_F5: Screen.KEY_F5,
            curses.KEY_F6: Screen.KEY_F6,
            curses.KEY_F7: Screen.KEY_F7,
            curses.KEY_F8: Screen.KEY_F8,
            curses.KEY_F9: Screen.KEY_F9,
            curses.KEY_F10: Screen.KEY_F10,
            curses.KEY_F11: Screen.KEY_F11,
            curses.KEY_F12: Screen.KEY_F12,
            curses.KEY_F13: Screen.KEY_F13,
            curses.KEY_F14: Screen.KEY_F14,
            curses.KEY_F15: Screen.KEY_F15,
            curses.KEY_F16: Screen.KEY_F16,
            curses.KEY_F17: Screen.KEY_F17,
            curses.KEY_F18: Screen.KEY_F18,
            curses.KEY_F19: Screen.KEY_F19,
            curses.KEY_F20: Screen.KEY_F20,
            curses.KEY_F21: Screen.KEY_F21,
            curses.KEY_F22: Screen.KEY_F22,
            curses.KEY_F23: Screen.KEY_F23,
            curses.KEY_F24: Screen.KEY_F24,
            curses.KEY_PRINT: Screen.KEY_PRINT_SCREEN,
            curses.KEY_IC: Screen.KEY_INSERT,
            curses.KEY_DC: Screen.KEY_DELETE,
            curses.KEY_HOME: Screen.KEY_HOME,
            curses.KEY_END: Screen.KEY_END,
            curses.KEY_LEFT: Screen.KEY_LEFT,
            curses.KEY_UP: Screen.KEY_UP,
            curses.KEY_RIGHT: Screen.KEY_RIGHT,
            curses.KEY_DOWN: Screen.KEY_DOWN,
            curses.KEY_PPAGE: Screen.KEY_PAGE_UP,
            curses.KEY_NPAGE: Screen.KEY_PAGE_DOWN,
            curses.KEY_BACKSPACE: Screen.KEY_BACK,
            9: Screen.KEY_TAB,
            curses.KEY_BTAB: Screen.KEY_BACK_TAB
            # Terminals translate keypad keys, so no need for a special
            # mapping here.

            # Terminals don't transmit meta keys (like control, shift, etc), so
            # there's no translation for them either.
        }

        def __init__(self, win, height=200, catch_interrupt=False,
                     unicode_aware=False):
            """
            :param win: The window object as returned by the curses wrapper
                method.
            :param height: The height of the screen buffer to be used.
            :param catch_interrupt: Whether to catch SIGINT or not.
            :param unicode_aware: Whether this Screen can use unicode or not.
            """
            # Determine unicode support if needed.
            if unicode_aware is None:
                try:
                    encoding = getlocale()[1]
                    if not encoding:
                        encoding = getdefaultlocale()[1]
                except ValueError:
                    encoding = os.environ.get("LC_CTYPE")
                unicode_aware = (encoding is not None and
                                 encoding.lower() == "utf-8")

            # Save off the screen details.
            super(_CursesScreen, self).__init__(
                win.getmaxyx()[0], win.getmaxyx()[1], height, unicode_aware)
            self._screen = win
            self._screen.keypad(1)

            # Set up basic colour schemes.
            self.colours = curses.COLORS

            # Disable the cursor.
            curses.curs_set(0)

            # Non-blocking key checks.
            self._screen.nodelay(1)

            # Store previous handlers for restoration at close
            self._signal_state = _SignalState()

            # Set up signal handler for screen resizing.
            self._re_sized = False
            self._signal_state.set(signal.SIGWINCH, self._resize_handler)

            # Catch SIGINTs and translated them to ctrl-c if needed.
            if catch_interrupt:
                # Ignore SIGINT (ctrl-c) and SIGTSTP (ctrl-z) signals.
                self._signal_state.set(signal.SIGINT, self._catch_interrupt)
                self._signal_state.set(signal.SIGTSTP, self._catch_interrupt)

            # Enable mouse events
            curses.mousemask(curses.ALL_MOUSE_EVENTS |
                             curses.REPORT_MOUSE_POSITION)

            # Lookup the necessary escape codes in the terminfo database.
            self._move_y_x = curses.tigetstr("cup")
            self._up_line = curses.tigetstr("ri").decode("utf-8")
            self._down_line = curses.tigetstr("ind").decode("utf-8")
            self._fg_color = curses.tigetstr("setaf")
            self._bg_color = curses.tigetstr("setab")
            self._clear_line = curses.tigetstr("el").decode("utf-8")
            if curses.tigetflag("hs"):
                self._start_title = curses.tigetstr("tsl").decode("utf-8")
                self._end_title = curses.tigetstr("fsl").decode("utf-8")
            else:
                self._start_title = self._end_title = None
            self._a_normal = curses.tigetstr("sgr0").decode("utf-8")
            self._a_bold = curses.tigetstr("bold").decode("utf-8")
            self._a_reverse = curses.tigetstr("rev").decode("utf-8")
            self._a_underline = curses.tigetstr("smul").decode("utf-8")
            self._clear_screen = curses.tigetstr("clear").decode("utf-8")

            # Look for a mismatch between the kernel terminal and the terminfo
            # database for backspace.  Fix up keyboard mappings if needed.
            kbs = curses.tigetstr("kbs").decode("utf-8")
            tbs = termios.tcgetattr(sys.stdin)[6][termios.VERASE]
            if tbs != kbs:
                self._KEY_MAP[ord(tbs)] = Screen.KEY_BACK

            # Conversion from Screen attributes to curses equivalents.
            self._ATTRIBUTES = {
                Screen.A_BOLD: self._a_bold,
                Screen.A_NORMAL: self._a_normal,
                Screen.A_REVERSE: self._a_reverse,
                Screen.A_UNDERLINE: self._a_underline
            }

            # Byte stream processing for unicode input.
            self._bytes_to_read = 0
            self._bytes_to_return = b""

            # We'll actually break out into low-level output, so flush any
            # high level buffers now.
            self._screen.refresh()

        def close(self, restore=True):
            """
            Close down this Screen and tidy up the environment as required.

            :param restore: whether to restore the environment or not.
            """
            self._signal_state.restore()
            if restore:
                self._screen.keypad(0)
                curses.echo()
                curses.nocbreak()
                curses.endwin()

        @staticmethod
        def _safe_write(msg):
            """
            Safe write to screen - catches IOErrors on screen resize.

            :param msg: The message to write to the screen.
            """
            try:
                sys.stdout.write(msg)
            except IOError:
                # Screen resize can throw IOErrors.  These can be safely
                # ignored as the screen will be shortly reset anyway.
                pass

        def _resize_handler(self, *_):
            """
            Window resize signal handler.  We don't care about any of the
            parameters passed in beyond the object reference.
            """
            curses.endwin()
            curses.initscr()
            self._re_sized = True

        def _scroll(self, lines):
            """
            Scroll the window up or down.

            :param lines: Number of lines to scroll.  Negative numbers scroll
                down.
            """
            if lines < 0:
                self._safe_write("{}{}".format(
                    curses.tparm(self._move_y_x, 0, 0).decode("utf-8"),
                    (self._up_line + self._clear_line) * -lines))
            else:
                self._safe_write("{}{}".format(curses.tparm(
                    self._move_y_x, self.height, 0).decode("utf-8"),
                    (self._down_line + self._clear_line) * lines))

        def _clear(self):
            """
            Clear the Screen of all content.
            """
            self._safe_write(self._clear_screen)
            sys.stdout.flush()

        def refresh(self):
            """
            Refresh the screen.
            """
            super(_CursesScreen, self).refresh()
            try:
                sys.stdout.flush()
            except IOError:
                pass

        @staticmethod
        def _catch_interrupt(signal_no, frame):
            """
            SIGINT handler.  We ignore the signal and frame info passed in.
            """
            # Stop pep-8 shouting at me for unused params I can't control.
            del frame

            # The OS already caught the ctrl-c, so inject it now for the next
            # input.
            if signal_no == signal.SIGINT:
                curses.ungetch(3)
            elif signal_no == signal.SIGTSTP:
                curses.ungetch(26)
            return

        def get_event(self):
            """
            Check for an event without waiting.
            """
            # Spin through notifications until we find something we want.
            key = 0
            while key != -1:
                # Get the next key
                key = self._screen.getch()

                if key == curses.KEY_RESIZE:
                    # Handle screen resize
                    self._re_sized = True
                elif key == curses.KEY_MOUSE:
                    # Handle a mouse event
                    _, x, y, _, bstate = curses.getmouse()
                    buttons = 0
                    # Some Linux modes only report clicks, so check for any
                    # button down or click events.
                    if (bstate & curses.BUTTON1_PRESSED != 0 or
                            bstate & curses.BUTTON1_CLICKED != 0):
                        buttons |= MouseEvent.LEFT_CLICK
                    if (bstate & curses.BUTTON3_PRESSED != 0 or
                            bstate & curses.BUTTON3_CLICKED != 0):
                        buttons |= MouseEvent.RIGHT_CLICK
                    if bstate & curses.BUTTON1_DOUBLE_CLICKED != 0:
                        buttons |= MouseEvent.DOUBLE_CLICK
                    return MouseEvent(x, y, buttons)
                elif key != -1:
                    # Handle any byte streams first
                    logger.debug("Processing key: %x", key)
                    if self._unicode_aware and key > 0:
                        if key & 0xC0 == 0xC0:
                            self._bytes_to_return = struct.pack(b"B", key)
                            self._bytes_to_read = bin(key)[2:].index("0") - 1
                            logger.debug("Byte stream: %d bytes left",
                                         self._bytes_to_read)
                            continue
                        elif self._bytes_to_read > 0:
                            self._bytes_to_return += struct.pack(b"B", key)
                            self._bytes_to_read -= 1
                            if self._bytes_to_read > 0:
                                continue
                            else:
                                key = ord(self._bytes_to_return.decode("utf-8"))

                    # Handle a genuine key press.
                    logger.debug("Returning key: %x", key)
                    if key in self._KEY_MAP:
                        return KeyboardEvent(self._KEY_MAP[key])
                    elif key != -1:
                        return KeyboardEvent(key)

            return None

        def has_resized(self):
            """
            Check whether the screen has been re-sized.
            """
            re_sized = self._re_sized
            self._re_sized = False
            return re_sized

        def _change_colours(self, colour, attr, bg):
            """
            Change current colour if required.

            :param colour: New colour to use.
            :param attr: New attributes to use.
            :param bg: New background colour to use.
            """
            # Change attribute first as this will reset colours when swapping
            # modes.
            if attr != self._attr:
                self._safe_write(self._a_normal)
                if attr != 0:
                    self._safe_write(self._ATTRIBUTES[attr])
                self._attr = attr
                self._colour = None
                self._bg = None

            # Now swap colours if required.
            if colour != self._colour:
                self._safe_write(curses.tparm(
                    self._fg_color, colour).decode("utf-8"))
                self._colour = colour
            if bg != self._bg:
                self._safe_write(curses.tparm(
                    self._bg_color, bg).decode("utf-8"))
                self._bg = bg

        def _print_at(self, text, x, y, width):
            """
            Print string at the required location.

            :param text: The text string to print.
            :param x: The x coordinate
            :param y: The Y coordinate
            :param width: The width of the character (for dual-width glyphs in CJK languages).
            """
            # Move the cursor if necessary
            cursor = u""
            if x != self._cur_x or y != self._cur_y:
                cursor = curses.tparm(self._move_y_x, y, x).decode("utf-8")

            # Print the text at the required location and update the current
            # position.
            try:
                self._safe_write(cursor + text)
            except UnicodeEncodeError:
                # This is probably a sign that the user has the wrong locale.
                # Try to soldier on anyway.
                self._safe_write(cursor + "?" * len(text))

            # Update cursor position for next time...
            self._cur_x = x + width
            self._cur_y = y

        def _wait_for_input(self, timeout):
            """
            Wait until there is some input or the timeout is hit.

            :param timeout: Time to wait for input in seconds (floating point).
            """
            try:
                select.select([sys.stdin], [], [], timeout)
            except select.error:
                # Any error will almost certainly result in a a Screen.  Ignore.
                pass

        def set_title(self, title):
            """
            Set the title for this terminal/console session.  This will
            typically change the text displayed in the window title bar.

            :param title: The title to be set.
            """
            if self._start_line is not None:
                self._safe_write("{}{}{}".format(self._start_title, title,
                                                 self._end_title))

    class _SignalState(object):
        """
        Save previous user signal state while setting signals.

        Used for signal restoration when asciimatics no longer has control
        of the user program.
        """

        def __init__(self):
            self._old_signal_states = []

        def set(self, signalnum, handler):
            """
            Set signal handler and record their previous values.

            :param signalnum: The const/enum matching to the signal to be set.
            :param handler: The function/const to set the signal to
            """
            old_handler = signal.getsignal(signalnum)
            self._old_signal_states.append((signalnum, old_handler))
            signal.signal(signalnum, handler)

        def restore(self):
            """
            Restore saved signals to their previous handles.
            """
            for signalnum, handler in self._old_signal_states:
                signal.signal(signalnum, handler)
            self._old_signal_states = []
