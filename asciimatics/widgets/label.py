# -*- coding: utf-8 -*-
"""This mdoule implements a widget to give a text label"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from asciimatics.widgets.widget import Widget
from asciimatics.widgets.utilities import _split_text

class Label(Widget):
    """
    A text label.
    """

    __slots__ = ["_text", "_required_height", "_align"]

    def __init__(self, label, height=1, align="<"):
        """
        :param label: The text to be displayed for the Label.
        :param height: Optional height for the label.  Defaults to 1 line.
        :param align: Optional alignment for the Label.  Defaults to left aligned.
            Options are "<" = left, ">" = right and "^" = centre

        """
        # Labels have no value and so should have no name for look-ups either.
        super(Label, self).__init__(None, tab_stop=False)

        # Although this is a label, we don't want it to contribute to the layout
        # tab calculations, so leave internal `_label` value as None.
        # Also ensure that the label really is text.
        self._text = str(label)
        self._required_height = height
        self._align = align

    def process_event(self, event):
        # Labels have no user interactions
        return event

    def update(self, frame_no):
        (colour, attr, background) = self._frame.palette[
            self._pick_palette_key("label", selected=False, allow_input_state=False)]
        for i, text in enumerate(
                _split_text(self._text, self._w, self._h, self._frame.canvas.unicode_aware)):
            self._frame.canvas.paint(
                "{:{}{}}".format(text, self._align, self._w),
                self._x, self._y + i, colour, attr, background
            )

    def reset(self):
        pass

    def required_height(self, offset, width):
        # Allow one line for text and a blank spacer before it.
        return self._required_height

    @property
    def text(self):
        """
        The current text for this Label.
        """
        return self._text

    @text.setter
    def text(self, new_value):
        self._text = new_value

    @property
    def value(self):
        return self._value
