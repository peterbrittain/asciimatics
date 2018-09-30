# -*- coding: utf-8 -*-
"""
This module allows you to create interactive text user interfaces.  For more details see
http://asciimatics.readthedocs.io/en/latest/widgets.html
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from collections import defaultdict, namedtuple
from inspect import isfunction
import re
import os
import unicodedata
from builtins import chr
from builtins import range
from builtins import object
from copy import copy, deepcopy
from functools import partial
from datetime import date, datetime, timedelta
from future.moves.itertools import zip_longest
from future.utils import with_metaclass
from abc import ABCMeta, abstractmethod, abstractproperty
from asciimatics.effects import Effect
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.exceptions import Highlander, InvalidFields
from asciimatics.screen import Screen, Canvas
from asciimatics.utilities import readable_timestamp, readable_mem, _DotDict
from wcwidth import wcswidth, wcwidth

# Logging
from logging import getLogger
logger = getLogger(__name__)


# Standard palettes for use with :py:meth:`~Frame.set_theme`.
_THEMES = {
    "monochrome": defaultdict(
        lambda: (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK),
        {
            "invalid": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_RED),
            "label": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "title": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_focus_field": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_edit_text": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_button": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_focus_control": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK),
        }
    ),
    "green": defaultdict(
        lambda: (Screen.COLOUR_GREEN, Screen.A_NORMAL, Screen.COLOUR_BLACK),
        {
            "invalid": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_RED),
            "label": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "title": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_focus_field": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_edit_text": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_button": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_focus_control": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK),
        }
    ),
    "bright": defaultdict(
        lambda: (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
        {
            "invalid": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_RED),
            "label": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_focus_control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_focus_field": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_button": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_edit_text": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK),
        }
    ),
    "tlj256": defaultdict(
        lambda: (16, 0, 15),
        {
            "invalid": (0, 0, 196),
            "label": (88, 0, 15),
            "title": (88, 0, 15),
            "selected_focus_field": (15, 0, 88),
            "focus_edit_text": (15, 0, 88),
            "focus_button": (15, 0, 88),
            "selected_focus_control": (15, 0, 88),
            "disabled": (8, 0, 15),
        }
    ),
}


def _enforce_width(text, width, unicode_aware=True):
    """
    Enforce a displayed piece of text to be a certain number of cells wide.  This takes into
    account double-width characters used in CJK languages.

    :param text: The text to be truncated
    :param width: The screen cell width to enforce
    :return: The resulting truncated text
    """
    size = 0
    if unicode_aware:
        for i, c in enumerate(text):
            if size + wcwidth(c) > width:
                return text[0:i]
            size += wcwidth(c)
    elif len(text) + 1 > width:
        return text[0:width]
    return text


def _find_min_start(text, max_width, unicode_aware=True, at_end=False):
    """
    Find the starting point in the string that will reduce it to be less than or equal to the
    specified width when displayed on screen.

    :param text: The text to analyze.
    :param max_width: The required maximum width
    :param at_end: At the end of the editable line, so allow spaced for cursor.

    :return: The offset within `text` to start at to reduce it to the required length.
    """
    result = 0
    string_len = wcswidth if unicode_aware else len
    char_len = wcwidth if unicode_aware else lambda x: 1
    display_end = string_len(text)
    while display_end > max_width:
        result += 1
        display_end -= char_len(text[0])
        text = text[1:]
    if at_end and display_end == max_width:
        result += 1
    return result


def _get_offset(text, visible_width, unicode_aware=True):
    """
    Find the character offset within some text for a given visible offset (taking into account the
    fact that some character glyphs are double width).

    :param text: The text to analyze
    :param visible_width: The required location within that text (as seen on screen).
    :return: The offset within text (as a character offset within the string).
    """
    result = 0
    width = 0
    if unicode_aware:
        for c in text:
            if visible_width - width <= 0:
                break
            result += 1
            width += wcwidth(c)
        if visible_width - width < 0:
            result -= 1
    else:
        result = min(len(text), visible_width)
    return result


def _split_text(text, width, height, unicode_aware=True):
    """
    Split text to required dimensions.

    This will first try to split the text into multiple lines, then put a "..." on the last
    3 characters of the last line if this still doesn't fit.

    :param text: The text to split.
    :param width: The maximum width for any line.
    :param height: The maximum height for the resulting text.
    :return: A list of strings of the broken up text.
    """
    tokens = text.split(" ")
    result = []
    current_line = ""
    string_len = wcswidth if unicode_aware else len
    for token in tokens:
        for i, line_token in enumerate(token.split("\n")):
            if string_len(current_line + line_token) > width or i > 0:
                result.append(current_line.rstrip())
                current_line = line_token + " "
            else:
                current_line += line_token + " "

    # Add any remaining text to the result.
    result.append(current_line.rstrip())

    # Check for a height overrun and truncate.
    if len(result) > height:
        result = result[:height]
        result[height - 1] = result[height - 1][:width - 3] + "..."

    # Very small columns could be shorter than individual words - truncate
    # each line if necessary.
    for i, line in enumerate(result):
        if len(line) > width:
            result[i] = line[:width - 3] + "..."
    return result


class Background(Effect):
    """
    Effect to be used as a Desktop background.  This sets the background to the specified
    colour.
    """

    def __init__(self, screen, bg=0, **kwargs):
        """
        :param screen: The Screen being used for the Scene.
        :param bg: Optional colour for the background.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(Background, self).__init__(screen, **kwargs)
        self._bg = bg

    def reset(self):
        pass

    def _update(self, frame_no):
        for y in range(self._screen.height):
            self._screen.print_at(" " * self._screen.width, 0, y, bg=self._bg)

    @property
    def frame_update_count(self):
        return 1000000

    @property
    def stop_frame(self):
        return self._stop_frame


