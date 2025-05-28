"""This module implements a vertical division between widgets"""
from __future__ import annotations
from typing import Optional
from asciimatics.widgets.widget import Widget
from asciimatics.event import Event


class VerticalDivider(Widget):
    """
    A vertical divider for separating columns.

    This widget should be put into a column of its own in the Layout.
    """

    __slots__ = ["_required_height"]

    def __init__(self, height: int = Widget.FILL_COLUMN):
        """
        :param height: The required height for this divider.
        """
        super().__init__(None, tab_stop=False)
        self._required_height = height

    def process_event(self, event: Optional[Event]) -> Optional[Event]:
        return event

    def update(self, frame_no: int):
        assert self._frame
        (color, attr, background) = self._frame.palette["borders"]
        vert = "│" if self._frame.canvas.unicode_aware else "|"
        for i in range(self._h):
            self._frame.canvas.print_at(vert, self._x, self._y + i, color, attr, background)

    def reset(self):
        pass

    def required_height(self, offset: int, width: int) -> int:
        return self._required_height

    @property
    def value(self) -> None:
        """
        The current value for this VerticalDivider.
        """
        return None

    @value.setter
    def value(self, new_value):
        self._value = new_value
