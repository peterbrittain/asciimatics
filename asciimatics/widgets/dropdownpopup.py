# -*- coding: utf-8 -*-
"""This module defines an internal class for drop down popups"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from asciimatics.widgets.divider import Divider
from asciimatics.widgets.layout import Layout
from asciimatics.widgets.listbox import ListBox
from asciimatics.widgets.temppopup import _TempPopup
from asciimatics.widgets.text import Text
from asciimatics.widgets.widget import Widget

class _DropdownPopup(_TempPopup):
    """
    An internal Frame for selecting an item from a drop-down list..
    """

    def __init__(self, parent):
        """
        :param parent: The widget that spawned this pop-up.
        """
        # Decide which way to present the list - up or down from the parent widget.
        location = parent.get_location()
        if parent.frame.screen.height - location[1] < 3:
            height = min(len(parent.options) + 4, location[1] + 2)
            start_line = location[1] - height + 2
            reverse = True
        else:
            start_line = location[1] - 1
            height = min(len(parent.options) + 4, parent.frame.screen.height - location[1] + 1)
            reverse = False

        # Construct the Frame
        super(_DropdownPopup, self).__init__(parent.frame.screen,
                                             parent,
                                             location[0], start_line,
                                             parent.width, height)

        # Build the widget to display the time selection.
        layout = Layout([1], fill_frame=True)
        self.add_layout(layout)
        self._field = Text()
        self._field.disabled = True
        divider = Divider()
        divider.disabled = True
        self._list = ListBox(Widget.FILL_FRAME,
                             parent.options,
                             add_scroll_bar=len(parent.options) > height - 4,
                             on_select=self.close, on_change=self._link)
        layout.add_widget(self._list if reverse else self._field, 0)
        layout.add_widget(divider, 0)
        layout.add_widget(self._field if reverse else self._list, 0)
        self.fix()

        # Set up the correct time.
        self._list.value = parent.value

    def _link(self):
        self._field.value = self._list.options[self._list._line][0]

    def _on_close(self, cancelled):
        if not cancelled:
            self._parent.value = self._list.value
