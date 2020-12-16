"""This module implements a multi line editing text box"""
from copy import copy
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.screen import Screen
from asciimatics.strings import ColouredText
from asciimatics.widgets.widget import Widget
from asciimatics.widgets.utilities import _find_min_start, _enforce_width, logger, _get_offset

class TextBox(Widget):
    """
    A TextBox is a widget for multi-line text editing.

    It consists of a framed box with option label.
    """

    __slots__ = ["_label", "_line", "_column", "_start_line", "_start_column", "_required_height",
                 "_as_string", "_line_wrap", "_on_change", "_reflowed_text_cache", "_parser",
                 "_readonly"]

    def __init__(self, height, label=None, name=None, as_string=False, line_wrap=False, parser=None,
                 on_change=None, readonly=False, **kwargs):
        """
        :param height: The required number of input lines for this TextBox.
        :param label: An optional label for the widget.
        :param name: The name for the TextBox.
        :param as_string: Use string with newline separator instead of a list
            for the value of this widget.
        :param line_wrap: Whether to wrap at the end of the line.
        :param parser: Optional parser to colour text.
        :param on_change: Optional function to call when text changes.
        :param readonly: Whether the widget prevents user input to change values.  Default is False.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super(TextBox, self).__init__(name, **kwargs)
        self._label = label
        self._line = 0
        self._column = 0
        self._start_line = 0
        self._start_column = 0
        self._required_height = height
        self._as_string = as_string
        self._line_wrap = line_wrap
        self._parser = parser
        self._on_change = on_change
        self._reflowed_text_cache = None
        self._readonly = readonly

    def update(self, frame_no):
        self._draw_label()

        # Calculate new visible limits if needed.
        height = self._h
        if not self._line_wrap:
            self._start_column = min(self._start_column, self._column)
            self._start_column += _find_min_start(
                str(self._value[self._line][self._start_column:self._column + 1]),
                self.width,
                self._frame.canvas.unicode_aware,
                self._column >= self.string_len(str(self._value[self._line])))

        # Clear out the existing box content
        (colour, attr, background) = self._pick_colours("readonly" if self._readonly else "edit_text")
        self._frame.canvas.clear_buffer(
            colour, attr, background, self._x + self._offset, self._y, self.width, height)

        # Convert value offset to display offsets
        # NOTE: _start_column is always in display coordinates.
        display_text = self._reflowed_text
        display_start_column = self._start_column
        display_line, display_column = 0, 0
        for i, (_, line, col) in enumerate(display_text):
            if line < self._line or (line == self._line and col <= self._column):
                display_line = i
                display_column = self._column - col

        # Restrict to visible/valid content.
        self._start_line = max(0, max(display_line - height + 1,
                                      min(self._start_line, display_line)))

        # Render visible portion of the text.
        for line, (text, _, _) in enumerate(display_text):
            if self._start_line <= line < self._start_line + height:
                paint_text = _enforce_width(
                    text[display_start_column:], self.width, self._frame.canvas.unicode_aware)
                self._frame.canvas.paint(
                    str(paint_text),
                    self._x + self._offset,
                    self._y + line - self._start_line,
                    colour, attr, background,
                    colour_map=paint_text.colour_map if hasattr(paint_text, "colour_map") else None)

        # Since we switch off the standard cursor, we need to emulate our own
        # if we have the input focus.
        if self._has_focus:
            line = str(display_text[display_line][0])
            logger.debug("Cursor: %d,%d", display_start_column, display_column)
            text_width = self.string_len(line[display_start_column:display_column])
            self._draw_cursor(
                " " if display_column >= len(line) else line[display_column],
                frame_no,
                self._x + self._offset + text_width,
                self._y + display_line - self._start_line)

    def reset(self):
        # Reset to original data and move to end of the text.
        self._start_line = 0
        self._line = len(self._value) - 1
        self._column = 0 if self._is_disabled else len(self._value[self._line])
        self._reflowed_text_cache = None

    def _change_line(self, delta):
        """
        Move the cursor up/down the specified number of lines.

        :param delta: The number of lines to move (-ve is up, +ve is down).
        """
        # Ensure new line is within limits
        self._line = min(max(0, self._line + delta), len(self._value) - 1)

        # Fix up column if the new line is shorter than before.
        if self._column >= len(self._value[self._line]):
            self._column = len(self._value[self._line])

    def process_event(self, event):
        def _join(a, b):
            if self._parser:
                return ColouredText(a, self._parser, colour=b[0].first_colour).join(b)
            return a.join(b)

        if isinstance(event, KeyboardEvent):
            old_value = copy(self._value)
            if event.key_code in [10, 13] and not self._readonly:
                # Split and insert line  on CR or LF.
                self._value.insert(self._line + 1,
                                   self._value[self._line][self._column:])
                self._value[self._line] = self._value[self._line][:self._column]
                self._line += 1
                self._column = 0
            elif event.key_code == Screen.KEY_BACK and not self._readonly:
                if self._column > 0:
                    # Delete character in front of cursor.
                    self._value[self._line] = _join(
                        "",
                        [self._value[self._line][:self._column - 1], self._value[self._line][self._column:]])
                    self._column -= 1
                else:
                    if self._line > 0:
                        # Join this line with previous
                        self._line -= 1
                        self._column = len(self._value[self._line])
                        self._value[self._line] += \
                            self._value.pop(self._line + 1)
            elif event.key_code == Screen.KEY_DELETE and not self._readonly:
                if self._column < len(self._value[self._line]):
                    self._value[self._line] = _join(
                        "",
                        [self._value[self._line][:self._column], self._value[self._line][self._column + 1:]])
                else:
                    if self._line < len(self._value) - 1:
                        # Join this line with next
                        self._value[self._line] += \
                            self._value.pop(self._line + 1)
            elif event.key_code == Screen.KEY_PAGE_UP:
                self._change_line(-self._h)
            elif event.key_code == Screen.KEY_PAGE_DOWN:
                self._change_line(self._h)
            elif event.key_code == Screen.KEY_UP:
                self._change_line(-1)
            elif event.key_code == Screen.KEY_DOWN:
                self._change_line(1)
            elif event.key_code == Screen.KEY_LEFT:
                # Move left one char, wrapping to previous line if needed.
                self._column -= 1
                if self._column < 0:
                    if self._line > 0:
                        self._line -= 1
                        self._column = len(self._value[self._line])
                    else:
                        self._column = 0
            elif event.key_code == Screen.KEY_RIGHT:
                # Move right one char, wrapping to next line if needed.
                self._column += 1
                if self._column > len(self._value[self._line]):
                    if self._line < len(self._value) - 1:
                        self._line += 1
                        self._column = 0
                    else:
                        self._column = len(self._value[self._line])
            elif event.key_code == Screen.KEY_HOME:
                # Go to the start of this line
                self._column = 0
            elif event.key_code == Screen.KEY_END:
                # Go to the end of this line
                self._column = len(self._value[self._line])
            elif event.key_code >= 32 and not self._readonly:
                # Insert any visible text at the current cursor position.
                self._value[self._line] = _join(
                    chr(event.key_code),
                    [self._value[self._line][:self._column], self._value[self._line][self._column:]])
                self._column += 1
            else:
                # Ignore any other key press.
                return event

            # If we got here we might have changed the value...
            if old_value != self._value:
                self._reflowed_text_cache = None
                if self._on_change:
                    self._on_change()

        elif isinstance(event, MouseEvent):
            # Mouse event - rebase coordinates to Frame context.
            if event.buttons != 0:
                if self.is_mouse_over(event, include_label=False):
                    # Find the line first.
                    clicked_line = event.y - self._y + self._start_line
                    if self._line_wrap:
                        # Line-wrapped text needs to be mapped to visible lines
                        display_text = self._reflowed_text
                        clicked_line = min(clicked_line, len(display_text) - 1)
                        text_line = display_text[clicked_line][1]
                        text_col = display_text[clicked_line][2]
                    else:
                        # non-wrapped just needs a little end protection
                        text_line = max(0, clicked_line)
                        text_col = 0
                    self._line = min(len(self._value) - 1, text_line)

                    # Now figure out location in text based on width of each glyph.
                    self._column = (self._start_column + text_col +
                                    _get_offset(
                                        str(self._value[self._line][self._start_column + text_col:]),
                                        event.x - self._x - self._offset,
                                        self._frame.canvas.unicode_aware))
                    self._column = min(len(self._value[self._line]), self._column)
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
        return self._required_height

    @property
    def _reflowed_text(self):
        """
        The text as should be formatted on the screen.

        This is an array of tuples of the form (text, value line, value column offset) where
        the line and column offsets are indeces into the value (not displayed glyph coordinates).
        """
        if self._reflowed_text_cache is None:
            if self._line_wrap:
                self._reflowed_text_cache = []
                limit = self._w - self._offset
                for i, line in enumerate(self._value):
                    column = 0
                    while self.string_len(str(line)) >= limit:
                        sub_string = _enforce_width(
                            line, limit, self._frame.canvas.unicode_aware)
                        self._reflowed_text_cache.append((sub_string, i, column))
                        line = line[len(sub_string):]
                        column += len(sub_string)
                    self._reflowed_text_cache.append((line, i, column))
            else:
                self._reflowed_text_cache = [(x, i, 0) for i, x in enumerate(self._value)]

        return self._reflowed_text_cache

    @property
    def value(self):
        if self._value is None:
            self._value = [""]
        return "\n".join([str(x) for x in self._value]) if self._as_string else self._value

    @value.setter
    def value(self, new_value):
        # Convert to the internal format
        old_value = self._value
        if new_value is None:
            new_value = [""]
        elif self._as_string:
            new_value = new_value.split("\n")
        self._value = new_value

        # TODO: Sort out speed of this code
        if self._parser:
            new_value = []
            last_colour = None
            for line in self._value:
                if hasattr(line, "raw_text"):
                    value = line
                else:
                    value = ColouredText(line, self._parser, colour=last_colour)
                new_value.append(value)
                last_colour = value.last_colour
            self._value = new_value
        self.reset()

        # Only trigger the notification after we've changed the value.
        if old_value != self._value and self._on_change:
            self._on_change()

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
    def frame_update_count(self):
        # Force refresh for cursor if needed.
        return 5 if self._has_focus and not self._frame.reduce_cpu else 0
