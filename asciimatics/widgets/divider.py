"""This module defines a divider between widgets"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from asciimatics.widgets.widget import Widget
if TYPE_CHECKING:
    from asciimatics.event import Event
    from asciimatics.widgets.frame import Frame


class Divider(Widget):
    """
    A divider to break up a group of widgets.
    """

    __slots__ = ["_draw_line", "_required_height", "_line_char"]

    def __init__(self, draw_line: bool = True, height: int = 1, line_char: Optional[str] = None):
        """
        :param draw_line: Whether to draw a line in the centre of the gap.
        :param height: The required vertical gap.
        :param line_char: Optional character to use for drawing the line.
        """
        # Dividers have no value and so should have no name for look-ups either.
        super().__init__(None, tab_stop=False)
        self._draw_line = draw_line
        self._required_height = height
        self._line_char = line_char

    def register_frame(self, frame: Frame):
        # Update line drawing character if needed once we have a canvas to query.
        super().register_frame(frame)
        assert self._frame
        if self._line_char is None:
            self._line_char = "─" if self._frame.canvas.unicode_aware else "-"

    def process_event(self, event: Optional[Event]) -> Optional[Event]:
        # Dividers have no user interactions
        return event

    def update(self, frame_no: int):
        assert self._frame
        (colour, attr, background) = self._frame.palette["borders"]
        if self._draw_line:
            assert self._line_char
            self._frame.canvas.print_at(self._line_char * self._w,
                                        self._x,
                                        self._y + (self._h // 2),
                                        colour,
                                        attr,
                                        background)

    def reset(self):
        pass

    def required_height(self, offset: int, width: int) -> int:
        return self._required_height

    @property
    def value(self):
        """
        The current value for this Divider.
        """
        return None

    @value.setter
    def value(self, new_value):
        self._value = new_value
