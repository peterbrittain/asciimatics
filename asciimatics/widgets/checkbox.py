"""This module defines a checkbox widget"""
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.widgets.widget import Widget


class CheckBox(Widget):
    """
    A CheckBox widget is used to ask for Boolean (i.e. yes/no) input.

    It consists of an optional label (typically used for the first in a group of CheckBoxes),
    the box and a field name.
    """

    __slots__ = ["_text", "_on_change"]

    def __init__(self, text, label=None, name=None, on_change=None, **kwargs):
        """
        :param text: The text to explain this specific field to the user.
        :param label: An optional label for the widget.
        :param name: The internal name for the widget.
        :param on_change: Optional function to call when text changes.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super().__init__(name, **kwargs)
        self._text = text
        self._label = label
        self._on_change = on_change

    def update(self, frame_no):
        self._draw_label()

        # Render this checkbox.
        check_char = "✓" if self._frame.canvas.unicode_aware else "X"
        (colour, attr, bg) = self._pick_colours("control", self._has_focus)
        self._frame.canvas.print_at(
            f"[{check_char if self._value else ' '}]",
            self._x + self._offset,
            self._y,
            colour, attr, bg)
        (colour, attr, bg) = self._pick_colours("field", self._has_focus)
        self._frame.canvas.print_at(
            self._text,
            self._x + self._offset + 4,
            self._y,
            colour, attr, bg)

    def reset(self):
        pass

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord(" "), 10, 13]:
                # Use property to trigger events.
                self.value = not self._value
            else:
                # Ignore any other key press.
                return event
        elif isinstance(event, MouseEvent):
            # Mouse event - rebase coordinates to Frame context.
            if event.buttons != 0:
                if self.is_mouse_over(event, include_label=False):
                    # Use property to trigger events.
                    self.value = not self._value
                    return None
            # Ignore other mouse events.
            return event
        else:
            # Ignore other events
            return event

        # If we got here, we processed the event - swallow it.
        return None

    def required_height(self, offset, width):
        return 1

    @property
    def value(self):
        """
        The current value for this Checkbox.
        """
        return self._value

    @value.setter
    def value(self, new_value):
        # Only trigger the notification after we've changed the value.
        old_value = self._value
        self._value = new_value if new_value else False
        if old_value != self._value and self._on_change:
            self._on_change()
