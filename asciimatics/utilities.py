
"""
This module is just a collection of simple helper functions.
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
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


class BoxTool:
    """Tool for building boxes out of characters. Supports a variety of line
    styles:

    * ``ASCII_LINE`` -- ASCII safe characters (0)
    * ``SINGLE_LINE`` -- Unicode based single lined box (1)
    * ``DOUBLE_LINE`` -- Unicode based double lined box (2)
    * ``MIXED_LINE`` -- Unicode based double line box for outside, single line inside (3)

    Individual characters of a box can be accessed directly through attributes:

    * ``up_left`` -- corner piece facing up and left
    * ``up_right`` -- corner piece facing up and right
    * ``down_left`` -- corner piece facing down and left
    * ``down_right`` -- corner piece facing down and right
    * ``h`` -- horizontal line 
    * ``h_inside`` -- horizontal line used inside the grid
    * ``v`` --  vertical line 
    * ``v_inside`` --  vertical line used inside the grid
    * ``v_left`` -- vertical line with mid joiner facing to the left
    * ``v_right`` -- vertical line with mid joiner facing to the right
    * ``h_up`` -- horizontal line with a mid joiner facing up
    * ``h_down`` -- horizontal line with a mid joiner facing down
    * ``cross`` -- intersection between vertical and horizontal
    """
    ASCII_LINE = 0
    SINGLE_LINE = 1
    DOUBLE_LINE = 2
    MIXED_LINE = 3

    #: Border specifiers for grid method
    NO_BORDERS = 0
    TOP_BORDER = 1
    LEFT_BORDER = 2
    RIGHT_BORDER = 4
    BOTTOM_BORDER = 8
    ALL_BORDERS = TOP_BORDER | LEFT_BORDER | RIGHT_BORDER | BOTTOM_BORDER

    def __init__(self, unicode_aware, style=SINGLE_LINE):
        """**Initialization:**

        :param unicode_aware: boolean indicating if the terminal is Unicode
            aware. If False, will force the use of the ASCII style
        :param style: line style specifier. Supports ``ASCII_LINE``,
            ``SINGLE_LINE``, and ``DOUBLE_LINE``. Defaults to ``SINGLE_LINE``.
        """
        self.unicode_aware = unicode_aware
        self.set_style(style)

    def set_style(self, style):
        """Change the line style used to draw boxes

        :param style: One of ``ASCII_LINE``, ``SINGLE_LINE``, or ``DOUBLE_LINE``
        """
        if style == self.SINGLE_LINE and self.unicode_aware:
            self.down_right = u"┌"
            self.down_left = u"┐"
            self.up_right = u"└"
            self.up_left = u"┘"
            self.h = u"─"
            self.h_inside = u"─"
            self.v = u"│"
            self.v_inside = u"│"
            self.v_left = u"┤"
            self.v_right = u"├"
            self.h_up = u"┴"
            self.h_down = u"┬"
            self.cross = u"┼"
        elif style == self.DOUBLE_LINE and self.unicode_aware:
            self.down_right = u"╔"
            self.down_left = u"╗"
            self.up_right = u"╚"
            self.up_left = u"╝"
            self.h = u"═"
            self.h_inside = u"═"
            self.v = u"║"
            self.v_inside = u"║"
            self.v_left = u"╣"
            self.v_right = u"╠"
            self.h_up = u"╩"
            self.h_down = u"╦"
            self.cross = u"╬"
        elif style == self.MIXED_LINE and self.unicode_aware:
            self.down_right = u"╔"
            self.down_left = u"╗"
            self.up_right = u"╚"
            self.up_left = u"╝"
            self.h = u"═"
            self.h_inside = u"─"
            self.v = u"║"
            self.v_inside = u"│"
            self.v_left = u"╢"
            self.v_right = u"╟"
            self.h_up = u"╧"
            self.h_down = u"╤"
            self.cross = u"┼"
        else:
            self.down_left = "+"
            self.down_right = "+"
            self.up_right = u"+"
            self.up_left = u"+"
            self.h = "-"
            self.h_inside = "-"
            self.v = "|"
            self.v_inside = ":"
            self.v_left = "+"
            self.v_right = "+"
            self.h_up = u"+"
            self.h_down = "+"
            self.cross = "+"

    # --- Empty box methods
    def box_top(self, width):
        """Returns a string containing the top border of a box

        :param width: width of box, including corners
        """
        return self.down_right + (width - 2) * self.h + self.down_left

    def box_bottom(self, width):
        """Returns a string containing the bottom border of a box

        :param width: width of box, including corners
        """
        return self.up_right + (width - 2) * self.h + self.up_left

    def box_line(self, width):
        """Returns a string with a vertical bar on each end, padded with
        spaces in between for the given width.

        :param width: width of box including sides
        """
        return self.v + (width - 2) * ' ' + self.v

    def box(self, height, width):
        """Returns a list of strings that together draw a box

        :param height: height of box
        :param width: width of box
        """
        lines = [self.box_top(width)]

        for _ in range(height - 1):
            lines.append(self.box_line(width))

        lines.append(self.box_bottom(width))
        return lines

    # --- Grid methods
    def _fill_line(self, width, borders, first, last, fill, joint_char, joints):
            parts = [fill for _ in range(width)]
            for j in range(width):
                if joints[j]:
                    parts[j] = joint_char

            if borders & self.LEFT_BORDER:
                parts[0] = first

            if borders & self.RIGHT_BORDER:
                parts[-1] = last

            return ''.join(parts)

    def grid(self, width, height, v_interval, h_interval, borders=ALL_BORDERS):
        """Returns a list of grid lines that build out a grid box

        :param width: width of the box
        :param height: height of the box
        :param v_interval: how frequent the vertical grid marks are, 1 for every
            column, 2 for every other, etc.
        :param h_interval: how frequent the horizontal grid marks are, 1 for 
            every row, 2 for every other, etc.
        :param borders: bit-wise or describing which borders the grid has,
            defaults to all of them
        :returns: list of grid lines
        """
        lines = []

        if h_interval == 0:
            h_lines = [False for _ in range(height)]
        else:
            h_lines = [(i + 1) % h_interval == 0 for i in range(height)]

        if borders & self.TOP_BORDER:
            h_lines.insert(0, True)
            h_lines.pop()

        if v_interval == 0:
            v_lines = [False for _ in range(width)]
        else:
            v_lines = [(j + 1) % v_interval == 0 for j in range(width)]

        if borders & self.LEFT_BORDER:
            v_lines.insert(0, True)
            v_lines.pop()

        # Create all lines
        for i in range(height):
            fill = ' '
            cross = self.v_inside
            if h_lines[i]:
                fill = self.h_inside
                cross = self.cross

            first = self.v if v_lines[0] else ' '
            if borders & self.LEFT_BORDER and h_lines[i]:
                first = self.v_right

            last = self.v if v_lines[-1] else ' '
            if borders & self.RIGHT_BORDER:
                if h_lines[i]:
                    last = self.v_left
                else:
                    last = self.v

            line = self._fill_line(width, borders, first, last, fill, 
                cross, v_lines)
            lines.append(line)

        if borders & self.TOP_BORDER:
            line = self._fill_line(width, borders, self.down_right, 
                self.down_left, self.h, self.h_down, v_lines)
            lines[0] = line

        # Create bottom border
        if borders & self.BOTTOM_BORDER:
            line = self._fill_line(width, borders, self.up_right, self.up_left, 
                self.h, self.h_up, v_lines)
            lines[-1] = line

        return lines
