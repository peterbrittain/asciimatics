"""This module implements a scroll bar capability for widgets"""

class _ScrollBar():
    """
    Internal object to provide vertical scroll bars for widgets.
    """

    def __init__(self, canvas, palette, x, y, height, get_pos, set_pos, absolute=False):
        """
        :param canvas: The canvas on which to draw the scroll bar.
        :param palette: The palette of the parent Frame.
        :param x: The x location of the top of the scroll bar.
        :param y: The y location of the top of the scroll bar.
        :param height: The height of the scroll bar.
        :param get_pos: A function to return the current position of the scroll bar.
        :param set_pos: A function to set the current position of the scroll bar.
        :param absolute: Whether the scroll bar should use absolute co-ordinates when handling mouse
            events.

        The current position for the scroll bar is defined to be 0.0 at the top and 1.0 at the
        bottom.  The scroll bar will call `get_pos` to find the current position when drawing and
        uses `set_pos` to update this position on a mouse click.

        The widget using the scroll bar is responsible for maintaining its own state of where the
        current view is scrolled (e.g. which is the top line in a text box) and for providing
        these two functions to translate that internal state into a form the scroll bar can use.
        """
        self._canvas = canvas
        self.palette = palette
        self.max_height = 0
        self._x = x
        self._y = y
        self._height = height
        self._absolute = absolute
        self._get_pos = get_pos
        self._set_pos = set_pos

    def update(self):
        """
        Draw the scroll bar.
        """
        # Sort out chars
        cursor = "█" if self._canvas.unicode_aware else "O"
        back = "░" if self._canvas.unicode_aware else "|"

        # Now draw...
        try:
            sb_pos = self._get_pos()
            sb_pos = min(1, max(0, sb_pos))
            sb_pos = max(int(self._height * sb_pos) - 1, 0)
        except ZeroDivisionError:
            sb_pos = 0
        (colour, attr, bg) = self.palette["scroll"]
        y = self._canvas.start_line if self._absolute else 0
        for dy in range(self._height):
            self._canvas.print_at(cursor if dy == sb_pos else back,
                                  self._x, y + self._y + dy,
                                  colour, attr, bg)

    def is_mouse_over(self, event):
        """
        Check whether a MouseEvent is over thus scroll bar.

        :param event: The MouseEvent to check.

        :returns: True if the mouse event is over the scroll bar.
        """
        return event.x == self._x and self._y <= event.y < self._y + self._height

    def process_event(self, event):
        """
        Handle input on the scroll bar.

        :param event: the event to be processed.

        :returns: True if the scroll bar handled the event.
        """
        # Convert into absolute coordinates if needed.
        new_event = event
        if self._absolute:
            new_event.y -= self._canvas.start_line

        # Process event if needed.
        if self.is_mouse_over(new_event) and event.buttons != 0:
            self._set_pos((new_event.y - self._y) / (self._height - 1))
            return True
        return False
