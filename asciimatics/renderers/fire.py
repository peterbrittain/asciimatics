"""
This module implements a fire effect renderer.
"""

import copy
from random import randint, random

from asciimatics.renderers.base import DynamicRenderer
from asciimatics.screen import Screen


class Fire(DynamicRenderer):
    """
    Renderer to create a fire effect based on a specified `emitter` that
    defines the heat source.

    The implementation here uses the same techniques described in
    http://freespace.virgin.net/hugo.elias/models/m_fire.htm, although a
    slightly different implementation.
    """

    _COLOURS_16 = [
        (Screen.COLOUR_RED, 0),
        (Screen.COLOUR_RED, 0),
        (Screen.COLOUR_RED, 0),
        (Screen.COLOUR_RED, 0),
        (Screen.COLOUR_RED, 0),
        (Screen.COLOUR_RED, 0),
        (Screen.COLOUR_RED, 0),
        (Screen.COLOUR_RED, Screen.A_BOLD),
        (Screen.COLOUR_RED, Screen.A_BOLD),
        (Screen.COLOUR_RED, Screen.A_BOLD),
        (Screen.COLOUR_RED, Screen.A_BOLD),
        (Screen.COLOUR_YELLOW, Screen.A_BOLD),
        (Screen.COLOUR_YELLOW, Screen.A_BOLD),
        (Screen.COLOUR_YELLOW, Screen.A_BOLD),
        (Screen.COLOUR_YELLOW, Screen.A_BOLD),
        (Screen.COLOUR_WHITE, Screen.A_BOLD),
    ]

    _COLOURS_256 = [
        (0, 0),
        (52, 0),
        (88, 0),
        (124, 0),
        (160, 0),
        (196, 0),
        (202, 0),
        (208, 0),
        (214, 0),
        (220, 0),
        (226, 0),
        (227, 0),
        (228, 0),
        (229, 0),
        (230, 0),
        (231, 0),
    ]

    _CHARS = " ...::$$$&&&@@"

    def __init__(self, height, width, emitter, intensity, spot, colours,
                 bg=False):
        """
        :param height: Height of the box to contain the flames.
        :param width: Width of the box to contain the flames.
        :param emitter: Heat source for the flames.  Any non-whitespace
            character is treated as part of the heat source.
        :param intensity: The strength of the flames.  The bigger the number,
            the hotter the fire.  0 <= intensity <= 1.0.
        :param spot: Heat of each spot source.  Must be an integer > 0.
        :param colours: Number of colours the screen supports.
        :param bg: (Optional) Whether to render background colours only.
        """
        super().__init__(height, width)
        self._emitter = emitter
        self._intensity = intensity
        self._spot_heat = spot
        self._count = len([c for c in emitter if c not in " \n"])
        line = [0 for _ in range(self._canvas.width)]
        self._buffer = [copy.deepcopy(line) for _ in range(self._canvas.width * 2)]
        self._colours = self._COLOURS_256 if colours >= 256 else \
            self._COLOURS_16
        self._bg_too = bg

        # Figure out offset of emitter to centre at the bottom of the buffer
        e_width = 0
        e_height = 0
        for line in self._emitter.split("\n"):
            e_width = max(e_width, len(line))
            e_height += 1
        self._x = (width - e_width) // 2
        self._y = height - e_height

    def _render_all(self):
        return [self._render_now()]

    def _render_now(self):
        # First make the fire rise with convection
        for y in range(len(self._buffer) - 1):
            self._buffer[y] = self._buffer[y + 1]
        self._buffer[len(self._buffer) - 1] = [0 for _ in range(self._canvas.width)]

        # Seed new hot spots
        x = self._x
        y = self._y
        for c in self._emitter:
            if c not in " \n" and random() < self._intensity:
                self._buffer[y][x] += randint(1, self._spot_heat)
            if c == "\n":
                x = self._x
                y += 1
            else:
                x += 1

        # Seed a few cooler spots
        for _ in range(self._canvas.width // 2):
            self._buffer[randint(0, self._canvas.height - 1)][
                randint(0, self._canvas.width - 1)] -= 10

        # Simulate cooling effect of the resulting environment.
        for y, row in enumerate(self._buffer):
            for x in range(self._canvas.width):
                new_val = row[x]
                if y < len(self._buffer) - 1:
                    new_val += self._buffer[y + 1][x]
                    if x > 0:
                        new_val += self._buffer[y][x - 1]
                    if x < self._canvas.width - 1:
                        new_val += self._buffer[y][x + 1]
                self._buffer[y][x] = new_val // 4

        # Now build the rendered text from the simulated flames.
        self._clear()
        for x in range(self._canvas.width):
            for y, row in enumerate(self._buffer):
                if row[x] > 0:
                    colour = self._colours[min(len(self._colours) - 1, row[x])]
                    if self._bg_too:
                        char = " "
                        bg = colour[0]
                    else:
                        char = self._CHARS[min(len(self._CHARS) - 1, row[x])]
                        bg = 0
                    self._write(char, x, y, colour[0], colour[1], bg)

        return self._plain_image, self._colour_map
