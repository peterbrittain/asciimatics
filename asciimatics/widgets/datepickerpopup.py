"""This module defines an internal base class for datepickers"""
from datetime import date
from asciimatics.exceptions import InvalidFields
from asciimatics.widgets.label import Label
from asciimatics.widgets.layout import Layout
from asciimatics.widgets.listbox import ListBox
from asciimatics.widgets.temppopup import _TempPopup

class _DatePickerPopup(_TempPopup):
    """
    An internal Frame for editing the currently selected date.
    """

    def __init__(self, parent, year_range=None):
        """
        :param parent: The widget that spawned this pop-up.
        :param year_range: Optional range to limit the year selection to.
        """
        # Create the lists for each entry.
        now = parent.value if parent.value else date.today()
        if year_range is None:
            year_range = range(now.year - 50, now.year + 50)
        self._days = ListBox(3,
                             [("{:02}".format(x), x) for x in range(1, 32)],
                             centre=True,
                             validator=self._check_date)
        self._months = ListBox(3,
                               [(now.replace(day=1, month=x).strftime("%b"), x)
                                for x in range(1, 13)],
                               centre=True,
                               on_change=self._refresh_day)
        self._years = ListBox(3,
                              [("{:04}".format(x), x) for x in year_range],
                              centre=True,
                              on_change=self._refresh_day)

        # Construct the Frame
        location = parent.get_location()
        super(_DatePickerPopup, self).__init__(parent.frame.screen,
                                               parent,
                                               location[0] - 1, location[1] - 2,
                                               13, 5)

        # Build the widget to display the time selection.
        layout = Layout([2, 1, 3, 1, 4], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._days, 0)
        layout.add_widget(Label("\n/", height=3), 1)
        layout.add_widget(self._months, 2)
        layout.add_widget(Label("\n/", height=3), 3)
        layout.add_widget(self._years, 4)
        self.fix()

        # Set up the correct time.
        self._years.value = parent.value.year
        self._months.value = parent.value.month
        self._days.value = parent.value.day

    def _check_date(self, value):
        try:
            date(self._years.value, self._months.value, value)
            return True
        except (TypeError, ValueError):
            return False

    def _refresh_day(self):
        self._days.value = self._days.value

    def _on_close(self, cancelled):
        try:
            if not cancelled:
                self._parent.value = self._parent.value.replace(day=self._days.value,
                                                                month=self._months.value,
                                                                year=self._years.value)
        except ValueError:
            raise InvalidFields([self._days])
