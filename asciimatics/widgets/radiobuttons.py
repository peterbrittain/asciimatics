"""This module implements the widget for radio buttons"""
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.screen import Screen
from asciimatics.widgets.widget import Widget


class RadioButtons(Widget):
    """
    A RadioButtons widget is used to ask for one of a list of values to be selected by the user.

    It consists of an optional label and then a list of selection bullets with field names.
    """

    __slots__ = ["_options", "_selection", "_start_column", "_on_change"]

    def __init__(self, options, label=None, name=None, on_change=None, **kwargs):
        """
        :param options: A list of (text, value) tuples for each radio button.
        :param label: An optional label for the widget.
        :param name: The internal name for the widget.
        :param on_change: Optional function to call when text changes.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super().__init__(name, **kwargs)
        self._options = options
        self._label = label
        self._selection = 0
        self._start_column = 0
        self._on_change = on_change

    def update(self, frame_no):
        self._draw_label()

        # Decide on check char
        check_char = "•" if self._frame.canvas.unicode_aware else "X"

        # Render the list of radio buttons.
        for i, (text, _) in enumerate(self._options):
            fg, attr, bg = self._pick_colours("control", self._has_focus and i == self._selection)
            fg2, attr2, bg2 = self._pick_colours("field", self._has_focus and i == self._selection)
            check = check_char if i == self._selection else " "
            self._frame.canvas.print_at(
                f"({check}) ",
                self._x + self._offset,
                self._y + i,
                fg, attr, bg)
            self._frame.canvas.print_at(
                text,
                self._x + self._offset + 4,
                self._y + i,
                fg2, attr2, bg2)

    def reset(self):
        pass

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code == Screen.KEY_UP:
                # Use property to trigger events.
                self._selection = max(0, self._selection - 1)
                self.value = self._options[self._selection][1]
            elif event.key_code == Screen.KEY_DOWN:
                # Use property to trigger events.
                self._selection = min(self._selection + 1,
                                      len(self._options) - 1)
                self.value = self._options[self._selection][1]
            else:
                # Ignore any other key press.
                return event
        elif isinstance(event, MouseEvent):
            # Mouse event - rebase coordinates to Frame context.
            if event.buttons != 0:
                if self.is_mouse_over(event, include_label=False):
                    # Use property to trigger events.
                    self._selection = event.y - self._y
                    self.value = self._options[self._selection][1]
                    return None
            # Ignore other mouse events.
            return event
        else:
            # Ignore non-keyboard events
            return event

        # If we got here, we processed the event - swallow it.
        return None

    def required_height(self, offset, width):
        return len(self._options)

    @property
    def value(self):
        """
        The current value for these RadioButtons.
        """
        # The value is actually the value of the current selection.
        return self._options[self._selection][1]

    @value.setter
    def value(self, new_value):
        # Only trigger the notification after we've changed the value.
        old_value = self._value
        for i, (_, value) in enumerate(self._options):
            if new_value == value:
                self._selection = i
                break
        else:
            self._selection = 0
        self._value = self._options[self._selection][1]
        if old_value != self._value and self._on_change:
            self._on_change()
