# -*- coding: utf-8 -*-
"""This module implements a multi line read-only text box"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from builtins import chr
from builtins import str
from copy import copy
from logging import getLogger
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.screen import Screen
from asciimatics.strings import ColouredText
from asciimatics.widgets.widget import Widget
from asciimatics.widgets.utilities import _find_min_start, _enforce_width, _get_offset

# Logging
logger = getLogger(__name__)


class ReadBox(Widget):
    """
    A ReadBox is a widget for multi-line read-only text viewing.

    It consists of a framed box with option label.
    """

    __slots__ = ["_label", "_required_height", "_line_wrap", "_parser",
        "_line_cursor", "_auto_scroll", "_longest", "_viewport_row",
        "_viewport_col", "_cursor_colour", "_content", "_content_changed",
        "_cursor_row"]

    def __init__(self, height, label=None, name=None, as_string=False,
            line_wrap=False, parser=None, on_change=None, **kwargs):
        """
        :param height: The required number of input lines for this ReadBox.
        :param label: An optional label for the widget.
        :param name: The name for the ReadBox.
        :param line_wrap: Whether to wrap at the end of the line.
        :param parser: Optional parser to colour text.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super(ReadBox, self).__init__(name, **kwargs)
        self._label = label

        self._viewport_row = 0
        self._viewport_col = 0

        self._cursor_row = 0

        self._required_height = height
        self._line_wrap = line_wrap
        self._parser = parser
        self._line_cursor = True
        self._cursor_colour = Screen.COLOUR_WHITE
        self._auto_scroll = False

        self._content = []
        self._content_changed = True
        self._longest = 0

    def update(self, frame_no):
        if self._content_changed:
            self._generate_content()

        self._draw_label()

        # Clear out the existing box content
        (colour, attr, background) = self._pick_colours("readonly")
        self._frame.canvas.clear_buffer(colour, attr, background,
            self._x + self._offset, self._y, self.width, self._h)

        # Loop through the content in the view port
        x = self._viewport_row
        h = self._viewport_row + self._h
        bg = background
        limit = self._w - self._offset

        #logger.debug("******* Updating Viewport")
        #for item in self._content[x:h]:
        #    logger.debug("%s", item)

        for index, (wrap_count, text) in enumerate(self._content[x:h]):
            position = self._viewport_row + index
            bg = background
            virtual_cursor = position
            if wrap_count > 0:
                virtual_cursor = position - wrap_count + 1

            if self._line_cursor and self._cursor_row == virtual_cursor \
                    and self._has_focus:
                #logger.debug("   CURSOR cx=%d vx=%d p=%d wc=%d %s",
                #    self._cursor_row, x, position, wrap_count, text)
                bg = self._cursor_colour

            # Clip the text to the width of the view port
            y = self._viewport_col
            paint_text = text[y:y+limit]
            colour_map = getattr(paint_text, "colour_map", None)

            self._frame.canvas.paint(
                paint_text,
                self._x + self._offset,
                self._y + index,
                colour, attr, bg,
                colour_map=colour_map)

    def reset(self):
        # Reset to original data and move to end of the text.
        self._viewport_row = 0
        self._viewport_col = 0

        self._cursor_row = 0

        if self._auto_scroll and self._content:
            # Scroll to the bottom
            self._change_line( len(self._content) )

    def _cursor_to_line(self, num):
        """Moves the cursor to the given line. Moves the view port if
        required.
        """
        #logger.debug("**** to line num=%d cr=%d vr=%d", num,
        #    self._cursor_row, self._viewport_row)
        if num < 0:
            self._cursor_row = 0
        elif num >= len(self._content):
            self._cursor_row = len(self._content) - 1
        else:
            self._cursor_row = num

        logger.debug("   adjusted cursor cr=%d", self._cursor_row)

        # Adjust cursor for wrapped rows
        if self._line_wrap and self._content[self._cursor_row][0] > 1:
            # Cursor moved to a wrapped line, adjust to the first of the
            # wrapped lines
            self._cursor_row -= self._content[self._cursor_row][0] - 1

            logger.debug("   wrap moved cr=%d", self._cursor_row)

        # Cursor has been moved, adjust the view port if needed
        if self._cursor_row < self._viewport_row:
            self._viewport_row = self._cursor_row
        elif self._cursor_row > self._viewport_row + self._h:
            self._viewport_row = self._cursor_row - self._h

        #logger.debug("   => outcome num=%d cr=%d vr=%d", num,
        #    self._cursor_row, self._viewport_row)

    def _change_line(self, delta):
        """
        Move the cursor up/down the specified number of lines.

        :param delta: The number of lines to move (-ve is up, +ve is down).
        """
        # Ensure new line is within limits
        self._cursor_row = min(max(0, self._cursor_row + delta),
            len(self._content) - 1)

        # If the cursor is on a wrapped line, position it to treat the wrapped
        # lines as a single unit
        if self._line_wrap and self._content[self._cursor_row][0] >= 1:
            if delta < 0 :
                # When moving up, cursor position is top of wrapped group
                self._cursor_row -= self._content[self._cursor_row][0] - 1
            else:
                # When moving down, skip any wrapped lines
                while self._content[self._cursor_row][0] > 1:
                    self._cursor_row += 1
                    if self._content[self._cursor_row][0] == 1:
                        # Hit two sets of wrapped lines in a row: stop
                        break

        # Check if the view port has moved
        if self._cursor_row < self._viewport_row:
            self._viewport_row = self._cursor_row
            return

        if self._cursor_row > self._viewport_row + self._h - 1:
            self._viewport_row = self._cursor_row - self._h + 1

    def _change_vscroll(self, delta):
        """
        Move the scroll port up/down the specified number of lines.

        :param delta: The number of lines to move (-ve is up, +ve is down).
        """
        self._viewport_row += delta

        if self._viewport_row < 0:
            self._viewport_row = 0
        elif self._viewport_row + self._h > len(self._content):
            self._viewport_row = len(self._content) - self._h

    def _change_hscroll(self, delta):
        """
        Move the scroll port left or right the specified number of columns.

        :param delta: The number of lines to move (-ve is left, +ve is right).
        """
        logger.debug("b hscroll y=%d d=%d", self._viewport_col, delta)

        self._viewport_col += delta
        if self._viewport_col < 0:
            self._viewport_col = 0
            return

        farthest = self._longest - (self._w - self._offset)
        logger.debug("  => farthest=%d w=%d l=%d o=%d", farthest, self._w,
            self._longest, self._offset)
        if self._viewport_col > farthest:
            self._viewport_col = farthest

    def _keyboard_event(self, event):
        if event.key_code == Screen.KEY_PAGE_UP:
            self._change_line(-self._h)
        elif event.key_code == Screen.KEY_PAGE_DOWN:
            self._change_line(self._h)
        elif event.key_code == Screen.KEY_UP:
            if self._line_cursor:
                self._change_line(-1)
            else:
                self._change_vscroll(-1)
        elif event.key_code == Screen.KEY_DOWN:
            if self._line_cursor:
                self._change_line(1)
            else:
                self._change_vscroll(1)
        elif event.key_code == Screen.KEY_LEFT and not self._line_wrap:
            self._change_hscroll(-1)
        elif event.key_code == Screen.KEY_RIGHT and not self._line_wrap:
            self._change_hscroll(1)
        elif event.key_code == Screen.KEY_HOME:
            # Go to the top of the view port
            self._change_line( -1 * len(self._content) )
        elif event.key_code == Screen.KEY_END:
            # Go to the bottom of the view port
            self._change_line( len(self._content) )
        else:
            # Ignore any other key press.
            return event

        # Event was handled
        return None

    def _mouse_event(self, event):
        # Mouse event - rebase coordinates to Frame context.
        if event.buttons != 0:
            if self.is_mouse_over(event, include_label=False):
                clicked_line = event.y - self._y + self._viewport_row
                self._cursor_to_line(clicked_line)
                return None

        # Ignore other mouse events.
        return event

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            result = self._keyboard_event(event)
        elif isinstance(event, MouseEvent):
            result = self._mouse_event(event)
        else:
            # Ignore other events
            return event

        return result

    def required_height(self, offset, width):
        return self._required_height

    @property
    def line_cursor(self):
        """
        Set to True to show the line cursor.  Defaults to False.
        """
        return self._hide_cursor

    @line_cursor.setter
    def line_cursor(self, new_value):
        self._line_cursor = new_value

    @property
    def auto_scroll(self):
        """
        When set to True the ReadBox will scroll to the bottom when created or
        next text is added. When set to False, the current scroll position
        will remain even if the contents are changed.

        Defaults to True.
        """
        return self._auto_scroll

    @auto_scroll.setter
    def auto_scroll(self, new_value):
        self._auto_scroll = new_value

    @property
    def cursor_colour(self):
        """The highlighting line cursor's colour. Defaults to white."""
        return self._cursor_colour

    @cursor_colour.setter
    def cursor_colour(self, colour):
        """The highlighting line cursor's colour. Defaults to white."""
        self._cursor_colour = colour


    @property
    def value(self):
        """
        The current value for this ReadBox as a list of strings.
        """
        if self._value is None:
            self._value = [""]
        return self._value

    @value.setter
    def value(self, new_value):
        self._content_changed = True
        self._value = new_value
        if new_value is None:
            return

        self.reset()

    def _generate_content(self):
        # Handle text colour parsing and determine longest line
        self._content = []

        lines = []
        self._longest = 0
        last_colour = None
        for line in self._value:
            # Parse colour escapes from text
            if self._parser and not hasattr(line, "raw_text"):
                line = ColouredText(line, self._parser, colour=last_colour)
                last_colour = line.last_colour

            length = self.string_len(str(line))
            if length > self._longest:
                self._longest = length

            lines.append(line)

        if self._line_wrap:
            # If wrapping lines, each line should be the width of the window
            self._longest = self._w - self._offset

        # Convert to the internal format:
        #
        #   (wrap, text)
        #
        # wrap: bool, True if this is part of a wrapped line
        # text: parsed text
        limit = self._w - self._offset
        for line in lines:
            length = self.string_len(str(line))

            if self._line_wrap and length > limit:
                # Wrapping, deconstruct the line into its parts
                wrap_count = 1
                while self.string_len(str(line)) >= limit:
                    sub_string = _enforce_width(line, limit,
                        self._frame.canvas.unicode_aware)

                    length = self.string_len(str(sub_string))
                    sub_string += ' ' * (self._longest - length)

                    self._content.append( (wrap_count, sub_string) )
                    line = line[len(sub_string):]

                    wrap_count += 1

                length = self.string_len(str(line))
                line += ' ' * (self._longest - length)
                self._content.append( (wrap_count, line) )
            else:
                # Not wrapping lines, pad to longest, then store
                length = self.string_len(str(line))
                line += ' ' * (self._longest - length)
                self._content.append( (0, line) )

        if self._auto_scroll and self._content:
            # Scroll to the bottom
            self._change_line( len(self._content) )

        #logger.debug("**** Content built")
        #for wc, text in self._content:
        #    logger.debug(" %3d *%s*", wc, text)
        self._content_changed = False
