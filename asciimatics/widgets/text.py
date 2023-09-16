"""This widget implements a text based input field"""
from re import match
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.screen import Screen
from asciimatics.widgets.utilities import _find_min_start, _enforce_width, _get_offset
from asciimatics.widgets.widget import Widget


class Text(Widget):
    """
    A Text widget is a single line input field.

    It consists of an optional label and an entry box.
    """

    __slots__ = ["_column", "_start_column", "_on_change", "_validator", "_hide_char", "_max_length"]

    def __init__(self, label=None, name=None, on_change=None, validator=None, hide_char=None,
                 max_length=None, readonly=False, **kwargs):
        """
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        :param on_change: Optional function to call when text changes.
        :param validator: Optional definition of valid data for this widget.
            This can be a function (which takes the current value and returns True for valid
            content) or a regex string (which must match the entire allowed value).
        :param hide_char: Character to use instead of what the user types - e.g. to hide passwords.
        :param max_length: Optional maximum length of the field.  If set, the widget will limit
            data entry to this length.
        :param readonly: Whether the widget prevents user input to change values.  Default is False.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super().__init__(name, **kwargs)
        self._label = label
        self._column = 0
        self._start_column = 0
        self._on_change = on_change
        self._validator = validator
        self._hide_char = hide_char
        self._max_length = max_length
        self._readonly = readonly

    def set_layout(self, x, y, offset, w, h):
        # Do the usual layout work. then apply max length to resulting dimensions.
        super().set_layout(x, y, offset, w, h)
        if self._max_length:
            # Allow extra char for cursor, so contents don't scroll at required length
            self._w = min(self._w, self._max_length + self._offset + 1)

    def update(self, frame_no):
        self._draw_label()

        # Calculate new visible limits if needed.
        self._start_column = min(self._start_column, self._column)
        self._start_column += _find_min_start(self._value[self._start_column:self._column + 1],
                                              self.width, self._frame.canvas.unicode_aware,
                                              self._column >= self.string_len(self._value))

        # Render visible portion of the text.
        (colour, attr, background) = self._pick_colours("readonly" if self._readonly else "edit_text")
        text = self._value[self._start_column:]
        text = _enforce_width(text, self.width, self._frame.canvas.unicode_aware)
        if self._hide_char:
            text = self._hide_char[0] * len(text)
        text += " " * (self.width - self.string_len(text))
        self._frame.canvas.print_at(
            text,
            self._x + self._offset,
            self._y,
            colour, attr, background)

        # Since we switch off the standard cursor, we need to emulate our own
        # if we have the input focus.
        if self._has_focus:
            text_width = self.string_len(text[:self._column - self._start_column])
            self._draw_cursor(
                " " if self._column >= len(self._value) else self._hide_char[0] if self._hide_char
                else self._value[self._column],
                frame_no,
                self._x + self._offset + text_width,
                self._y)

    def reset(self):
        # Reset to original data and move to end of the text.
        self._start_column = 0
        self._column = len(self._value)

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code == Screen.KEY_BACK and not self._readonly:
                if self._column > 0:
                    # Delete character in front of cursor.
                    self._set_and_check_value("".join([self._value[:self._column - 1],
                                                       self._value[self._column:]]))
                    self._column -= 1
            elif event.key_code == Screen.KEY_DELETE and not self._readonly:
                if self._column < len(self._value):
                    self._set_and_check_value("".join([self._value[:self._column],
                                                       self._value[self._column + 1:]]))
            elif event.key_code == Screen.KEY_LEFT:
                self._column -= 1
                self._column = max(self._column, 0)
            elif event.key_code == Screen.KEY_RIGHT:
                self._column += 1
                self._column = min(len(self._value), self._column)
            elif event.key_code == Screen.KEY_HOME:
                self._column = 0
            elif event.key_code == Screen.KEY_END:
                self._column = len(self._value)
            elif event.key_code >= 32 and not self._readonly:
                # Enforce required max length - swallow event if not allowed
                if self._max_length is None or len(self._value) < self._max_length:
                    # Insert any visible text at the current cursor position.
                    self._set_and_check_value(chr(event.key_code).join([self._value[:self._column],
                                                                        self._value[self._column:]]))
                    self._column += 1
            else:
                # Ignore any other key press.
                return event
        elif isinstance(event, MouseEvent):
            # Mouse event - rebase coordinates to Frame context.
            if event.buttons != 0:
                if self.is_mouse_over(event, include_label=False):
                    self._column = (self._start_column +
                                    _get_offset(self._value[self._start_column:],
                                                event.x - self._x - self._offset,
                                                self._frame.canvas.unicode_aware))
                    self._column = min(len(self._value), self._column)
                    self._column = max(0, self._column)
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
    def frame_update_count(self):
        # Force refresh for cursor if needed.
        return 5 if self._has_focus and not self._frame.reduce_cpu else 0

    @property
    def readonly(self):
        """
        Whether this widget is readonly or not.
        """
        return self._readonly

    @readonly.setter
    def readonly(self, new_value):
        self._readonly = new_value

    @property
    def value(self):
        """
        The current value for this Text.
        """
        return self._value

    @value.setter
    def value(self, new_value):
        self._set_and_check_value(new_value, reset=True)

    def _set_and_check_value(self, new_value, reset=False):
        # Only trigger the notification after we've changed the value.
        old_value = self._value
        self._value = new_value if new_value else ""
        if reset:
            self.reset()
        if old_value != self._value and self._on_change:
            self._on_change()
        if self._validator:
            if callable(self._validator):
                self._is_valid = self._validator(self._value)
            else:
                self._is_valid = match(self._validator, self._value) is not None
