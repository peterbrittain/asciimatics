"""This module implements a vertical division between widgets"""
from asciimatics.widgets.widget import Widget

class VerticalDivider(Widget):
    """
    A vertical divider for separating columns.

    This widget should be put into a column of its own in the Layout.
    """

    __slots__ = ["_required_height"]

    def __init__(self, height=Widget.FILL_COLUMN):
        """
        :param height: The required height for this divider.
        """
        super(VerticalDivider, self).__init__(None, tab_stop=False)
        self._required_height = height

    def process_event(self, event):
        return event

    def update(self, frame_no):
        (color, attr, background) = self._frame.palette["borders"]
        vert = u"│" if self._frame.canvas.unicode_aware else "|"
        for i in range(self._h):
            self._frame.canvas.print_at(vert, self._x, self._y + i, color, attr, background)

    def reset(self):
        pass

    def required_height(self, offset, width):
        return self._required_height

    @property
    def value(self):
        return self._value
