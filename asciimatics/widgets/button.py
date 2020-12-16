# -*- coding: utf-8 -*-
"""This module defines a button widget"""
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.widgets.widget import Widget

class Button(Widget):
    """
    A Button widget to be  displayed in a Frame.

    It is typically used to represent a desired action for te user to invoke (e.g. a submit button
    on a form).
    """

    __slots__ = ["_text", "_add_box", "_on_click", "_label"]

    def __init__(self, text, on_click, label=None, add_box=True, **kwargs):
        """
        :param text: The text for the button.
        :param on_click: The function to invoke when the button is clicked.
        :param label: An optional label for the widget.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super(Button, self).__init__(None, **kwargs)
        # We nly ever draw the button with borders, so calculate that once now.
        self._text = "< {} >".format(text) if add_box else text
        self._add_box = add_box
        self._on_click = on_click
        self._label = label

    def set_layout(self, x, y, offset, w, h):
        # Do the usual layout work. then recalculate exact x/w values for the
        # rendered button.
        super(Button, self).set_layout(x, y, offset, w, h)
        text_width = self.string_len(self._text)
        if self._add_box:
            # Minimize widget to make a nice little button.
            self._x += max(0, (self.width - text_width) // 2)
            self._w = min(self._w, text_width)
        else:
            # Maximize text to make for a consistent colouring when used in menus.
            self._text += " " * (self._w - text_width)

    def update(self, frame_no):
        self._draw_label()

        (colour, attr, bg) = self._pick_colours("button")
        self._frame.canvas.print_at(
            self._text,
            self._x + self._offset,
            self._y,
            colour, attr, bg)

    def reset(self):
        self._value = False

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord(" "), 10, 13]:
                self._on_click()
                return None
            # Ignore any other key press.
            return event
        if isinstance(event, MouseEvent):
            if event.buttons != 0:
                if (self._x <= event.x < self._x + self._w and
                        self._y <= event.y < self._y + self._h):
                    self._on_click()
                    return None
        # Ignore other events
        return event

    def required_height(self, offset, width):
        return 1

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
