# -*- coding: utf-8 -*-
"""This module defines a dropdown list widget"""
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.screen import Screen
from asciimatics.widgets.dropdownpopup import _DropdownPopup
from asciimatics.widgets.utilities import _enforce_width
from asciimatics.widgets.widget import Widget

class DropdownList(Widget):
    """
    This widget allows you to pick an item from a temporary pop-up list.
    """

    __slots__ = ["_label", "_on_change", "_child", "_options", "_line", "_value"]

    def __init__(self, options, label=None, name=None, on_change=None, **kwargs):
        """
        :param options: The options for each row in the widget.
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        :param on_change: Optional function to call when the selected time changes.

        The `options` are a list of tuples, where the first value is the string to be displayed
        to the user and the second is an interval value to identify the entry to the program.
        For example:

            options=[("First option", 1), ("Second option", 2)]

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super(DropdownList, self).__init__(name, **kwargs)
        self._label = label
        self._on_change = on_change
        self._child = None
        self._options = options
        self._line = 0 if len(options) > 0 else None
        self._value = options[self._line][1] if self._line is not None else None

    @property
    def options(self):
        """
        The set of allowed options for the drop-down list.
        """
        return self._options

    @options.setter
    def options(self, new_value):
        self._options = new_value
        self.value = self._value

    def update(self, frame_no):
        self._draw_label()

        # This widget only ever needs display the current selection - the separate Frame does all
        # the clever stuff when it has the focus.
        text = "" if self._line is None else self._options[self._line][0]
        (colour, attr, background) = self._pick_colours("field", selected=self._has_focus)
        self._frame.canvas.print_at(
            "[{:{}}]".format(
                _enforce_width(text, self.width - 2, self._frame.canvas.unicode_aware),
                self.width - 2),
            self._x + self._offset,
            self._y,
            colour, attr, background)

    def reset(self):
        pass

    def process_event(self, event):
        if event is not None:
            if isinstance(event, KeyboardEvent):
                if event.key_code in [Screen.ctrl("M"), Screen.ctrl("J"), ord(" ")]:
                    event = None
            elif isinstance(event, MouseEvent):
                if event.buttons != 0:
                    if self.is_mouse_over(event, include_label=False):
                        event = None
            if event is None:
                self._child = _DropdownPopup(self)
                self.frame.scene.add_effect(self._child)

        return event

    def required_height(self, offset, width):
        return 1

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        # Only trigger change notification after we've changed selection
        old_value = self._value
        self._value = new_value
        for i, [_, value] in enumerate(self._options):
            if value == new_value:
                self._line = i
                break
        else:
            self._value = self._line = None
        if old_value != self._value and self._on_change:
            self._on_change()
