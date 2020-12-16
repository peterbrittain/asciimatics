"""This module implements a time picker widget"""
from datetime import datetime
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.screen import Screen
from asciimatics.widgets.timepickerpopup import _TimePickerPopup
from asciimatics.widgets.widget import Widget

class TimePicker(Widget):
    """
    A TimePicker widget allows you to pick a time from a compact, temporary, pop-up Frame.
    """

    __slots__ = ["_label", "_on_change", "_value", "_child", "include_seconds"]

    def __init__(self, label=None, name=None, seconds=False, on_change=None, **kwargs):
        """
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        :param seconds: Whether to include selection of seconds or not.
        :param on_change: Optional function to call when the selected time changes.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super(TimePicker, self).__init__(name, **kwargs)
        self._label = label
        self._on_change = on_change
        self._value = datetime.now().time()
        self._child = None
        self.include_seconds = seconds

    def update(self, frame_no):
        self._draw_label()

        # This widget only ever needs display the current selection - the separate Frame does all
        # the clever stuff when it has the focus.
        (colour, attr, background) = self._pick_colours("edit_text")
        self._frame.canvas.print_at(
            self._value.strftime("%H:%M:%S" if self.include_seconds else "%H:%M"),
            self._x + self._offset,
            self._y,
            colour, attr, background)

    def reset(self):
        pass

    def process_event(self, event):
        if event is not None:
            # Handle key or mouse selection events - e.g. click on widget or Enter.
            if isinstance(event, KeyboardEvent):
                if event.key_code in [Screen.ctrl("M"), Screen.ctrl("J"), ord(" ")]:
                    event = None
            elif isinstance(event, MouseEvent):
                if event.buttons != 0:
                    if self.is_mouse_over(event, include_label=False):
                        event = None

            # Create the pop-up if needed
            if event is None:
                self._child = _TimePickerPopup(self)
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
