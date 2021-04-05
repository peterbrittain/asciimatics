# -*- coding: utf-8 -*-
"""This module defines a divider between widgets"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from asciimatics.widgets.widget import Widget

class Divider(Widget):
    """
    A divider to break up a group of widgets.
    """

    __slots__ = ["_draw_line", "_required_height", "_line_char"]

    def __init__(self, draw_line=True, height=1, line_char=None):
        """
        :param draw_line: Whether to draw a line in the centre of the gap.
        :param height: The required vertical gap.
        :param line_char: Optional character to use for drawing the line.
        """
        # Dividers have no value and so should have no name for look-ups either.
        super(Divider, self).__init__(None, tab_stop=False)
        self._draw_line = draw_line
        self._required_height = height
        self._line_char = line_char

    def register_frame(self, frame):
        # Update line drawing character if needed once we have a canvas to query.
        super(Divider, self).register_frame(frame)
        if self._line_char is None:
            self._line_char = u"─" if self._frame.canvas.unicode_aware else "-"

    def process_event(self, event):
        # Dividers have no user interactions
        return event

    def update(self, frame_no):
        (colour, attr, background) = self._frame.palette["borders"]
        if self._draw_line:
            self._frame.canvas.print_at(self._line_char * self._w,
                                        self._x,
                                        self._y + (self._h // 2),
                                        colour, attr, background)

    def reset(self):
        pass

    def required_height(self, offset, width):
        return self._required_height

    @property
    def value(self):
        """
        The current value for this Divider.
        """
        return self._value
