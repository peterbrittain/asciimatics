# -*- coding: utf-8 -*-
"""
This module implements a plasma effect renderer.
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from builtins import range
from math import sin, pi, sqrt

from asciimatics.renderers.base import DynamicRenderer
from asciimatics.screen import Screen


class Plasma(DynamicRenderer):
    """
    Renderer to create a "plasma" effect using sinusoidal functions.

    The implementation here uses the same techniques described in
    http://lodev.org/cgtutor/plasma.html
    """

    # The ASCII grey scale from darkest to lightest.
    _greyscale = ' .:;rsA23hHG#9&@'

    # Colours for different environments
    _palette_8 = [
        (Screen.COLOUR_BLUE, Screen.A_NORMAL),
        (Screen.COLOUR_BLUE, Screen.A_NORMAL),
        (Screen.COLOUR_MAGENTA, Screen.A_NORMAL),
        (Screen.COLOUR_MAGENTA, Screen.A_NORMAL),
        (Screen.COLOUR_RED, Screen.A_NORMAL),
        (Screen.COLOUR_RED, Screen.A_BOLD),
    ]
    _palette_256 = [
        (18, 0),
        (19, 0),
        (20, 0),
        (21, 0),
        (57, 0),
        (93, 0),
        (129, 0),
        (201, 0),
        (200, 0),
        (199, 0),
        (198, 0),
        (197, 0),
        (196, 0),
        (196, 0),
        (196, 0),
    ]

    def __init__(self, height, width, colours):
        """
        :param height: Height of the box to contain the plasma.
        :param width: Width of the box to contain the plasma.
        :param colours: Number of colours the screen supports.
        """
        super(Plasma, self).__init__(height, width)
        self._palette = self._palette_256 if colours >= 256 else self._palette_8
        self._t = 0

    def _render_now(self):
        # Internal function for creating a sine wave radiating out from a point
        def f(x1, y1, xp, yp, n):
            return sin(sqrt((x1 - self._canvas.width * xp) ** 2 +
                            4 * ((y1 - self._canvas.height * yp) ** 2)) * pi / n)

        self._t += 1
        for y in range(self._canvas.height - 1):
            for x in range(self._canvas.width - 1):
                value = abs(f(x + self._t / 3, y, 1 / 4, 1 / 3, 15) +
                            f(x, y, 1 / 8, 1 / 5, 11) +
                            f(x, y + self._t / 3, 1 / 2, 1 / 5, 13) +
                            f(x, y, 3 / 4, 4 / 5, 13)) / 4.0
                fg, attr = self._palette[
                    int(round(value * (len(self._palette) - 1)))]
                char = self._greyscale[int((len(self._greyscale) - 1) * value)]
                self._write(char, x, y, fg, attr, 0)

        return self._plain_image, self._colour_map
