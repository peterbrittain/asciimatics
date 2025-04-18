"""This module implements a time picker widget"""
from datetime import datetime

from asciimatics.widgets.basepicker import _BasePicker
from asciimatics.widgets.label import Label
from asciimatics.widgets.layout import Layout
from asciimatics.widgets.listbox import ListBox
from asciimatics.widgets.temppopup import _TempPopup


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


class TimePicker(_BasePicker):
    """
    A TimePicker widget allows you to pick a time from a compact, temporary, pop-up Frame.
    """

    __slots__ = ["include_seconds"]

    def __init__(self, label=None, name=None, seconds=False, on_change=None, **kwargs):
        """
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        :param seconds: Whether to include selection of seconds or not.
        :param on_change: Optional function to call when the selected time changes.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super().__init__(_TimePickerPopup, label=label, name=name, on_change=on_change, **kwargs)
        self._value = datetime.now().time()
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