class Frame(Effect):
    """
    A Frame is a special Effect for controlling and displaying Widgets.

    It is similar to a window as used in native GUI applications.  Widgets are text UI elements
    that can be used to create an interactive application within your Frame.
    """

    #: Colour palette for the widgets within the Frame.  Each entry should be
    #: a 3-tuple of (foreground colour, attribute, background colour).
    palette = {
        "background":
            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "shadow":
            (Screen.COLOUR_BLACK, None, Screen.COLOUR_BLACK),
        "disabled":
            (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "invalid":
            (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_RED),
        "label":
            (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "borders":
            (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "scroll":
            (Screen.COLOUR_CYAN, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "title":
            (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "edit_text":
            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "focus_edit_text":
            (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "button":
            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "focus_button":
            (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "control":
            (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "selected_control":
            (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "focus_control":
            (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "selected_focus_control":
            (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "field":
            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "selected_field":
            (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "focus_field":
            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "selected_focus_field":
            (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
    }

    def __init__(self, screen, height, width, data=None, on_load=None,
                 has_border=True, hover_focus=False, name=None, title=None,
                 x=None, y=None, has_shadow=False, reduce_cpu=False, is_modal=False,
                 can_scroll=True):
        """
        :param screen: The Screen that owns this Frame.
        :param width: The desired width of the Frame.
        :param height: The desired height of the Frame.
        :param data: optional data dict to initialize any widgets in the frame.
        :param on_load: optional function to call whenever the Frame reloads.
        :param has_border: Whether the frame has a border box (and scroll bar). Defaults to True.
        :param hover_focus: Whether hovering a mouse over a widget (i.e. mouse move events)
            should change the input focus.  Defaults to false.
        :param name: Optional name to identify this Frame.  This is used to reset data as needed
            from on old copy after the screen resizes.
        :param title: Optional title to display if has_border is True.
        :param x: Optional x position for the top left corner of the Frame.
        :param y: Optional y position for the top left corner of the Frame.
        :param has_shadow: Optional flag to indicate if this Frame should have a shadow when
            drawn.
        :param reduce_cpu: Whether to minimize CPU usage (for use on low spec systems).
        :param is_modal: Whether this Frame is "modal" - i.e. will stop all other Effects from
            receiving input events.
        :param can_scroll: Whether a scrollbar should be available on the border, or not.
            (Only valid if `has_border=True`).
        """
        super(Frame, self).__init__(screen)
        self._focus = 0
        self._max_height = 0
        self._layouts = []
        self._effects = []
        self._canvas = Canvas(screen, height, width, x, y)
        self._data = None
        self._on_load = on_load
        self._has_border = has_border
        self._can_scroll = can_scroll
        self._scroll_bar = _ScrollBar(
            self._canvas, self.palette, self._canvas.width - 1, 2, self._canvas.height - 4,
            self._get_pos, self._set_pos, absolute=True) if can_scroll else None
        self._hover_focus = hover_focus
        self._initial_data = data if data else {}
        self._title = None
        self.title = title  # Use property to re-format text as required.
        self._has_shadow = has_shadow
        self._reduce_cpu = reduce_cpu
        self._is_modal = is_modal
        self._has_focus = False

        # A unique name is needed for cloning.  Try our best to get one!
        self._name = title if name is None else name

        # Flag to catch recursive calls inside the data setting.  This is
        # typically caused by callbacks subsequently trying to re-use functions.
        self._in_call = False

        # Now set up any passed data - use the public property to trigger any
        # necessary updates.
        self.data = deepcopy(self._initial_data)

        # Optimization for non-unicode displays to avoid slow unicode calls.
        self.string_len = wcswidth if self._canvas.unicode_aware else len

    def _get_pos(self):
        """
        Get current position for scroll bar.
        """
        if self._canvas.height >= self._max_height:
            return 0
        else:
            return self._canvas.start_line / (self._max_height - self._canvas.height + 1)

    def _set_pos(self, pos):
        """
        Set current position for scroll bar.
        """
        if self._canvas.height < self._max_height:
            pos *= self._max_height - self._canvas.height + 1
            pos = int(round(max(0, pos), 0))
            self._canvas.scroll_to(pos)

    def add_layout(self, layout):
        """
        Add a Layout to the Frame.

        :param layout: The Layout to be added.
        """
        layout.register_frame(self)
        self._layouts.append(layout)

    def add_effect(self, effect):
        """
        Add an Effect to the Frame.

        :param effect: The Effect to be added.
        """
        effect.register_scene(self._scene)
        self._effects.append(effect)

    def fix(self):
        """
        Fix the layouts and calculate the locations of all the widgets.

        This function should be called once all Layouts have been added to the Frame and all
        widgets added to the Layouts.
        """
        # Do up to 2 passes in case we have a variable height Layout.
        fill_layout = None
        fill_height = y = 0
        for _ in range(2):
            # Pick starting point/height - varies for borders.
            if self._has_border:
                x = y = start_y = 1
                height = self._canvas.height - 2
                width = self._canvas.width - 2
            else:
                x = y = start_y = 0
                height = self._canvas.height
                width = self._canvas.width

            # Process each Layout in the Frame - getting required height for
            # each.
            for layout in self._layouts:
                if layout.fill_frame:
                    if fill_layout is None:
                        # First pass - remember it for now.
                        fill_layout = layout
                    elif fill_layout == layout:
                        # Second pass - pass in max height
                        y = layout.fix(x, y, width, fill_height)
                    else:
                        # A second filler - this is a bug in the application.
                        raise Highlander("Too many Layouts filling Frame")
                else:
                    y = layout.fix(x, y, width, height)

            # If we hit a variable height Layout - figure out the available
            # space and reset everything to the new values.
            if fill_layout is None:
                break
            else:
                fill_height = max(1, start_y + height - y)

        # Remember the resulting height of the underlying Layouts.
        self._max_height = y

        # Reset text
        while self._focus < len(self._layouts):
            try:
                self._layouts[self._focus].focus(force_first=True)
                break
            except IndexError:
                self._focus += 1
        self._clear()

    def _clear(self):
        """
        Clear the current canvas.
        """
        # It's orders of magnitude faster to reset with a print like this
        # instead of recreating the screen buffers.
        (colour, attr, bg) = self.palette["background"]
        self._canvas.clear_buffer(colour, attr, bg)

    def _update(self, frame_no):
        # TODO: Should really be in a separate Desktop Manager class - wait for v2.0
        if self.scene and self.scene.effects[-1] != self:
            if self._focus < len(self._layouts):
                self._layouts[self._focus].blur()
            self._has_focus = False

        # Reset the canvas to prepare for next round of updates.
        self._clear()

        # Update all the widgets first.
        for layout in self._layouts:
            layout.update(frame_no)

        # Then update any effects as needed.
        for effect in self._effects:
            effect.update(frame_no)

        # Draw any border if needed.
        if self._has_border:
            # Decide on box chars to use.
            tl = u"┌" if self._canvas.unicode_aware else "+"
            tr = u"┐" if self._canvas.unicode_aware else "+"
            bl = u"└" if self._canvas.unicode_aware else "+"
            br = u"┘" if self._canvas.unicode_aware else "+"
            horiz = u"─" if self._canvas.unicode_aware else "-"
            vert = u"│" if self._canvas.unicode_aware else "|"

            # Draw the basic border first.
            (colour, attr, bg) = self.palette["borders"]
            for dy in range(self._canvas.height):
                y = self._canvas.start_line + dy
                if dy == 0:
                    self._canvas.print_at(
                        tl + (horiz * (self._canvas.width - 2)) + tr,
                        0, y, colour, attr, bg)
                elif dy == self._canvas.height - 1:
                    self._canvas.print_at(
                        bl + (horiz * (self._canvas.width - 2)) + br,
                        0, y, colour, attr, bg)
                else:
                    self._canvas.print_at(vert, 0, y, colour, attr, bg)
                    self._canvas.print_at(vert, self._canvas.width - 1, y,
                                          colour, attr, bg)

            # Now the title
            (colour, attr, bg) = self.palette["title"]
            title_width = self.string_len(self._title)
            self._canvas.print_at(
                self._title,
                (self._canvas.width - title_width) // 2,
                self._canvas.start_line,
                colour, attr, bg)

            # And now the scroll bar
            if self._can_scroll and self._canvas.height > 5:
                self._scroll_bar.update()

        # Now push it all to screen.
        self._canvas.refresh()

        # And finally - draw the shadow
        if self._has_shadow:
            (colour, _, bg) = self.palette["shadow"]
            self._screen.highlight(
                self._canvas.origin[0] + 1,
                self._canvas.origin[1] + self._canvas.height,
                self._canvas.width - 1,
                1,
                fg=colour, bg=bg, blend=50)
            self._screen.highlight(
                self._canvas.origin[0] + self._canvas.width,
                self._canvas.origin[1] + 1,
                1,
                self._canvas.height,
                fg=colour, bg=bg, blend=50)

    def set_theme(self, theme):
        """
        Pick a palette from the list of supported THEMES.

        :param theme: The name of the theme to set.
        """
        if theme in _THEMES:
            self.palette = _THEMES[theme]
            if self._scroll_bar:
                # TODO: fix protected access.
                self._scroll_bar._palette = self.palette

    @property
    def title(self):
        """
        Title for this Frame.
        """
        return self._title

    @title.setter
    def title(self, new_value):
        self._title = " " + new_value[0:self._canvas.width - 4] + " " if new_value else ""

    @property
    def data(self):
        """
        Data dictionary containing values from the contained widgets.
        """
        return self._data

    @data.setter
    def data(self, new_value):
        # Don't allow this function to recurse.
        if self._in_call:
            return
        self._in_call = True

        # Do a key-by-key copy to allow for dictionary-like objects - e.g.
        # sqlite3 Row class.
        self._data = {}
        if new_value is not None:
            for key in list(new_value.keys()):
                self._data[key] = new_value[key]

        # Now update any widgets as needed.
        for layout in self._layouts:
            layout.update_widgets()

        # All done - clear the recursion flag.
        self._in_call = False

    @property
    def stop_frame(self):
        # Widgets have no defined end - always return -1.
        return -1

    @property
    def safe_to_default_unhandled_input(self):
        # It is NOT safe to use the unhandled input handler on Frames as the
        # default on space and enter is to go to the next Scene.
        return False

    @property
    def canvas(self):
        """
        The Canvas that backs this Frame.
        """
        return self._canvas

    @property
    def focussed_widget(self):
        """
        The widget that currently has the focus within this Frame.
        """
        # If the frame has no focus, it can't have a focussed widget.
        if not self._has_focus:
            return None

        try:
            layout = self._layouts[self._focus]
            return layout._columns[layout._live_col][layout._live_widget]
        except IndexError:
            # If the current indexing is invalid it's because no widget is selected.
            return None

    @property
    def frame_update_count(self):
        """
        The number of frames before this Effect should be updated.
        """
        result = 1000000
        for layout in self._layouts:
            if layout.frame_update_count > 0:
                result = min(result, layout.frame_update_count)
        for effect in self._effects:
            if effect.frame_update_count > 0:
                result = min(result, effect.frame_update_count)
        return result

    @property
    def reduce_cpu(self):
        """
        Whether this Frame should try to optimize refreshes to reduce CPU.
        """
        return self._reduce_cpu

    def find_widget(self, name):
        """
        Look for a widget with a specified name.

        :param name: The name to search for.

        :returns: The widget that matches or None if one couldn't be found.
        """
        result = None
        for layout in self._layouts:
            result = layout.find_widget(name)
            if result:
                break
        return result

    def clone(self, _, scene):
        """
        Create a clone of this Frame into a new Screen.

        :param _: ignored.
        :param scene: The new Scene object to clone into.
        """
        # Assume that the application creates a new set of Frames and so we need to match up the
        # data from the old object to the new (using the name).
        if self._name is not None:
            for effect in scene.effects:
                if isinstance(effect, Frame):
                    if effect._name == self._name:
                        effect.data = self.data
                        for layout in self._layouts:
                            layout.update_widgets(new_frame=effect)

    def reset(self):
        # Reset form to default state.
        self.data = deepcopy(self._initial_data)

        # Now reset the individual widgets.
        self._canvas.reset()
        for layout in self._layouts:
            layout.reset()
            layout.blur()

        # Then reset any effects as needed.
        for effect in self._effects:
            effect.reset()

        # Set up active widget.
        self._focus = 0
        while self._focus < len(self._layouts):
            try:
                self._layouts[self._focus].focus(force_first=True)
                break
            except IndexError:
                self._focus += 1

        # Call the on_load function now if specified.
        if self._on_load is not None:
            self._on_load()

    def save(self, validate=False):
        """
        Save the current values in all the widgets back to the persistent data storage.

        :param validate: Whether to validate the data before saving.

        Calling this while setting the `data` field (e.g. in a widget callback) will have no
        effect.

        When validating data, it can throw an Exception for any
        """
        # Don't allow this function to be called if we are already updating the
        # data for the form.
        if self._in_call:
            return

        # We're clear - pass on to all layouts/widgets.
        invalid = []
        for layout in self._layouts:
            try:
                layout.save(validate=validate)
            except InvalidFields as exc:
                invalid.extend(exc.fields)

        # Check for any bad data and raise exception if needed.
        if len(invalid) > 0:
            raise InvalidFields(invalid)

    def switch_focus(self, layout, column, widget):
        """
        Switch focus to the specified widget.

        :param layout: The layout that owns the widget.
        :param column: The column the widget is in.
        :param widget: The index of the widget to take the focus.
        """
        # Find the layout to own the focus.
        for i, l in enumerate(self._layouts):
            if l is layout:
                break
        else:
            # No matching layout - give up now
            return

        self._layouts[self._focus].blur()
        self._focus = i
        self._layouts[self._focus].focus(force_column=column,
                                         force_widget=widget)

    def move_to(self, x, y, h):
        """
        Make the specified location visible.  This is typically used by a widget to scroll the
        canvas such that it is visible.

        :param x: The x location to make visible.
        :param y: The y location to make visible.
        :param h: The height of the location to make visible.
        """
        if self._has_border:
            start_x = 1
            width = self.canvas.width - 2
            start_y = self.canvas.start_line + 1
            height = self.canvas.height - 2
        else:
            start_x = 0
            width = self.canvas.width
            start_y = self.canvas.start_line
            height = self.canvas.height

        if ((x >= start_x) and (x < start_x + width) and
                (y >= start_y) and (y + h < start_y + height)):
            # Already OK - quit now.
            return

        if y < start_y:
            self.canvas.scroll_to(y - 1 if self._has_border else y)
        else:
            line = y + h - self.canvas.height + (1 if self._has_border else 0)
            self.canvas.scroll_to(max(0, line))

    def rebase_event(self, event):
        """
        Rebase the coordinates of the passed event to frame-relative coordinates.

        :param event: The event to be rebased.
        :returns: A new event object appropriately re-based.
        """
        new_event = copy(event)
        if isinstance(new_event, MouseEvent):
            origin = self._canvas.origin
            new_event.x -= origin[0]
            new_event.y -= origin[1] - self._canvas.start_line
        logger.debug("New event: %s", new_event)
        return new_event

    def process_event(self, event):
        # Rebase any mouse events into Frame coordinates now.
        old_event = event
        event = self.rebase_event(event)

        # Claim the input focus if a mouse clicked on this Frame.
        claimed_focus = False
        if isinstance(event, MouseEvent) and event.buttons > 0:
            if (0 <= event.x < self._canvas.width and
                    0 <= event.y < self._canvas.height):
                self._scene.remove_effect(self)
                self._scene.add_effect(self, reset=False)
                if not self._has_focus and self._focus < len(self._layouts):
                    self._layouts[self._focus].focus()
                self._has_focus = claimed_focus = True
            else:
                if self._has_focus and self._focus < len(self._layouts):
                    self._layouts[self._focus].blur()
                self._has_focus = False
        elif isinstance(event, KeyboardEvent):
            # TODO: Should have Desktop Manager handling this - wait for v2.0
            # By this stage, if we're processing keys, we have the focus.
            if not self._has_focus and self._focus < len(self._layouts):
                self._layouts[self._focus].focus()
            self._has_focus = True

        # No need to do anything if this Frame has no Layouts - and hence no
        # widgets.  Swallow all Keyboard events while we have focus.
        #
        # Also don't bother trying to process widgets if there is no defined
        # focus.  This means there is no enabled widget in the Frame.
        if (self._focus < 0 or self._focus >= len(self._layouts) or
                not self._layouts):
            if event is not None and isinstance(event, KeyboardEvent):
                return None
            else:
                # Don't allow events to bubble down if this window owns the Screen - as already
                # calculated when taking te focus - or is modal.
                return None if claimed_focus or self._is_modal else old_event

        # Give the current widget in focus first chance to process the event.
        event = self._layouts[self._focus].process_event(event, self._hover_focus)

        # If the underlying widgets did not process the event, try processing
        # it now.
        if event is not None:
            if isinstance(event, KeyboardEvent):
                if event.key_code in [Screen.KEY_TAB, Screen.KEY_DOWN]:
                    # Move on to next widget.
                    self._layouts[self._focus].blur()
                    old_focus = self._focus
                    self._focus += 1
                    while self._focus != old_focus:
                        try:
                            self._layouts[self._focus].focus(force_first=True)
                            break
                        except IndexError:
                            self._focus += 1
                            if self._focus >= len(self._layouts):
                                self._focus = 0
                    self._layouts[self._focus].focus(force_first=True)
                    old_event = None
                elif event.key_code in [Screen.KEY_BACK_TAB, Screen.KEY_UP]:
                    # Move on to previous widget.
                    self._layouts[self._focus].blur()
                    old_focus = self._focus
                    self._focus -= 1
                    while self._focus != old_focus:
                        if self._focus < 0:
                            self._focus = len(self._layouts) - 1
                        try:
                            self._layouts[self._focus].focus(force_last=True)
                            break
                        except IndexError:
                            self._focus -= 1
                    self._layouts[self._focus].focus(force_last=True)
                    old_event = None
            elif isinstance(event, MouseEvent):
                # Give layouts/widgets first dibs on the mouse message.
                for layout in self._layouts:
                    if layout.process_event(event, self._hover_focus) is None:
                        return None

                # If no joy, check whether the scroll bar was clicked.
                if self._has_border and self._can_scroll:
                    if self._scroll_bar.process_event(event):
                        return None

        # Don't allow events to bubble down if this window owns the Screen (as already
        # calculated when taking te focus) or if the Frame is modal.
        return None if claimed_focus or self._is_modal else old_event


class Layout(object):
    """
    Widget layout handler.

    All Widgets must be contained within a Layout within a Frame.The Layout class is responsible
    for deciding the exact size and location of the widgets.  The logic uses similar ideas as
    used in modern web frameworks and is as follows.

    1.  The Frame owns one or more Layouts.  The Layouts stack one above each other when
        displayed - i.e. the first Layout in the Frame is above the second, etc.
    2.  Each Layout defines the horizontal constraints by defining columns as a percentage of the
        full canvas width.
    3.  The Widgets are assigned a column within the Layout that owns them.
    4.  The Layout then decides the exact size and location to make the
        Widget best fit the canvas as constrained by the above.
    """

    def __init__(self, columns, fill_frame=False):
        """
        :param columns: A list of numbers specifying the width of each column in this layout.
        :param fill_frame: Whether this Layout should attempt to fill the rest of the Frame.
            Defaults to False.

        The Layout will automatically normalize the units used for the columns, e.g. converting
        [2, 6, 2] to [20%, 60%, 20%] of the available canvas.
        """
        total_size = sum(columns)
        self._column_sizes = [x / total_size for x in columns]
        self._columns = [[] for _ in columns]
        self._frame = None
        self._has_focus = False
        self._live_col = 0
        self._live_widget = -1
        self._fill_frame = fill_frame

    @property
    def fill_frame(self):
        """
        Whether this Layout is variable height or not.
        """
        return self._fill_frame

    @property
    def frame_update_count(self):
        """
        The number of frames before this Layout should be updated.
        """
        result = 1000000
        for column in self._columns:
            for widget in column:
                if widget.frame_update_count > 0:
                    result = min(result, widget.frame_update_count)
        return result

    def register_frame(self, frame):
        """
        Register the Frame that owns this Widget.

        :param frame: The owning Frame.
        """
        self._frame = frame
        for column in self._columns:
            for widget in column:
                widget.register_frame(self._frame)

    def add_widget(self, widget, column=0):
        """
        Add a widget to this Layout.

        :param widget: The widget to be added.
        :param column: The column within the widget for this widget.  Defaults to zero.
        """
        # Make sure that the Layout is fully initialised before we try to add any widgets.
        if self._frame is None:
            raise RuntimeError("You must add the Layout to the Frame before you can add a Widget.")

        # Now process the widget.
        self._columns[column].append(widget)
        widget.register_frame(self._frame)

        if widget.name in self._frame.data:
            widget.value = self._frame.data[widget.name]

    def focus(self, force_first=False, force_last=False, force_column=None,
              force_widget=None):
        """
        Call this to give this Layout the input focus.

        :param force_first: Optional parameter to force focus to first widget.
        :param force_last: Optional parameter to force focus to last widget.
        :param force_column: Optional parameter to mandate the new column index.
        :param force_widget: Optional parameter to mandate the new widget index.

        The force_column and force_widget parameters must both be set together or they will
        otherwise be ignored.

        :raises IndexError: if a force option specifies a bad column or widget, or if the whole
            Layout is readonly.
        """
        self._has_focus = True
        if force_widget is not None and force_column is not None:
            self._live_col = force_column
            self._live_widget = force_widget
        elif force_first:
            self._live_col = 0
            self._live_widget = -1
            self._find_next_widget(1)
        elif force_last:
            self._live_col = len(self._columns) - 1
            self._live_widget = len(self._columns[self._live_col])
            self._find_next_widget(-1)
        self._columns[self._live_col][self._live_widget].focus()

    def blur(self):
        """
        Call this to take the input focus from this Layout.
        """
        self._has_focus = False
        try:
            self._columns[self._live_col][self._live_widget].blur()
        except IndexError:
            # don't worry if there are no active widgets in the Layout
            pass

    def fix(self, start_x, start_y, max_width, max_height):
        """
        Fix the location and size of all the Widgets in this Layout.

        :param start_x: The start column for the Layout.
        :param start_y: The start line for the Layout.
        :param max_width: Max width to allow this layout.
        :param max_height: Max height to allow this layout.
        :returns: The next line to be used for any further Layouts.
        """
        x = start_x
        width = max_width
        y = w = 0
        max_y = start_y
        string_len = wcswidth if self._frame.canvas.unicode_aware else len
        dimensions = []
        for i, column in enumerate(self._columns):
            # For each column determine if we need a tab offset for labels.
            # Only allow labels to take up 1/3 of the column.
            if len(column) > 0:
                offset = max([0 if c.label is None else string_len(c.label) + 1 for c in column])
            else:
                offset = 0
            offset = int(min(offset,
                         width * self._column_sizes[i] // 3))

            # Start tracking new column
            dimensions.append(_DotDict())
            dimensions[i].parameters = []
            dimensions[i].offset = offset

            # Do first pass to figure out the gaps for widgets that want to fill remaining space.
            fill_layout = None
            fill_column = None
            y = start_y
            w = int(width * self._column_sizes[i])
            for widget in column:
                h = widget.required_height(offset, w)
                if h == Widget.FILL_FRAME:
                    if fill_layout is None and fill_column is None:
                        dimensions[i].parameters.append([widget, x, w, h])
                        fill_layout = widget
                    else:
                        # Two filling widgets in one column - this is a bug.
                        raise Highlander("Too many Widgets filling Layout")
                elif h == Widget.FILL_COLUMN:
                    if fill_layout is None and fill_column is None:
                        dimensions[i].parameters.append([widget, x, w, h])
                        fill_column = widget
                    else:
                        # Two filling widgets in one column - this is a bug.
                        raise Highlander("Too many Widgets filling Layout")
                else:
                    dimensions[i].parameters.append([widget, x, w, h])
                    y += h

            # Note space used by this column.
            dimensions[i].height = y

            # Update tracking variables fpr the next column.
            max_y = max(max_y, y)
            x += w

        # Finally check whether the Layout is allowed to expand.
        if self.fill_frame:
            max_y = max(max_y, start_y + max_height)

        # Now apply calculated sizes, updating any widgets that need to fill space.
        for column in dimensions:
            y = start_y
            for widget, x, w, h in column.parameters:
                if h == Widget.FILL_FRAME:
                    h = max(1, start_y + max_height - column.height)
                elif h == Widget.FILL_COLUMN:
                    h = max_y - column.height
                widget.set_layout(x, y, column.offset, w, h)
                y += h

        return max_y

    def _find_next_widget(self, direction, stay_in_col=False, start_at=None,
                          wrap=False):
        """
        Find the next widget to get the focus, stopping at the start/end of the list if hit.

        :param direction: The direction to move through the widgets.
        :param stay_in_col: Whether to limit search to current column.
        :param start_at: Optional starting point in current column.
        :param wrap: Whether to wrap around columns when at the end.
        """
        current_widget = self._live_widget
        current_col = self._live_col
        if start_at is not None:
            self._live_widget = start_at
        still_looking = True
        while still_looking:
            while 0 <= self._live_col < len(self._columns):
                self._live_widget += direction
                while 0 <= self._live_widget < len(
                        self._columns[self._live_col]):
                    widget = self._columns[self._live_col][self._live_widget]
                    if widget.is_tab_stop and not widget.disabled:
                        return
                    self._live_widget += direction
                if stay_in_col:
                    # Don't move to another column - just stay where we are.
                    self._live_widget = current_widget
                    break
                else:
                    self._live_col += direction
                    self._live_widget = -1 if direction > 0 else \
                        len(self._columns[self._live_col])
                    if self._live_col == current_col:
                        # We've wrapped all the way back to the same column -
                        # give up now and stay where we were.
                        self._live_widget = current_widget
                        return

            # If we got here we hit the end of the columns - only keep on
            # looking if we're allowed to wrap.
            still_looking = wrap
            if still_looking:
                if self._live_col < 0:
                    self._live_col = len(self._columns) - 1
                else:
                    self._live_col = 0

    def process_event(self, event, hover_focus):
        """
        Process any input event.

        :param event: The event that was triggered.
        :param hover_focus: Whether to trigger focus change on mouse moves.
        :returns: None if the Effect processed the event, else the original event.
        """
        # Check whether this Layout is read-only - i.e. has no active focus.
        if self._live_col < 0 or self._live_widget < 0:
            # Might just be that we've unset the focus - so check we can't find a focus.
            self._find_next_widget(1)
            if self._live_col < 0 or self._live_widget < 0:
                return event

        # Give the active widget the first refusal for this event.
        event = self._columns[
            self._live_col][self._live_widget].process_event(event)

        # Check for any movement keys if the widget refused them.
        if event is not None:
            if isinstance(event, KeyboardEvent):
                if event.key_code == Screen.KEY_TAB:
                    # Move on to next widget, unless it is the last in the
                    # Layout.
                    self._columns[self._live_col][self._live_widget].blur()
                    self._find_next_widget(1)
                    if self._live_col >= len(self._columns):
                        self._live_col = 0
                        self._live_widget = -1
                        self._find_next_widget(1)
                        return event

                    # If we got here, we still should have the focus.
                    self._columns[self._live_col][self._live_widget].focus()
                    event = None
                elif event.key_code == Screen.KEY_BACK_TAB:
                    # Move on to previous widget, unless it is the first in the
                    # Layout.
                    self._columns[self._live_col][self._live_widget].blur()
                    self._find_next_widget(-1)
                    if self._live_col < 0:
                        self._live_col = len(self._columns) - 1
                        self._live_widget = len(self._columns[self._live_col])
                        self._find_next_widget(-1)
                        return event

                    # If we got here, we still should have the focus.
                    self._columns[self._live_col][self._live_widget].focus()
                    event = None
                elif event.key_code == Screen.KEY_DOWN:
                    # Move on to next widget in this column
                    wid = self._live_widget
                    self._columns[self._live_col][self._live_widget].blur()
                    self._find_next_widget(1, stay_in_col=True)
                    self._columns[self._live_col][self._live_widget].focus()
                    # Don't swallow the event if it had no effect.
                    event = event if wid == self._live_widget else None
                elif event.key_code == Screen.KEY_UP:
                    # Move on to previous widget, unless it is the first in the
                    # Layout.
                    wid = self._live_widget
                    self._columns[self._live_col][self._live_widget].blur()
                    self._find_next_widget(-1, stay_in_col=True)
                    self._columns[self._live_col][self._live_widget].focus()
                    # Don't swallow the event if it had no effect.
                    event = event if wid == self._live_widget else None
                elif event.key_code == Screen.KEY_LEFT:
                    # Move on to last widget in the previous column
                    self._columns[self._live_col][self._live_widget].blur()
                    self._find_next_widget(-1, start_at=0, wrap=True)
                    self._columns[self._live_col][self._live_widget].focus()
                    event = None
                elif event.key_code == Screen.KEY_RIGHT:
                    # Move on to first widget in the next column.
                    self._columns[self._live_col][self._live_widget].blur()
                    self._find_next_widget(
                        1,
                        start_at=len(self._columns[self._live_col]),
                        wrap=True)
                    self._columns[self._live_col][self._live_widget].focus()
                    event = None
            elif isinstance(event, MouseEvent):
                logger.debug("Check layout: %d, %d", event.x, event.y)
                if ((hover_focus and event.buttons >= 0) or
                        event.buttons > 0):
                    # Mouse click - look to move focus.
                    for i, column in enumerate(self._columns):
                        for j, widget in enumerate(column):
                            if widget.is_mouse_over(event):
                                self._frame.switch_focus(self, i, j)
                                widget.process_event(event)
                                return None
        return event

    def update(self, frame_no):
        """
        Redraw the widgets inside this Layout.

        :param frame_no: The current frame to be drawn.
        """
        for column in self._columns:
            for widget in column:
                widget.update(frame_no)

    def save(self, validate):
        """
        Save the current values in all the widgets back to the persistent data storage.

        :param validate: whether to validate the saved data or not.
        :raises: InvalidFields if any invalid data is found.
        """
        invalid = []
        for column in self._columns:
            for widget in column:
                if widget.is_valid or not validate:
                    if widget.name is not None:
                        # This relies on the fact that we are passed the actual
                        # dict and so can edit it directly.  In this case, that
                        # is all we want - no need to update the widgets.
                        self._frame._data[widget.name] = widget.value
                else:
                    invalid.append(widget.name)
        if len(invalid) > 0:
            raise InvalidFields(invalid)

    def find_widget(self, name):
        """
        Look for a widget with a specified name.

        :param name: The name to search for.

        :returns: The widget that matches or None if one couldn't be found.
        """
        result = None
        for column in self._columns:
            for widget in column:
                if widget.name is not None and name == widget.name:
                    result = widget
                    break
        return result

    def update_widgets(self, new_frame=None):
        """
        Reset the values for any Widgets in this Layout based on the current Frame data store.

        :param new_frame: optional old Frame - used when cloning scenes.
        """
        for column in self._columns:
            for widget in column:
                # First handle the normal case - pull the default data from the current frame.
                if widget.name in self._frame.data:
                    widget.value = self._frame.data[widget.name]
                elif widget.is_tab_stop:
                    # Make sure every active widget is properly initialised, by calling the setter.
                    # This will fix up any dodgy NoneType values, but preserve any values overridden
                    # by other code.
                    widget.value = widget.value

                # If an old frame was present, give the widget a chance to clone internal state
                # from the previous view.  If there is no clone function, ignore the error.
                if new_frame:
                    try:
                        widget.clone(new_frame.find_widget(widget.name))
                    except AttributeError:
                        pass

    def reset(self):
        """
        Reset this Layout and the Widgets it contains.
        """
        # Ensure that the widgets are using the right values.
        self.update_widgets()

        # Reset all the widgets.
        for column in self._columns:
            for widget in column:
                widget.reset()
                widget.blur()

        # Find the focus for the first widget
        self._live_widget = -1
        self._find_next_widget(1)


class Widget(with_metaclass(ABCMeta, object)):
    """
    A Widget is a re-usable component that can be used to create a simple GUI.
    """

    #: Widgets with this constant for the required height will be re-sized to
    #: fit the available vertical space in the Layout.
    FILL_FRAME = -135792468

    #: Widgets with this constant for the required height will be re-sized to
    #: fit the maximum space used by any other column in the Layout.
    FILL_COLUMN = -135792467

    def __init__(self, name, tab_stop=True, on_focus=None, on_blur=None):
        """
        :param name: The name of this Widget.
        :param tab_stop: Whether this widget should take focus or not when tabbing around the
            Frame.
        :param on_focus: Optional callback whenever this widget gets the focus.
        :param on_blur: Optional callback whenever this widget loses the focus.
        """
        super(Widget, self).__init__()
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
        self._is_disabled = False
        self._is_valid = True
        self._custom_colour = None
        self._on_focus = on_focus
        self._on_blur = on_blur

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
        self._has_focus = True
        self._frame.move_to(self._x, self._y, self._h)
        if self._on_focus is not None:
            self._on_focus()

    def is_mouse_over(self, event, include_label=True, width_modifier=0):
        """
        Check if the specified mouse event is over this widget.

        :param event: The MouseEvent to check.
        :param include_label: Include space reserved for the label when checking.
        :param width_modifier: Adjustement to width (e.g. for scroll bars).
        :returns: True if the mouse is over the active parts of the widget.
        """
        # Disabled widgets should not react to the mouse.
        logger.debug("Widget: %s (%d, %d) (%d, %d)", self, self._x, self._y, self._w, self._h)
        if self._is_disabled:
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
            (colour, attr, bg) = self._frame.palette["label"]
            for i, text in enumerate(self._display_label):
                self._frame.canvas.paint(
                    text, self._x, self._y + i, colour, attr, bg)

    def _draw_cursor(self, char, frame_no, x, y):
        """
        Draw a flashing cursor for this widget.

        :param char: The character to use for the cursor (when not a block)
        :param frame_no: The current frame number.
        :param x: The x coordinate for the cursor.
        :param y: The y coordinate for the cursor.
        """
        (colour, attr, bg) = self._pick_colours("edit_text")
        if frame_no % 10 < 5 or self._frame.reduce_cpu:
            attr |= Screen.A_REVERSE
        self._frame.canvas.print_at(char, x, y, colour, attr, bg)

    def _pick_colours(self, palette_name, selected=False):
        """
        Pick the rendering colour for a widget based on the current state.

        :param palette_name: The stem name for the widget - e.g. "button".
        :param selected: Whether this item is selected or not.
        :returns: A colour tuple (fg, attr, bg) to be used.
        """
        if self._custom_colour:
            key = self._custom_colour
        elif self.disabled:
            key = "disabled"
        elif not self._is_valid:
            key = "invalid"
        else:
            if self._has_focus:
                key = "focus_" + palette_name
            else:
                key = palette_name
            if selected:
                key = "selected_" + key
        return self._frame.palette[key]

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

    # I need an abstract writable property - which bizarrely needs functions
    # to be declared.  Use None for all of them to force errors if called.

    #: The value to return for this widget based on the user's input.
    value = abstractproperty(
        None,
        None,
        None,
        "The value to return for this widget based on the user's input.")

    @abstractmethod
    def required_height(self, offset, width):
        """
        Calculate the minimum required height for this widget.

        :param offset: The allowed width for any labels.
        :param width: The total width of the widget, including labels.
        """


class Label(Widget):
    """
    A text label.
    """

    def __init__(self, label, height=1, align="<"):
        """
        :param label: The text to be displayed for the Label.
        :param height: Optional height for the label.  Defaults to 1 line.
        :param align: Optional alignment for the Label.  Defaults to left aligned.
            Options are "<" = left, ">" = right and "^" = centre

        """
        # Labels have no value and so should have no name for look-ups either.
        super(Label, self).__init__(None, tab_stop=False)
        # Although this is a label, we don't want it to contribute to the layout
        # tab calculations, so leave internal `_label` value as None.
        self._text = label
        self._required_height = height
        self._align = align

    def process_event(self, event):
        # Labels have no user interactions
        return event

    def update(self, frame_no):
        (colour, attr, bg) = self._frame.palette["label"]
        for i, text in enumerate(
                _split_text(self._text, self._w, self._h, self._frame.canvas.unicode_aware)):
            self._frame.canvas.paint(
                "{:{}{}}".format(text, self._align, self._w), self._x, self._y + i, colour, attr, bg)

    def reset(self):
        pass

    def required_height(self, offset, width):
        # Allow one line for text and a blank spacer before it.
        return self._required_height

    @property
    def text(self):
        """
        The current text for this Label.
        """
        return self._text

    @text.setter
    def text(self, new_value):
        self._text = new_value

    @property
    def value(self):
        return self._value


class Divider(Widget):
    """
    A divider to break up a group of widgets.
    """

    def __init__(self, draw_line=True, height=1, line_char=None):
        """
        :param draw_line: Whether to draw a line in the centre of the gap.
        :param height: The required vertical gap.
        :param line_char: Optional character to use for drawing the line.
        """
        # Dividers have no value and so should have no name for look-ups either.
        super(Divider, self).__init__(None, tab_stop=False)
        self._draw_line = draw_line
        self._required_height = height
        self._line_char = line_char

    def register_frame(self, frame):
        # Update line drawing character if needed once we have a canvas to query.
        super(Divider, self).register_frame(frame)
        if self._line_char is None:
            self._line_char = u"─" if self._frame.canvas.unicode_aware else "-"

    def process_event(self, event):
        # Dividers have no user interactions
        return event

    def update(self, frame_no):
        (colour, attr, bg) = self._frame.palette["borders"]
        if self._draw_line:
            self._frame.canvas.print_at(self._line_char * self._w,
                                        self._x,
                                        self._y + (self._h // 2),
                                        colour, attr, bg)

    def reset(self):
        pass

    def required_height(self, offset, width):
        return self._required_height

    @property
    def value(self):
        return self._value


class Text(Widget):
    """
    A Text widget is a single line input field.

    It consists of an optional label and an entry box.
    """

    def __init__(self, label=None, name=None, on_change=None, validator=None, hide_char=None,
                 **kwargs):
        """
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        :param on_change: Optional function to call when text changes.
        :param validator: Optional definition of valid data for this widget.
            This can be a function (which takes the current value and returns True for valid
            content) or a regex string (which must match the entire allowed value).
        :param hide_char: Character to use instead of what the user types - e.g. to hide passwords.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super(Text, self).__init__(name, **kwargs)
        self._label = label
        self._column = 0
        self._start_column = 0
        self._on_change = on_change
        self._validator = validator
        self._hide_char = hide_char

    def update(self, frame_no):
        self._draw_label()

        # Calculate new visible limits if needed.
        self._start_column = min(self._start_column, self._column)
        self._start_column += _find_min_start(self._value[self._start_column:self._column + 1],
                                              self.width, self._frame.canvas.unicode_aware,
                                              self._column >= self.string_len(self._value))

        # Render visible portion of the text.
        (colour, attr, bg) = self._pick_colours("edit_text")
        text = self._value[self._start_column:]
        text = _enforce_width(text, self.width, self._frame.canvas.unicode_aware)
        if self._hide_char:
            text = self._hide_char[0] * len(text)
        text += " " * (self.width - self.string_len(text))
        self._frame.canvas.print_at(
            text,
            self._x + self._offset,
            self._y,
            colour, attr, bg)

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
        self._column = len(self._value)

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code == Screen.KEY_BACK:
                if self._column > 0:
                    # Delete character in front of cursor.
                    self._set_and_check_value("".join([self._value[:self._column - 1],
                                                       self._value[self._column:]]))
                    self._column -= 1
            if event.key_code == Screen.KEY_DELETE:
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
            elif event.key_code >= 32:
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
    def value(self):
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
                self._is_valid = re.match(self._validator,
                                          self._value) is not None


class CheckBox(Widget):
    """
    A CheckBox widget is used to ask for Boolean (i.e. yes/no) input.

    It consists of an optional label (typically used for the first in a group of CheckBoxes),
    the box and a field name.
    """

    def __init__(self, text, label=None, name=None, on_change=None, **kwargs):
        """
        :param text: The text to explain this specific field to the user.
        :param label: An optional label for the widget.
        :param name: The internal name for the widget.
        :param on_change: Optional function to call when text changes.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super(CheckBox, self).__init__(name, **kwargs)
        self._text = text
        self._label = label
        self._on_change = on_change

    def update(self, frame_no):
        self._draw_label()

        # Render this checkbox.
        check_char = u"✓" if self._frame.canvas.unicode_aware else "X"
        (colour, attr, bg) = self._pick_colours("control", self._has_focus)
        self._frame.canvas.print_at(
            "[{}] ".format(check_char if self._value else " "),
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
        return self._value

    @value.setter
    def value(self, new_value):
        # Only trigger the notification after we've changed the value.
        old_value = self._value
        self._value = new_value if new_value else False
        if old_value != self._value and self._on_change:
            self._on_change()


class RadioButtons(Widget):
    """
    A RadioButtons widget is used to ask for one of a list of values to be selected by the user.

    It consists of an optional label and then a list of selection bullets with field names.
    """

    def __init__(self, options, label=None, name=None, on_change=None, **kwargs):
        """
        :param options: A list of (text, value) tuples for each radio button.
        :param label: An optional label for the widget.
        :param name: The internal name for the widget.
        :param on_change: Optional function to call when text changes.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super(RadioButtons, self).__init__(name, **kwargs)
        self._options = options
        self._label = label
        self._selection = 0
        self._start_column = 0
        self._on_change = on_change

    def update(self, frame_no):
        self._draw_label()

        # Decide on check char
        check_char = u"•" if self._frame.canvas.unicode_aware else "X"

        # Render the list of radio buttons.
        for i, (text, _) in enumerate(self._options):
            fg, attr, bg = self._pick_colours("control", self._has_focus and i == self._selection)
            fg2, attr2, bg2 = self._pick_colours("field", self._has_focus and i == self._selection)
            check = check_char if i == self._selection else " "
            self._frame.canvas.print_at(
                "({}) ".format(check),
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
        # The value is actually the value of the current selection.
        return self._options[self._selection][1]

    @value.setter
    def value(self, new_value):
        # Only trigger the notification after we've changed the value.
        old_value = self._value
        self._value = new_value
        for i, (_, value) in enumerate(self._options):
            if new_value == value:
                self._selection = i
                break
        else:
            self._selection = 0
        self._value = new_value if new_value else None
        if old_value != self._value and self._on_change:
            self._on_change()


class TextBox(Widget):
    """
    A TextBox is a widget for multi-line text editing.

    It consists of a framed box with option label.
    """

    def __init__(self, height, label=None, name=None, as_string=False, line_wrap=False,
                 on_change=None, **kwargs):
        """
        :param height: The required number of input lines for this TextBox.
        :param label: An optional label for the widget.
        :param name: The name for the TextBox.
        :param as_string: Use string with newline separator instead of a list
            for the value of this widget.
        :param line_wrap: Whether to wrap at the end of the line.
        :param on_change: Optional function to call when text changes.

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
        self._on_change = on_change
        self._reflowed_text_cache = None

    def update(self, frame_no):
        self._draw_label()

        # Calculate new visible limits if needed.
        height = self._h
        dx = dy = 0
        if not self._line_wrap:
            self._start_column = min(self._start_column, self._column)
            self._start_column += _find_min_start(
                self._value[self._line][self._start_column:self._column + 1],
                self.width,
                self._frame.canvas.unicode_aware,
                self._column >= self.string_len(self._value[self._line]))

        # Clear out the existing box content
        (colour, attr, bg) = self._pick_colours("edit_text")
        for i in range(height):
            self._frame.canvas.print_at(
                " " * self.width,
                self._x + self._offset + dx,
                self._y + i + dy,
                colour, attr, bg)

        # Convert value offset to display offsets
        # NOTE: _start_column is always in display coordinates.
        display_text = self._reflowed_text
        display_start_column = self._start_column
        display_line, display_column = 0, 0
        for i, (_, line, col) in enumerate(display_text):
            if line <= self._line and col <= self._column:
                display_line = i
                display_column = self._column - col

        # Restrict to visible/valid content.
        self._start_line = max(0, max(display_line - height + 1,
                                      min(self._start_line, display_line)))

        # Render visible portion of the text.
        for line, (text, _, _) in enumerate(display_text):
            if self._start_line <= line < self._start_line + height:
                self._frame.canvas.print_at(
                    _enforce_width(text[display_start_column:], self.width,
                                   self._frame.canvas.unicode_aware),
                    self._x + self._offset + dx,
                    self._y + line + dy - self._start_line,
                    colour, attr, bg)

        # Since we switch off the standard cursor, we need to emulate our own
        # if we have the input focus.
        if self._has_focus:
            line = display_text[display_line][0]
            text_width = self.string_len(line[display_start_column:display_column])
            self._draw_cursor(
                " " if display_column >= len(line) else line[display_column],
                frame_no,
                self._x + self._offset + dx + text_width,
                self._y + display_line + dy - self._start_line)

    def reset(self):
        # Reset to original data and move to end of the text.
        self._line = len(self._value) - 1
        self._column = len(self._value[self._line])
        self._reflowed_text_cache = None

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            old_value = copy(self._value)
            if event.key_code in [10, 13]:
                # Split and insert line  on CR or LF.
                self._value.insert(self._line + 1,
                                   self._value[self._line][self._column:])
                self._value[self._line] = self._value[self._line][:self._column]
                self._line += 1
                self._column = 0
            elif event.key_code == Screen.KEY_BACK:
                if self._column > 0:
                    # Delete character in front of cursor.
                    self._value[self._line] = "".join([
                        self._value[self._line][:self._column - 1],
                        self._value[self._line][self._column:]])
                    self._column -= 1
                else:
                    if self._line > 0:
                        # Join this line with previous
                        self._line -= 1
                        self._column = len(self._value[self._line])
                        self._value[self._line] += \
                            self._value.pop(self._line + 1)
            elif event.key_code == Screen.KEY_DELETE:
                if self._column < len(self._value[self._line]):
                    self._value[self._line] = "".join([
                        self._value[self._line][:self._column],
                        self._value[self._line][self._column + 1:]])
                else:
                    if self._line < len(self._value) - 1:
                        # Join this line with next
                        self._value[self._line] += \
                            self._value.pop(self._line + 1)
            elif event.key_code == Screen.KEY_UP:
                # Move up one line in text
                self._line = max(0, self._line - 1)
                if self._column >= len(self._value[self._line]):
                    self._column = len(self._value[self._line])
            elif event.key_code == Screen.KEY_DOWN:
                # Move down one line in text
                self._line = min(len(self._value) - 1, self._line + 1)
                if self._column >= len(self._value[self._line]):
                    self._column = len(self._value[self._line])
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
            elif event.key_code >= 32:
                # Insert any visible text at the current cursor position.
                self._value[self._line] = chr(event.key_code).join([
                    self._value[self._line][:self._column],
                    self._value[self._line][self._column:]])
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
                                        self._value[self._line][self._start_column + text_col:],
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
                    while self.string_len(line) >= limit:
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
        return "\n".join(self._value) if self._as_string else self._value

    @value.setter
    def value(self, new_value):
        # Only trigger the notification after we've changed the value.
        old_value = self._value
        if new_value is None:
            self._value = [""]
        elif self._as_string:
            self._value = new_value.split("\n")
        else:
            self._value = new_value
        self.reset()
        if old_value != self._value and self._on_change:
            self._on_change()

    @property
    def frame_update_count(self):
        # Force refresh for cursor if needed.
        return 5 if self._has_focus and not self._frame.reduce_cpu else 0


class _BaseListBox(with_metaclass(ABCMeta, Widget)):
    """
    An Internal class to contain common function between list box types.
    """

    def __init__(self, height, options, titles=None, label=None, name=None, on_change=None,
                 on_select=None, validator=None):
        """
        :param height: The required number of input lines for this widget.
        :param options: The options for each row in the widget.
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        :param on_change: Optional function to call when selection changes.
        :param on_select: Optional function to call when the user actually selects an entry from
            this list - e.g. by double-clicking or pressing Enter.
        :param validator: Optional function to validate selection for this widget.
        """
        super(_BaseListBox, self).__init__(name)
        self._options = options
        self._titles = titles
        self._label = label
        self._line = 0
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
                    event = self._scroll_bar.process_event(event)

            # Ignore other mouse events.
            return event
        else:
            # Ignore other events
            return event

        # If we got here, we processed the event - swallow it.
        return None

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

    @property
    def options(self):
        """
        The list of options available for user selection

        This is a list of tuples (<human readable string>, <internal value>).
        """
        return self._options

    @options.setter
    def options(self, new_value):
        self._options = new_value
        self.value = self._options[0][1] if len(self._options) > 0 else None


class ListBox(_BaseListBox):
    """
    A ListBox is a widget that displays a list from which the user can select one option.
    """

    def __init__(self, height, options, centre=False, label=None, name=None, add_scroll_bar=False,
                 on_change=None, on_select=None, validator=None):
        """
        :param height: The required number of input lines for this ListBox.
        :param options: The options for each row in the widget.
        :param centre: Whether to centre the selected line in the list.
        :param label: An optional label for the widget.
        :param name: The name for the ListBox.
        :param on_change: Optional function to call when selection changes.
        :param on_select: Optional function to call when the user actually selects an entry from
        :param validator: Optional function to validate selection for this widget.

        The `options` are a list of tuples, where the first value is the string to be displayed
        to the user and the second is an interval value to identify the entry to the program.
        For example:

            options=[("First option", 1), ("Second option", 2)]
        """
        super(ListBox, self).__init__(
            height, options, label=label, name=name, on_change=on_change, on_select=on_select,
            validator=validator)
        self._centre = centre
        self._add_scroll_bar = add_scroll_bar

    def update(self, frame_no):
        self._draw_label()

        # Prepare to calculate new visible limits if needed.
        height = self._h
        width = self._w
        dx = dy = 0

        # Clear out the existing box content
        (colour, attr, bg) = self._frame.palette["field"]
        for i in range(height):
            self._frame.canvas.print_at(
                " " * self.width,
                self._x + self._offset + dx,
                self._y + i + dy,
                colour, attr, bg)

        # Don't bother with anything else if there are no options to render.
        if len(self._options) <= 0:
            return

        # Decide whether we need to show or hide the scroll bar.
        # TODO: Move this to base package when supported in multicolumnlistbox too.
        if self._add_scroll_bar and self._scroll_bar is None:
            self._scroll_bar = _ScrollBar(
                self._frame.canvas, self._frame.palette, self._x + width - 1, self._y,
                height, self._get_pos, self._set_pos)
        if self._scroll_bar:
            width -= 1

        # Render visible portion of the text.
        y_offset = 0
        if self._centre:
            # Always make selected text the centre - not very compatible with scroll bars, but
            # there's not much else I can do here.
            self._start_line = self._line - (height // 2)
        start_line = self._start_line
        if self._start_line < 0:
            y_offset = -self._start_line
            start_line = 0
        for i, (text, _) in enumerate(self._options):
            if start_line <= i < start_line + height - y_offset:
                colour, attr, bg = self._pick_colours("field", i == self._line)
                if len(text) > width:
                    text = text[:width - 3] + "..."
                self._frame.canvas.print_at(
                    "{:{}}".format(
                        _enforce_width(text, width, self._frame.canvas.unicode_aware), width),
                    self._x + self._offset + dx,
                    self._y + y_offset + i + dy - start_line,
                    colour, attr, bg)

        # And finally draw any scroll bar.
        if self._scroll_bar:
            self._scroll_bar.update()

    def _find_option(self, search_value):
        for text, value in self._options:
            if text.startswith(search_value):
                return value
        return None

    def _get_pos(self):
        """
        Get current position for scroll bar.
        """
        if self._h >= len(self._options):
            return 0
        else:
            return self._start_line / (len(self._options) - self._h)

    def _set_pos(self, pos):
        """
        Set current position for scroll bar.
        """
        if self._h < len(self._options):
            pos *= len(self._options) - self._h
            pos = int(round(max(0, pos), 0))
            self._start_line = pos


class MultiColumnListBox(_BaseListBox):
    """
    A MultiColumnListBox is a widget for displaying tabular data.

    It displays a list of related data in columns, from which the user can select a line.
    """

    def __init__(self, height, columns, options, titles=None, label=None,
                 name=None, on_change=None, on_select=None):
        """
        :param height: The required number of input lines for this ListBox.
        :param columns: A list of widths and alignments for each column.
        :param options: The options for each row in the widget.
        :param titles: Optional list of titles for each column.  Must match the length of
            `columns`.
        :param label: An optional label for the widget.
        :param name: The name for the ListBox.
        :param on_change: Optional function to call when selection changes.
        :param on_select: Optional function to call when the user actually selects an entry from

        The `columns` parameter is a list of integers or strings.  If it is an integer, this is
        the absolute width of the column in characters.  If it is a string, it must be of the
        format "[<align>]<width>[%]" where:

        * <align> is the alignment string ("<" = left, ">" = right, "^" = centre)
        * <width> is the width in characters
        * % is an optional qualifier that says the number is a percentage of the width of the
          widget.

        Column widths need to encompass any space required between columns, so for example, if
        your column is 5 characters, allow 6 for an extra space at the end.  It is not possible
        to do this when you have a right-justified column next to a left-justified column, so
        this widget will automatically space them for you.

        An integer value of 0 is interpreted to be use whatever space is left available after the
        rest of the columns have been calculated.  There must be only one of these columns.

        The number of columns is for this widget is determined from the number of entries in the
        `columns` parameter.  The `options` list is then a list of tuples of the form
        ([val1, val2, ... , valn], index).  For example, this data provides 2 rows for a 3 column
        widget:

            options=[(["One", "row", "here"], 1), (["Second", "row", "here"], 2)]

        The options list may be None and then can be set later using the `options` property on
        this widget.
        """
        super(MultiColumnListBox, self).__init__(
            height, options, titles=titles, label=label, name=name, on_change=on_change,
            on_select=on_select)
        self._columns = []
        self._align = []
        self._spacing = []
        for i, column in enumerate(columns):
            if isinstance(column, int):
                self._columns.append(column)
                self._align.append("<")
            else:
                match = re.match(r"([<>^]?)(\d+)([%]?)", column)
                self._columns.append(float(match.group(2)) / 100
                                     if match.group(3) else int(match.group(2)))
                self._align.append(match.group(1) if match.group(1) else "<")
            self._spacing.append(1 if i > 0 and self._align[i] == "<" and
                                 self._align[i - 1] == ">" else 0)

    def _get_width(self, width):
        """
        Helper function to figure out the actual column width from the various options.

        :param width: The size of column requested
        :return: the integer width of the column in characters
        """
        if isinstance(width, float):
            return int(self._w * width)
        if width == 0:
            width = (self.width - sum(self._spacing) -
                     sum([self._get_width(x) for x in self._columns if x != 0]))
        return width

    def update(self, frame_no):
        self._draw_label()

        # Calculate new visible limits if needed.
        height = self._h
        dx = dy = 0

        # Clear out the existing box content
        (colour, attr, bg) = self._frame.palette["field"]
        for i in range(height):
            self._frame.canvas.print_at(
                " " * self.width,
                self._x + self._offset + dx,
                self._y + i + dy,
                colour, attr, bg)

        # Allow space for titles if needed.
        if self._titles:
            dy += 1
            height -= 1
            row_dx = 0
            colour, attr, bg = self._frame.palette["title"]
            for i, [title, align, space] in enumerate(
                    zip(self._titles, self._align, self._spacing)):
                width = self._get_width(self._columns[i])
                self._frame.canvas.print_at(
                    "{}{:{}{}}".format(" " * space,
                                       _enforce_width(
                                           title, width, self._frame.canvas.unicode_aware),
                                       align, width),
                    self._x + self._offset + row_dx,
                    self._y,
                    colour, attr, bg)
                row_dx += width + space

        # Don't bother with anything else if there are no options to render.
        if len(self._options) <= 0:
            return

        # Render visible portion of the text.
        self._start_line = max(0, max(self._line - height + 1,
                                      min(self._start_line, self._line)))
        for i, [row, _] in enumerate(self._options):
            if self._start_line <= i < self._start_line + height:
                colour, attr, bg = self._pick_colours("field", i == self._line)
                row_dx = 0
                # Try to handle badly formatted data, where row lists don't
                # match the expected number of columns.
                for text, width, align, space in zip_longest(
                        row, self._columns, self._align, self._spacing, fillvalue=""):
                    if width == "":
                        break
                    width = self._get_width(width)
                    if len(text) > width:
                        text = text[:width - 3] + "..."
                    self._frame.canvas.print_at(
                        "{}{:{}{}}".format(" " * space,
                                           _enforce_width(
                                               text, width, self._frame.canvas.unicode_aware),
                                           align, width),
                        self._x + self._offset + dx + row_dx,
                        self._y + i + dy - self._start_line,
                        colour, attr, bg)
                    row_dx += width + space

    def _find_option(self, search_value):
        for row, value in self._options:
            # TODO: Should this be aware of a sort column?
            if row[0].startswith(search_value):
                return value
        return None


class FileBrowser(MultiColumnListBox):
    """
    A FileBrowser is a widget for finding a file on the local disk.
    """

    def __init__(self, height, root, name=None, on_select=None, on_change=None):
        """
        :param height: The desired height for this widget.
        :param root: The starting root directory to display in the widget.
        :param name: The name of this widget.
        :param on_select: Optional function that gets called when user selects a file (by pressing
            enter or double-clicking).
        :param on_change: Optional function that gets called on any movement of the selection.
        """
        super(FileBrowser, self).__init__(
            height,
            [0, ">8", ">14"],
            [],
            titles=["Filename", "Size", "Last modified"],
            name=name,
            on_select=self._on_selection,
            on_change=on_change)

        # Remember the on_select handler for external notification.  This allows us to wrap the
        # normal on_select notification with a function that will open new sub-directories as
        # needed.
        self._external_notification = on_select
        self._root = root
        self._in_update = False
        self._initialized = False

    def update(self, frame_no):
        # Defer initial population until we first display the widget in order to avoid race
        # conditions in the Frame that may be using this widget.
        if not self._initialized:
            self._populate_list(self._root)
            self._initialized = True
        super(FileBrowser, self).update(frame_no)

    def _on_selection(self):
        """
        Internal function to handle directory traversal or bubble notifications up to user of the
        Widget as needed.
        """
        if self.value and os.path.isdir(self.value):
            self._populate_list(self.value)
        elif self._external_notification:
            self._external_notification()

    def clone(self, new_widget):
        # Copy the data into the new widget.  Notes:
        # 1) I don't really want to expose these methods, so am living with the protected access.
        # 2) I need to populate the list and then assign the values to ensure that we get the
        #    right selection on re-sizing.
        new_widget._populate_list(self._root)
        new_widget._start_line = self._start_line
        new_widget._root = self._root
        new_widget.value = self.value

    def _populate_list(self, value):
        """
        Populate the current multi-column list with the contents of the selected directory.

        :param value: The new value to use.
        """
        # Nothing to do if the value is rubbish.
        if value is None:
            return

        # Stop any recursion - no more returns from here to end of fn please!
        if self._in_update:
            return
        self._in_update = True

        # We need to update the tree view.
        self._root = os.path.abspath(value if os.path.isdir(value) else os.path.dirname(value))

        # The absolute expansion of "/" or "\" is the root of the disk, so is a cross-platform
        # way of spotting when to insert ".." or not.
        tree_view = []
        if len(self._root) > len(os.path.abspath(os.sep)):
            tree_view.append((["|-+ .."], os.path.join(self._root, "..")))

        tree_dirs = []
        tree_files = []
        try:
            files = os.listdir(self._root)
        except PermissionError:
            # Can fail on Windows due to access permissions
            files = []
        for my_file in files:
            full_path = os.path.join(self._root, my_file)
            try:
                details = os.lstat(full_path)
            except PermissionError:
                # Can happen on Windows due to access permissions
                details = namedtuple("stat_type", "st_size st_mtime")
                details.st_size = 0
                details.st_mtime = 0
            name = "|-- {}".format(my_file)
            tree = tree_files
            if os.path.isdir(full_path):
                tree = tree_dirs
                if os.path.islink(full_path):
                    # Show links separately for directories
                    real_path = os.path.realpath(full_path)
                    name = "|-+ {} -> {}".format(my_file, real_path)
                else:
                    name = "|-+ {}".format(my_file)
            elif os.path.islink(full_path):
                # Check if link target exists and if it does, show statistics of the
                # linked file, otherwise just display the link
                real_path = os.path.realpath(full_path)
                if os.path.exists(real_path):
                    details = os.stat(real_path)
                    name = "|-- {} -> {}".format(my_file, real_path)
                else:
                    # Both broken directory and file links fall to this case.
                    # Actually using the files will cause a FileNotFound exception
                    name = "|-- {} -> {}".format(my_file, real_path)

            # Normalize names for MacOS and then add to the list.
            tree.append(([unicodedata.normalize("NFC", name),
                          readable_mem(details.st_size),
                          readable_timestamp(details.st_mtime)], full_path))

        tree_view.extend(sorted(tree_dirs))
        tree_view.extend(sorted(tree_files))

        self.options = tree_view
        self._titles[0] = self._root

        # We're out of the function - unset recursion flag.
        self._in_update = False


class Button(Widget):
    """
    A Button widget to be  displayed in a Frame.

    It is typically used to represent a desired action for te user to invoke (e.g. a submit button
    on a form).
    """

    def __init__(self, text, on_click, label=None, add_box=True, **kwargs):
        """
        :param text: The text for the button.
        :param on_click: The function to invoke when the button is clicked.
        :param label: An optional label for the widget.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super(Button, self).__init__(None, **kwargs)
        # We nly ever draw the button with borders, so calculate that once now.
        self._text = "< {} >".format(text) if add_box else text
        self._add_box = add_box
        self._on_click = on_click
        self._label = label

    def set_layout(self, x, y, offset, w, h):
        # Do the usual layout work. then recalculate exact x/w values for the
        # rendered button.
        super(Button, self).set_layout(x, y, offset, w, h)
        text_width = self.string_len(self._text)
        if self._add_box:
            # Minimize widget to make a nice little button.
            self._x += max(0, (self.width - text_width) // 2)
            self._w = min(self._w, text_width)
        else:
            # Maximize text to make for a consistent colouring when used in menus.
            self._text += " " * (self._w - text_width)

    def update(self, frame_no):
        self._draw_label()

        (colour, attr, bg) = self._pick_colours("button")
        self._frame.canvas.print_at(
            self._text,
            self._x + self._offset,
            self._y,
            colour, attr, bg)

    def reset(self):
        self._value = False

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord(" "), 10, 13]:
                self._on_click()
                return None
            else:
                # Ignore any other key press.
                return event
        elif isinstance(event, MouseEvent):
            if event.buttons != 0:
                if (self._x <= event.x < self._x + self._w and
                        self._y <= event.y < self._y + self._h):
                    self._on_click()
                    return None
        # Ignore other events
        return event

    def required_height(self, offset, width):
        return 1

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value


class PopUpDialog(Frame):
    """
    A fixed implementation Frame that provides a standard message box dialog.
    """

    # Override standard palette for pop-ups
    _normal = (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_RED)
    _bold = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_RED)
    _focus = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_YELLOW)
    palette = {
        "background": _normal,
        "shadow": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_BLACK),
        "label": _bold,
        "borders": _normal,
        "scroll": _normal,
        "title": _bold,
        "edit_text": _normal,
        "focus_edit_text": _bold,
        "field": _normal,
        "focus_field": _bold,
        "button": _normal,
        "focus_button": _focus,
        "control": _normal,
        "focus_control": _bold,
        "disabled": _bold,
    }

    def __init__(self, screen, text, buttons, on_close=None, has_shadow=False):
        """
        :param screen: The Screen that owns this dialog.
        :param text: The message text to display.
        :param buttons: A list of button names to display.
        :param on_close: Optional function to invoke on exit.
        :param has_shadow: optional flag to specify if dialog should have a shadow when drawn.

        The `on_close` method (if specified) will be called with one integer parameter that
        corresponds to the index of the button passed in the array of available `buttons`.

        Note that `on_close` must be a static method to work across screen resizing.  Either it
        is static (and so the dialog will be cloned) or it is not (and the dialog will disappear
        when the screen is resized).
        """
        # Remember parameters for cloning.
        self._text = text
        self._buttons = buttons
        self._on_close = on_close

        # Decide on optimum width of the dialog.  Limit to 2/3 the screen width.
        string_len = wcswidth if screen.unicode_aware else len
        width = max([string_len(x) for x in text.split("\n")])
        width = max(width + 4,
                    sum([string_len(x) + 4 for x in buttons]) + len(buttons) + 5)
        width = min(width, screen.width * 2 // 3)

        # Figure out the necessary message and allow for buttons and borders
        # when deciding on height.
        self._message = _split_text(text, width - 4, screen.height - 4, screen.unicode_aware)
        height = len(self._message) + 4

        # Construct the Frame
        self._data = {"message": self._message}
        super(PopUpDialog, self).__init__(
            screen, height, width, self._data, has_shadow=has_shadow, is_modal=True)

        # Build up the message box
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        text_box = TextBox(len(self._message), name="message")
        text_box.disabled = True
        layout.add_widget(text_box)
        layout2 = Layout([1 for _ in buttons])
        self.add_layout(layout2)
        for i, button in enumerate(buttons):
            func = partial(self._destroy, i)
            layout2.add_widget(Button(button, func), i)
        self.fix()

    def _destroy(self, selected):
        self._scene.remove_effect(self)
        if self._on_close:
            self._on_close(selected)

    def clone(self, screen, scene):
        """
        Create a clone of this Dialog into a new Screen.

        :param screen: The new Screen object to clone into.
        :param scene: The new Scene object to clone into.
        """
        # Only clone the object if the function is safe to do so.
        if self._on_close is None or isfunction(self._on_close):
            scene.add_effect(PopUpDialog(screen, self._text, self._buttons, self._on_close))


class _TempPopup(Frame):
    """
    An internal Frame for creating a temporary pop-up for a Widget in another Frame.
    """

    def __init__(self, screen, parent, x, y, w, h):
        """
        :param screen: The Screen being used for this pop-up.
        :param parent: The widget that spawned this pop-up.
        :param x: The X coordinate for the desired pop-up.
        :param y: The Y coordinate for the desired pop-up.
        :param w: The width of the desired pop-up.
        :param h: The height of the desired pop-up.
        """
        # Set up the new palette for this Frame
        self.palette = defaultdict(lambda: parent.frame.palette["focus_field"])
        self.palette["selected_field"] = parent.frame.palette["selected_field"]
        self.palette["selected_focus_field"] = parent.frame.palette["selected_focus_field"]
        self.palette["invalid"] = parent.frame.palette["invalid"]

        # Construct the Frame
        super(_TempPopup, self).__init__(
            screen, h, w, x=x, y=y, has_border=True, can_scroll=False, is_modal=True)

        # Internal state for the pop-up
        self._parent = parent

    def process_event(self, event):
        # Look for events that will close the pop-up - e.g. clicking outside the Frame or Enter key.
        cancelled = False
        if event is not None:
            if isinstance(event, KeyboardEvent):
                if event.key_code in [Screen.ctrl("M"), Screen.ctrl("J"), ord(" ")]:
                    event = None
                elif event.key_code == Screen.KEY_ESCAPE:
                    event = None
                    cancelled = True
            elif isinstance(event, MouseEvent):
                origin = self._canvas.origin
                if event.y < origin[1] or event.y >= origin[1] + self._canvas.height:
                    event = None
                elif event.x < origin[0] or event.x >= origin[0] + self._canvas.width:
                    event = None

        # Remove this pop-up if we're done; otherwise bubble up the event.
        if event is None:
            try:
                self.close(cancelled)
            except InvalidFields:
                # Nothing to do as we've already prevented the Effect from being removed.
                pass
        return super(_TempPopup, self).process_event(event)

    def close(self, cancelled=False):
        """
        Close this temporary pop-up.

        :param cancelled: Whether the pop-up was cancelled (e.g. by pressing Esc).
        """
        self._on_close(cancelled)
        self._scene.remove_effect(self)

    @abstractmethod
    def _on_close(self, cancelled):
        """
        Method to handle any communication back to the parent widget on closure of this pop-up.

        :param cancelled: Whether the pop-up was cancelled (e.g. by pressing Esc).

        This method can raise an InvalidFields exception to indicate that the current selection is
        invalid and so the pop-up cannot be dismissed.
        """
        pass


class _TimePickerPopup(_TempPopup):
    """
    An internal Frame for editing the currently selected time.
    """

    def __init__(self, parent):
        """
        :param parent: The widget that spawned this pop-up.
        """
        # Construct the Frame
        location = parent.get_location()
        super(_TimePickerPopup, self).__init__(parent.frame.screen,
                                               parent,
                                               location[0] - 1, location[1] - 2,
                                               10 if parent.include_seconds else 7, 5)

        # Build the widget to display the time selection.
        self._hours = ListBox(3, [("{:02}".format(x), x) for x in range(24)], centre=True)
        self._minutes = ListBox(3, [("{:02}".format(x), x) for x in range(60)], centre=True)
        self._seconds = ListBox(3, [("{:02}".format(x), x) for x in range(60)], centre=True)
        if self._parent.include_seconds:
            layout = Layout([2, 1, 2, 1, 2], fill_frame=True)
        else:
            layout = Layout([2, 1, 2], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._hours, 0)
        layout.add_widget(Label("\n:", height=3), 1)
        layout.add_widget(self._minutes, 2)
        if self._parent.include_seconds:
            layout.add_widget(Label("\n:", height=3), 3)
            layout.add_widget(self._seconds, 4)
        self.fix()

        # Set up the correct time.
        self._hours.value = parent.value.hour
        self._minutes.value = parent.value.minute
        self._seconds.value = parent.value.second

    def _on_close(self, cancelled):
        if not cancelled:
            self._parent.value = self._parent.value.replace(hour=self._hours.value,
                                                            minute=self._minutes.value,
                                                            second=self._seconds.value)


class TimePicker(Widget):
    """
    A TimePicker widget allows you to pick a time from a compact, temporary, pop-up Frame.
    """

    def __init__(self, label=None, name=None, seconds=False, on_change=None, **kwargs):
        """
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        :param seconds: Whether to include selection of seconds or not.
        :param on_change: Optional function to call when the selected time changes.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super(TimePicker, self).__init__(name, **kwargs)
        self._label = label
        self._on_change = on_change
        self._value = None
        self._child = None
        self.include_seconds = seconds

    def update(self, frame_no):
        self._draw_label()

        # This widget only ever needs display the current selection - the separate Frame does all
        # the clever stuff when it has the focus.
        (colour, attr, bg) = self._pick_colours("edit_text")
        self._frame.canvas.print_at(
            self._value.strftime("%H:%M:%S" if self.include_seconds else "%H:%M"),
            self._x + self._offset,
            self._y,
            colour, attr, bg)

    def reset(self):
        pass

    def process_event(self, event):
        if event is not None:
            # Handle key or mouse selection events - e.g. click on widget or Enter.
            if isinstance(event, KeyboardEvent):
                if event.key_code in [Screen.ctrl("M"), Screen.ctrl("J"), ord(" ")]:
                    event = None
            elif isinstance(event, MouseEvent):
                if event.buttons != 0:
                    if self.is_mouse_over(event, include_label=False):
                        event = None

            # Create the pop-up if needed
            if event is None:
                self._child = _TimePickerPopup(self)
                self.frame.scene.add_effect(self._child)

        return event

    def required_height(self, offset, width):
        return 1

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        # Only trigger the notification after we've changed the value.
        old_value = self._value
        self._value = new_value
        if old_value != self._value and self._on_change:
            self._on_change()


class _DatePickerPopup(_TempPopup):
    """
    An internal Frame for editing the currently selected date.
    """

    def __init__(self, parent, year_range=None):
        """
        :param parent: The widget that spawned this pop-up.
        :param year_range: Optional range to limit the year selection to.
        """
        # Create the lists for each entry.
        now = parent.value if parent.value else date.today()
        if year_range is None:
            year_range = range(now.year - 50, now.year + 50)
        self._days = ListBox(3,
                             [("{:02}".format(x), x) for x in range(1, 32)],
                             centre=True,
                             validator=self._check_date)
        self._months = ListBox(3,
                               [(now.replace(day=1, month=x).strftime("%b"), x)
                                for x in range(1, 13)],
                               centre=True,
                               on_change=self._refresh_day)
        self._years = ListBox(3,
                              [("{:04}".format(x), x) for x in year_range],
                              centre=True,
                              on_change=self._refresh_day)

        # Construct the Frame
        location = parent.get_location()
        super(_DatePickerPopup, self).__init__(parent.frame.screen,
                                               parent,
                                               location[0] - 1, location[1] - 2,
                                               13, 5)

        # Build the widget to display the time selection.
        layout = Layout([2, 1, 3, 1, 4], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._days, 0)
        layout.add_widget(Label("\n/", height=3), 1)
        layout.add_widget(self._months, 2)
        layout.add_widget(Label("\n/", height=3), 3)
        layout.add_widget(self._years, 4)
        self.fix()

        # Set up the correct time.
        self._years.value = parent.value.year
        self._months.value = parent.value.month
        self._days.value = parent.value.day

    def _check_date(self, value):
        try:
            date(self._years.value, self._months.value, value)
            return True
        except (TypeError, ValueError):
            return False

    def _refresh_day(self):
        self._days.value = self._days.value

    def _on_close(self, cancelled):
        try:
            if not cancelled:
                self._parent.value = self._parent.value.replace(day=self._days.value,
                                                                month=self._months.value,
                                                                year=self._years.value)
        except ValueError:
            raise InvalidFields([self._days])


class DatePicker(Widget):
    """
    A DatePicker widget allows you to pick a date from a compact, temporary, pop-up Frame.
    """

    def __init__(self, label=None, name=None, year_range=None, on_change=None, **kwargs):
        """
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        :param on_change: Optional function to call when the selected time changes.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super(DatePicker, self).__init__(name, **kwargs)
        self._label = label
        self._on_change = on_change
        self._value = None
        self._child = None
        self._year_range = year_range

    def update(self, frame_no):
        self._draw_label()

        # This widget only ever needs display the current selection - the separate Frame does all
        # the clever stuff when it has the focus.
        (colour, attr, bg) = self._pick_colours("edit_text")
        self._frame.canvas.print_at(
            self._value.strftime("%d/%b/%Y"),
            self._x + self._offset,
            self._y,
            colour, attr, bg)

    def reset(self):
        pass

    def process_event(self, event):
        if event is not None:
            if isinstance(event, KeyboardEvent):
                if event.key_code in [Screen.ctrl("M"), Screen.ctrl("J"), ord(" ")]:
                    event = None
            elif isinstance(event, MouseEvent):
                if event.buttons != 0:
                    if self.is_mouse_over(event, include_label=False):
                        event = None
            if event is None:
                self._child = _DatePickerPopup(self, year_range=self._year_range)
                self.frame.scene.add_effect(self._child)

        return event

    def required_height(self, offset, width):
        return 1

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        # Only trigger the notification after we've changed the value.
        old_value = self._value
        self._value = new_value
        if old_value != self._value and self._on_change:
            self._on_change()


class _DropdownPopup(_TempPopup):
    """
    An internal Frame for selecting an item from a drop-down list..
    """

    def __init__(self, parent):
        """
        :param parent: The widget that spawned this pop-up.
        """
        # Decide which way to present the list - up or down from the parent widget.
        location = parent.get_location()
        if parent.frame.screen.height - location[1] < 3:
            height = min(len(parent.options) + 4, location[1] + 2)
            start_line = location[1] - height + 2
            reverse = True
        else:
            start_line = location[1] - 1
            height = min(len(parent.options) + 4, parent.frame.screen.height - location[1] + 1)
            reverse = False

        # Construct the Frame
        super(_DropdownPopup, self).__init__(parent.frame.screen,
                                             parent,
                                             location[0], start_line,
                                             parent.width, height)

        # Build the widget to display the time selection.
        layout = Layout([1], fill_frame=True)
        self.add_layout(layout)
        self._field = Text()
        self._field.disabled = True
        divider = Divider()
        divider.disabled = True
        self._list = ListBox(Widget.FILL_FRAME,
                             parent.options,
                             add_scroll_bar=len(parent.options) > height - 4,
                             on_select=self.close, on_change=self._link)
        layout.add_widget(self._list if reverse else self._field, 0)
        layout.add_widget(divider, 0)
        layout.add_widget(self._field if reverse else self._list, 0)
        self.fix()

        # Set up the correct time.
        self._list.value = parent.value

    def _link(self):
        self._field.value = self._list.options[self._list._line][0]

    def _on_close(self, cancelled):
        if not cancelled:
            self._parent.value = self._list.value


class DropdownList(Widget):
    """
    This widget allows you to pick an item from a temporary pop-up list.
    """

    def __init__(self, options, label=None, name=None, on_change=None, **kwargs):
        """
        :param options: The options for each row in the widget.
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        :param on_change: Optional function to call when the selected time changes.

        The `options` are a list of tuples, where the first value is the string to be displayed
        to the user and the second is an interval value to identify the entry to the program.
        For example:

            options=[("First option", 1), ("Second option", 2)]

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super(DropdownList, self).__init__(name, **kwargs)
        self._label = label
        self._on_change = on_change
        self._child = None
        self._options = options
        self._line = 0 if len(options) > 0 else None
        self._value = options[self._line][1] if self._line is not None else None

    @property
    def options(self):
        """
        The set of allowed options for the drop-down list.
        """
        return self._options

    def update(self, frame_no):
        self._draw_label()

        # This widget only ever needs display the current selection - the separate Frame does all
        # the clever stuff when it has the focus.
        text = "" if self._line is None else self._options[self._line][0]
        (colour, attr, bg) = self._pick_colours("field", selected=self._has_focus)
        self._frame.canvas.print_at(
            "[{:{}}]".format(
                _enforce_width(text, self.width - 2, self._frame.canvas.unicode_aware),
                self.width - 2),
            self._x + self._offset,
            self._y,
            colour, attr, bg)

    def reset(self):
        pass

    def process_event(self, event):
        if event is not None:
            if isinstance(event, KeyboardEvent):
                if event.key_code in [Screen.ctrl("M"), Screen.ctrl("J"), ord(" ")]:
                    event = None
            elif isinstance(event, MouseEvent):
                if event.buttons != 0:
                    if self.is_mouse_over(event, include_label=False):
                        event = None
            if event is None:
                self._child = _DropdownPopup(self)
                self.frame.scene.add_effect(self._child)

        return event

    def required_height(self, offset, width):
        return 1

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
            self._value = self._line = None
        if old_value != self._value and self._on_change:
            self._on_change()


class _ScrollBar(object):
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
        self._palette = palette
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
        cursor = u"█" if self._canvas.unicode_aware else "O"
        back = u"░" if self._canvas.unicode_aware else "|"

        # Now draw...
        try:
            sb_pos = self._get_pos()
            sb_pos = min(1, max(0, sb_pos))
            sb_pos = max(int(self._height * sb_pos) - 1, 0)
        except ZeroDivisionError:
            sb_pos = 0
        (colour, attr, bg) = self._palette["scroll"]
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


class PopupMenu(Frame):
    """
    A widget for displaying a menu.
    """

    palette = defaultdict(lambda: (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_CYAN))
    palette["focus_button"] = (Screen.COLOUR_CYAN, Screen.A_NORMAL, Screen.COLOUR_WHITE)

    def __init__(self, screen, menu_items, x, y):
        """
        :param screen: The Screen being used for this pop-up.
        :param menu_items: a list of items to be displayed in the menu.
        :param x: The X coordinate for the desired pop-up.
        :param y: The Y coordinate for the desired pop-up.

        The menu_items parameter is a list of 2-tuples, which define the text to be displayed in
        the menu and the function to call when that menu item is clicked.  For example:

            menu_items = [("Open", file_open), ("Save", file_save), ("Close", file_close)]
        """
        # Sort out location based on width of menu text.
        w = max(len(i[0]) for i in menu_items)
        h = len(menu_items)
        if x + w >= screen.width:
            x -= w - 1
        if y + h >= screen.height:
            y -= h - 1

        # Construct the Frame
        super(PopupMenu, self).__init__(
            screen, h, w, x=x, y=y, has_border=False, is_modal=True, hover_focus=True)

        # Build the widget to display the time selection.
        layout = Layout([1], fill_frame=True)
        self.add_layout(layout)
        for item in menu_items:
            func = partial(self._destroy, item[1])
            layout.add_widget(Button(item[0], func, add_box=False), 0)
        self.fix()

    def _destroy(self, callback=None):
        self._scene.remove_effect(self)
        if callback is not None:
            callback()

    def process_event(self, event):
        # Look for events that will close the pop-up - e.g. clicking outside the Frame or ESC key.
        if event is not None:
            if isinstance(event, KeyboardEvent):
                if event.key_code == Screen.KEY_ESCAPE:
                    event = None
            elif isinstance(event, MouseEvent) and event.buttons != 0:
                origin = self._canvas.origin
                if event.y < origin[1] or event.y >= origin[1] + self._canvas.height:
                    event = None
                elif event.x < origin[0] or event.x >= origin[0] + self._canvas.width:
                    event = None
        if event is None:
            self._destroy()
        return super(PopupMenu, self).process_event(event)


class VerticalDivider(Widget):
    """
    A vertical divider for separating columns.

    This widget should be put into a column of its own in the Layout.
    """

    def __init__(self, height=Widget.FILL_COLUMN):
        """
        :param height: The required height for this divider.
        """
        super(VerticalDivider, self).__init__(None, tab_stop=False)
        self._required_height = height

    def process_event(self, event):
        return event

    def update(self, frame_no):
        (color, attr, bg) = self._frame.palette["borders"]
        vert = u"│" if self._frame.canvas.unicode_aware else "|"
        for i in range(self._h):
            self._frame.canvas.print_at(vert, self._x, self._y + i, color, attr, bg)

    def reset(self):
        pass

    def required_height(self, offset, width):
        return self._required_height

    @property
    def value(self):
        return self._value
