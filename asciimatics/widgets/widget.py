"""
This module allows you to create interactive text user interfaces.  For more details see
http://asciimatics.readthedocs.io/en/latest/widgets.html
"""
from abc import ABCMeta, abstractmethod

from logging import getLogger
from wcwidth import wcswidth
from asciimatics.screen import Screen
from asciimatics.widgets.utilities import _split_text

# Logging
logger = getLogger(__name__)


class Widget(metaclass=ABCMeta):
    """
    A Widget is a re-usable component that can be used to create a simple GUI.
    """

    #: Widgets with this constant for the required height will be re-sized to
    #: fit the available vertical space in the Layout.
    FILL_FRAME = -135792468

    #: Widgets with this constant for the required height will be re-sized to
    #: fit the maximum space used by any other column in the Layout.
    FILL_COLUMN = -135792467

    __slots__ = ["_name", "_label", "_frame", "_value", "_has_focus", "_x",
                 "_y", "_h", "_w", "_offset", "_display_label", "_is_tab_stop",
                 "_is_disabled", "_is_valid", "_custom_colour", "_on_focus",
                 "_on_blur", "string_len", "_readonly"]

    def __init__(self, name, tab_stop=True, disabled=False, on_focus=None, on_blur=None):
        """
        :param name: The name of this Widget.
        :param tab_stop: Whether this widget should take focus or not when tabbing around the Frame.
        :param disabled: Whether this Widget should be disabled or not.
        :param on_focus: Optional callback whenever this widget gets the focus.
        :param on_blur: Optional callback whenever this widget loses the focus.
        """
        super().__init__()
        # Internal properties
        self._name = name
        self._label = None
        self._frame = None
        self._value = None
        self._has_focus = False
        self._x = self._y = 0
        self._w = self._h = 0
        self._offset = 0
        self._display_label = None
        self._is_tab_stop = tab_stop
        self._is_disabled = disabled
        self._is_valid = True
        self._custom_colour = None
        self._on_focus = on_focus
        self._on_blur = on_blur
        self._readonly = False

        # Helper function to optimise string length calculations - default for now and pick
        # the optimal version when we know whether we need unicode support or not.
        self.string_len = wcswidth

    @property
    def frame(self):
        """
        The Frame that contains this Widget.
        """
        return self._frame

    @property
    def is_valid(self):
        """
        Whether this widget has passed its data validation or not.
        """
        return self._is_valid

    @property
    def is_tab_stop(self):
        """
        Whether this widget is a valid tab stop for keyboard navigation.
        """
        return self._is_tab_stop

    @property
    def is_visible(self):
        """
        Whether this widget is visible on the Canvas or not.
        """
        return not (self._y + self._h <= self._frame.canvas.start_line or
                    self._y >= self._frame.canvas.start_line + self._frame.canvas.height)

    @property
    def disabled(self):
        """
        Whether this widget is disabled or not.
        """
        return self._is_disabled

    @disabled.setter
    def disabled(self, new_value):
        self._is_disabled = new_value

    @property
    def custom_colour(self):
        """
        A custom colour to use instead of the normal calculated one when drawing this widget.

        This must be a key name from the palette dictionary.
        """
        return self._custom_colour

    @custom_colour.setter
    def custom_colour(self, new_value):
        self._custom_colour = new_value

    @property
    def frame_update_count(self):
        """
        The number of frames before this Widget should be updated.
        """
        return 0

    @property
    def width(self):
        """
        The width of this Widget (excluding any labels).

        Only valid after the Frame has been fixed in place.
        """
        return self._w - self._offset

    def register_frame(self, frame):
        """
        Register the Frame that owns this Widget.

        :param frame: The owning Frame.
        """
        self._frame = frame
        self.string_len = wcswidth if self._frame.canvas.unicode_aware else len

    def set_layout(self, x, y, offset, w, h):
        """
        Set the size and position of the Widget.

        This should not be called directly.  It is used by the :py:obj:`.Layout` class to arrange
        all widgets within the Frame.

        :param x: The x position of the widget.
        :param y: The y position of the widget.
        :param offset: The allowed label size for the widget.
        :param w: The width of the widget.
        :param h: The height of the widget.
        """
        self._x = x
        self._y = y
        self._offset = offset
        self._w = w
        self._h = h

    def get_location(self):
        """
        Return the absolute location of this widget on the Screen, taking into account the
        current state of the Frame that is displaying it and any label offsets of the Widget.

        :returns: A tuple of the form (<X coordinate>, <Y coordinate>).
        """
        origin = self._frame.canvas.origin
        return (self._x + origin[0] + self._offset,
                self._y + origin[1] - self._frame.canvas.start_line)

    def focus(self):
        """
        Call this to give this Widget the input focus.
        """
        logger.debug("Widget focus: %s", self)
        self._has_focus = True
        self._frame.move_to(self._x, self._y, self._h)
        if self._on_focus is not None:
            self._on_focus()

    def is_mouse_over(self, event, include_label=True, width_modifier=0):
        """
        Check if the specified mouse event is over this widget.

        :param event: The MouseEvent to check.
        :param include_label: Include space reserved for the label when checking.
        :param width_modifier: Adjustment to width (e.g. for scroll bars).
        :returns: True if the mouse is over the active parts of the widget.
        """
        # Disabled widgets should not react to the mouse.
        logger.debug("Widget: %s (%d, %d) (%d, %d)", self, self._x, self._y, self._w, self._h)
        if self._is_disabled:
            return False

        # Check this part of the canvas is visible - can't be clicked if not visible.
        if (event.y < self._frame.canvas.start_line or
                event.y >= self._frame.canvas.start_line + self._frame.canvas.height):
            return False

        # Check for any overlap
        if self._y <= event.y < self._y + self._h:
            if ((include_label and self._x <= event.x < self._x + self._w - width_modifier) or
                    (self._x + self._offset <= event.x < self._x + self._w - width_modifier)):
                return True

        return False

    def blur(self):
        """
        Call this to take the input focus from this Widget.
        """
        logger.debug("Widget blur: %s", self)
        self._has_focus = False
        if self._on_blur is not None:
            self._on_blur()

    def _draw_label(self):
        """
        Draw the label for this widget if needed.
        """
        if self._label is not None:
            # Break the label up as required.
            if self._display_label is None:
                # noinspection PyTypeChecker
                self._display_label = _split_text(
                    self._label, self._offset, self._h, self._frame.canvas.unicode_aware)

            # Draw the  display label.
            (colour, attr, background) = self._frame.palette["label"]
            for i, text in enumerate(self._display_label):
                self._frame.canvas.paint(
                    text, self._x, self._y + i, colour, attr, background)

    def _draw_cursor(self, char, frame_no, x, y):
        """
        Draw a flashing cursor for this widget.

        :param char: The character to use for the cursor (when not a block)
        :param frame_no: The current frame number.
        :param x: The x coordinate for the cursor.
        :param y: The y coordinate for the cursor.
        """
        (colour, attr, background) = self._pick_colours("readonly" if self._readonly else "edit_text")
        if frame_no % 10 < 5 or self._frame.reduce_cpu:
            attr |= Screen.A_REVERSE
        self._frame.canvas.print_at(char, x, y, colour, attr, background)

    def _pick_palette_key(self, palette_name, selected=False, allow_input_state=True):
        """
        Pick the rendering colour for a widget based on the current state.

        :param palette_name: The stem name for the widget - e.g. "button".
        :param selected: Whether this item is selected or not.
        :param allow_input_state: Whether to allow input state (e.g. focus) to affect result.
        :returns: A colour palette key to be used.
        """
        key = palette_name
        if self._custom_colour:
            key = self._custom_colour
        elif self.disabled:
            key = "disabled"
        elif not self._is_valid:
            key = "invalid"
        elif allow_input_state:
            if self._has_focus:
                key = "focus_" + palette_name
            if selected:
                key = "selected_" + key
        return key

    def _pick_colours(self, palette_name, selected=False):
        """
        Pick the rendering colour for a widget based on the current state.

        :param palette_name: The stem name for the widget - e.g. "button".
        :param selected: Whether this item is selected or not.
        :returns: A colour tuple (fg, attr, background) to be used.
        """
        return self._frame.palette[self._pick_palette_key(palette_name, selected)]

    @abstractmethod
    def update(self, frame_no):
        """
        The update method is called whenever this widget needs to redraw itself.

        :param frame_no: The frame number for this screen update.
        """

    @abstractmethod
    def reset(self):
        """
        The reset method is called whenever the widget needs to go back to its
        default (initially created) state.
        """

    @abstractmethod
    def process_event(self, event):
        """
        Process any input event.

        :param event: The event that was triggered.
        :returns: None if the Effect processed the event, else the original event.
        """

    @property
    def label(self):
        """
        The label for this widget.  Can be `None`.
        """
        return self._label

    @property
    def name(self):
        """
        The name for this widget (for reference in the persistent data).  Can
        be `None`.
        """
        return self._name

    @property
    @abstractmethod
    def value(self):
        """
        The value to return for this widget based on the user's input.
        """

    @abstractmethod
    def required_height(self, offset, width):
        """
        Calculate the minimum required height for this widget.

        :param offset: The allowed width for any labels.
        :param width: The total width of the widget, including labels.
        """
