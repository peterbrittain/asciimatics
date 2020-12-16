"""This is the baseclass for list box types"""
from datetime import datetime, timedelta
from abc import ABCMeta, abstractmethod, abstractproperty
from future.utils import with_metaclass
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.screen import Screen
from asciimatics.widgets.widget import Widget
from asciimatics.widgets.scrollbar import _ScrollBar

class _BaseListBox(with_metaclass(ABCMeta, Widget)):
    """
    An Internal class to contain common function between list box types.
    """

    __slots__ = ["_options", "_titles", "_label", "_line", "_start_line", "_required_height", "_on_change",
                 "_on_select", "_validator", "_search", "_last_search", "_scroll_bar", "_parser"]

    def __init__(self, height, options, titles=None, label=None, name=None, parser=None,
                 on_change=None, on_select=None, validator=None):
        """
        :param height: The required number of input lines for this widget.
        :param options: The options for each row in the widget.
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        :param parser: Optional parser to colour text.
        :param on_change: Optional function to call when selection changes.
        :param on_select: Optional function to call when the user actually selects an entry from
            this list - e.g. by double-clicking or pressing Enter.
        :param validator: Optional function to validate selection for this widget.
        """
        super(_BaseListBox, self).__init__(name)
        self._titles = titles
        self._label = label
        self._parser = parser
        self._options = self._parse_options(options)
        self._line = 0
        self._value = None
        self._start_line = 0
        self._required_height = height
        self._on_change = on_change
        self._on_select = on_select
        self._validator = validator
        self._search = ""
        self._last_search = datetime.now()
        self._scroll_bar = None

    def reset(self):
        pass

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if len(self._options) > 0 and event.key_code == Screen.KEY_UP:
                # Move up one line in text - use value to trigger on_select.
                self._line = max(0, self._line - 1)
                self.value = self._options[self._line][1]
            elif len(self._options) > 0 and event.key_code == Screen.KEY_DOWN:
                # Move down one line in text - use value to trigger on_select.
                self._line = min(len(self._options) - 1, self._line + 1)
                self.value = self._options[self._line][1]
            elif len(self._options) > 0 and event.key_code == Screen.KEY_PAGE_UP:
                # Move up one page.
                self._line = max(0, self._line - self._h + (1 if self._titles else 0))
                self.value = self._options[self._line][1]
            elif len(self._options) > 0 and event.key_code == Screen.KEY_PAGE_DOWN:
                # Move down one page.
                self._line = min(
                    len(self._options) - 1, self._line + self._h - (1 if self._titles else 0))
                self.value = self._options[self._line][1]
            elif event.key_code in [Screen.ctrl("m"), Screen.ctrl("j")]:
                # Fire select callback.
                if self._on_select:
                    self._on_select()
            elif event.key_code > 0:
                # Treat any other normal press as a search
                now = datetime.now()
                if now - self._last_search >= timedelta(seconds=1):
                    self._search = ""
                self._search += chr(event.key_code)
                self._last_search = now

                # If we find a new match for the search string, update the list selection
                new_value = self._find_option(self._search)
                if new_value is not None:
                    self.value = new_value
            else:
                return event
        elif isinstance(event, MouseEvent):
            # Mouse event - adjust for scroll bar as needed.
            if event.buttons != 0:
                # Check for normal widget.
                if (len(self._options) > 0 and
                        self.is_mouse_over(event, include_label=False,
                                           width_modifier=1 if self._scroll_bar else 0)):
                    # Figure out selected line
                    new_line = event.y - self._y + self._start_line
                    if self._titles:
                        new_line -= 1
                    new_line = min(new_line, len(self._options) - 1)

                    # Update selection and fire select callback if needed.
                    if new_line >= 0:
                        self._line = new_line
                        self.value = self._options[self._line][1]
                        if event.buttons & MouseEvent.DOUBLE_CLICK != 0 and self._on_select:
                            self._on_select()
                    return None

                # Check for scroll bar interactions:
                if self._scroll_bar:
                    if self._scroll_bar.process_event(event):
                        return None

            # Ignore other mouse events.
            return event
        else:
            # Ignore other events
            return event

        # If we got here, we processed the event - swallow it.
        return None

    def _add_or_remove_scrollbar(self, width, height, dy):
        """
        Add or remove a scrollbar from this listbox based on height and available options.

        :param width: Width of the Listbox
        :param height: Height of the Listbox.
        :param dy: Vertical offset from top of widget.
        """
        if self._scroll_bar is None and len(self._options) > height:
            self._scroll_bar = _ScrollBar(
                self._frame.canvas, self._frame.palette, self._x + width - 1, self._y + dy,
                height, self._get_pos, self._set_pos)
        elif self._scroll_bar is not None and len(self._options) <= height:
            self._scroll_bar = None

    def _get_pos(self):
        """
        Get current position for scroll bar.
        """
        if self._h >= len(self._options):
            return 0
        return self._start_line / (len(self._options) - self._h)

    def _set_pos(self, pos):
        """
        Set current position for scroll bar.
        """
        if self._h < len(self._options):
            pos *= len(self._options) - self._h
            pos = int(round(max(0, pos), 0))
            self._start_line = pos

    @abstractmethod
    def _find_option(self, search_value):
        """
        Internal function called by the BaseListBox to do a text search on user input.

        :param search_value: The string value to search for in the list.
        :return: The value of the matching option (or None if nothing matches).
        """

    def required_height(self, offset, width):
        return self._required_height

    @property
    def start_line(self):
        """
        The line that will be drawn at the top of the visible section of this list.
        """
        return self._start_line

    @start_line.setter
    def start_line(self, new_value):
        if 0 <= new_value < len(self._options):
            self._start_line = new_value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        # Only trigger change notification after we've changed selection
        old_value = self._value
        self._value = new_value
        for i, [_, value] in enumerate(self._options):
            if value == new_value:
                self._line = i
                break
        else:
            # No matching value - pick a default.
            if len(self._options) > 0:
                self._line = 0
                self._value = self._options[self._line][1]
            else:
                self._line = -1
                self._value = None
        if self._validator:
            self._is_valid = self._validator(self._value)
        if old_value != self._value and self._on_change:
            self._on_change()

        # Fix up the start line now that we've explicitly set a new value.
        self._start_line = max(
            0, max(self._line - self._h + 1, min(self._start_line, self._line)))

    def _parse_options(self, options):
        """
        Parse a the options list for ColouredText.

        :param options: the options list to parse
        :returns: the options list parsed and converted to ColouredText as needed.
        """
        if self._parser:
            parsed_value = []
            for option in options:
                parsed_value.append((self._parse_option(option[0]), option[1]))
            return parsed_value
        return options

    @abstractmethod
    def _parse_option(self, option):
        """
        Parse a single option for ColouredText.

        :param option: the option to parse
        :returns: the option parsed and converted to ColouredText.
        """

    @abstractproperty
    def options(self):
        """
        The list of options available for user selection.
        """
