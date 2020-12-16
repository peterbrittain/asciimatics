"""This module defines a datepicker widget"""
from datetime import datetime
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.screen import Screen
from asciimatics.widgets.datepickerpopup import _DatePickerPopup
from asciimatics.widgets.widget import Widget

class DatePicker(Widget):
    """
    A DatePicker widget allows you to pick a date from a compact, temporary, pop-up Frame.
    """

    __slots__ = ["_label", "_on_change", "_value", "_child", "_year_range"]

    def __init__(self, label=None, name=None, year_range=None, on_change=None, **kwargs):
        """
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        :param on_change: Optional function to call when the selected time changes.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super(DatePicker, self).__init__(name, **kwargs)
        self._label = label
        self._on_change = on_change
        self._value = datetime.now().date()
        self._child = None
        self._year_range = year_range

    def update(self, frame_no):
        self._draw_label()

        # This widget only ever needs display the current selection - the separate Frame does all
        # the clever stuff when it has the focus.
        (colour, attr, background) = self._pick_colours("edit_text")
        self._frame.canvas.print_at(
            self._value.strftime("%d/%b/%Y"),
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
                self._child = _DatePickerPopup(self, year_range=self._year_range)
                self.frame.scene.add_effect(self._child)

        return event

    def required_height(self, offset, width):
        return 1

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        # Only trigger the notification after we've changed the value.
        old_value = self._value
        self._value = new_value
        if old_value != self._value and self._on_change:
            self._on_change()
