"""This module implements a time picker widget"""
from datetime import datetime

from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.screen import Screen
from asciimatics.widgets.label import Label
from asciimatics.widgets.layout import Layout
from asciimatics.widgets.listbox import ListBox
from asciimatics.widgets.temppopup import _TempPopup
from asciimatics.widgets.widget import Widget


class _TimePickerPopup(_TempPopup):
    """
    An internal Frame for editing the currently selected time.
    """

    def __init__(self, parent):
        """
        :param parent: The widget that spawned this pop-up.
        """
        # Construct the Frame
        location = parent.get_location()
        super().__init__(parent.frame.screen,
                                               parent,
                                               location[0] - 1, location[1] - 2,
                                               10 if parent.include_seconds else 7, 5)

        # Build the widget to display the time selection.
        self._hours = ListBox(3, [(f"{x:02}", x) for x in range(24)], centre=True)
        self._minutes = ListBox(3, [(f"{x:02}", x) for x in range(60)], centre=True)
        self._seconds = ListBox(3, [(f"{x:02}", x) for x in range(60)], centre=True)
        if self._parent.include_seconds:
            layout = Layout([2, 1, 2, 1, 2], fill_frame=True)
        else:
            layout = Layout([2, 1, 2], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._hours, 0)
        layout.add_widget(Label("\n:", height=3), 1)
        layout.add_widget(self._minutes, 2)
        if self._parent.include_seconds:
            layout.add_widget(Label("\n:", height=3), 3)
            layout.add_widget(self._seconds, 4)
        self.fix()

        # Set up the correct time.
        self._hours.value = parent.value.hour
        self._minutes.value = parent.value.minute
        self._seconds.value = parent.value.second

    def _on_close(self, cancelled):
        if not cancelled:
            self._parent.value = self._parent.value.replace(hour=self._hours.value,
                                                            minute=self._minutes.value,
                                                            second=self._seconds.value)


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
        super().__init__(name, **kwargs)
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
        """
        The current selected time.
        """
        return self._value

    @value.setter
    def value(self, new_value):
        # Only trigger the notification after we've changed the value.
        old_value = self._value
        self._value = new_value
        if old_value != self._value and self._on_change:
            self._on_change()
