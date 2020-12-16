"""This module implements a base class for time picking"""
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
        super(_TimePickerPopup, self).__init__(parent.frame.screen,
                                               parent,
                                               location[0] - 1, location[1] - 2,
                                               10 if parent.include_seconds else 7, 5)

        # Build the widget to display the time selection.
        self._hours = ListBox(3, [("{:02}".format(x), x) for x in range(24)], centre=True)
        self._minutes = ListBox(3, [("{:02}".format(x), x) for x in range(60)], centre=True)
        self._seconds = ListBox(3, [("{:02}".format(x), x) for x in range(60)], centre=True)
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
