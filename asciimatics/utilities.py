
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


class BorderLines:
    """Represents the characters used to draw a border. Supports following
    types:

    * ``ASCII_LINE`` -- ASCII safe characters (0)
    * ``SINGLE_LINE`` -- Unicode based single lined box (1)
    * ``DOUBLE_LINE`` -- Unicode based double lined box (2)

    Objects that support borders will have an instance of this class. The
    border style can be changed through a call to
    :func:`set_type`.

    Individual parts of the border can be accessed directly through the
    attributes:

    * ``top_left`` -- top left corner
    * ``top_right`` -- top right corner
    * ``bottom_left`` -- bottom left corner
    * ``bottom_right`` -- bottom right corner
    * ``horizontal`` -- horizontal line for top and bottom borders
    * ``vertical`` --  vertical line for left and right side borders
    """

    ASCII_LINE = 0
    SINGLE_LINE = 1
    DOUBLE_LINE = 2

    def __init__(self, unicode_aware, border_type=SINGLE_LINE):
        """**Initialization:**

        :param unicode_aware: boolean indicating if the terminal is Unicode
            aware. If False, will force the use of ASCII symbols in the border
        :param border_type: property indicating the type of border. Supports
            ``ASCII_LINE``, ``SINGLE_LINE``, and ``DOUBLE_LINE``. Defaults to 
            ``SINGLE_LINE``.
        """
        self.unicode_aware = unicode_aware
        self.set_type(border_type)

    def set_type(self, border_type):
        """Change the type of border line being drawn

        :param border_type: One of ``ASCII_LINE``, ``SINGLE_LINE``, or 
            ``DOUBLE_LINE``
        """
        if border_type == self.SINGLE_LINE and self.unicode_aware:
            self.top_left = u"┌"
            self.top_right = u"┐"
            self.bottom_left = u"└"
            self.bottom_right = u"┘"
            self.horizontal = u"─"
            self.vertical = u"│"
        elif border_type == self.DOUBLE_LINE and self.unicode_aware:
            self.top_left = u"╔"
            self.top_right = u"╗"
            self.bottom_left = u"╚"
            self.bottom_right = u"╝"
            self.horizontal = u"═"
            self.vertical = u"║"
        else:
            self.top_left = "+"
            self.top_right = "+"
            self.bottom_left = "+"
            self.bottom_right = "+"
            self.horizontal = "-"
            self.vertical = "|"

    def top_line(self, length):
        """Returns a string containing the top border to be drawn. 

        :param length: length of border, including corners
        :returns: String to draw border comprised of top left corner,
            horizontal bar, and top right corner.
        """
        return self.top_left + (length - 2) * self.horizontal + self.top_right

    def bottom_line(self, length):
        """Returns a string containing the bottom border to be drawn. 

        :param length: length of border, including corners
        :returns: String to draw border comprised of bottom left corner,
            horizontal bar, and bottom right corner.
        """
        return self.bottom_left + (length - 2) * self.horizontal + self.bottom_right
