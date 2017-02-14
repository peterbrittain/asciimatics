# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from types import FunctionType
import re
from builtins import chr
from builtins import range
from builtins import object
from copy import copy, deepcopy
from functools import partial
from future.moves.itertools import zip_longest
from future.utils import with_metaclass
from abc import ABCMeta, abstractmethod, abstractproperty
from asciimatics.effects import Effect
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.exceptions import Highlander, InvalidFields
from asciimatics.screen import Screen, Canvas


def _split_text(text, width, height):
    """
    Split text to required dimensions.  This will first try to split the
    text into multiple lines, then put a "..." on the last 3 characters of
    the last line if this still doesn't fit.

    :param text: The text to split.
    :param width: The maximum width for any line.
    :param height: The maximum height for the resulting text.
    :return: A list of strings of the broken up text.
    """
    tokens = text.split(" ")
    result = []
    current_line = ""
    for token in tokens:
        for i, line_token in enumerate(token.split("\n")):
            if len(current_line + line_token) > width or i > 0:
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


class Frame(Effect):
    """
    A Frame is a special Effect for controlling and displaying Widgets and
    is similar to a window as used in native GUI applications.  Widgets
    are text UI elements that can be used to create an interactive application
    within your Frame.
    """

    # Colour palette for the widgets within the Frame.
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
                 x=None, y=None, has_shadow=False, reduce_cpu=False):
        """
        :param screen: The Screen that owns this Frame.
        :param width: The desired width of the Frame.
        :param height: The desired height of the Frame.
        :param data: optional data dict to initialize any widgets in the frame.
        :param on_load: optional function to call whenever the Frame reloads.
        :param has_border: Whether the frame has a border box (and scroll bar).
            Defaults to True.
        :param hover_focus: Whether hovering a mouse over a widget (i.e. mouse
            move events) should change the input focus.  Defaults to false.
        :param name: Optional name to identify this Frame.  This is used to
            reset data as needed from on old copy after the screen resizes.
        :param title: Optional title to display if has_border is True.
        :param x: Optional x position for the top left corner of the Frame.
        :param y: Optional y position for the top left corner of the Frame.
        :param has_shadow: Optional flag to indicate if this Frame should have
            a shadow when drawn.
        :param reduce_cpu: Whether to minimize CPU usage (for use on low spec
            systems).
        """
        super(Frame, self).__init__()
        self._focus = 0
        self._max_height = 0
        self._layouts = []
        self._effects = []
        self._screen = screen
        self._canvas = Canvas(screen, height, width, x, y)
        self._data = None
        self._on_load = on_load
        self._has_border = has_border
        self._hover_focus = hover_focus
        self._initial_data = data if data else {}
        self._title = " " + title[0:width - 4] + " " if title else ""
        self._has_shadow = has_shadow
        self._reduce_cpu = reduce_cpu

        # A unique name is needed for cloning.  Try our best to get one!
        self._name = title if name is None else name

        # Flag to catch recursive calls inside the data setting.  This is
        # typically caused by callbacks subsequently trying to re-use functions.
        self._in_call = False

        # Now set up any passed data - use the public property to trigger any
        # necessary updates.
        self.data = deepcopy(self._initial_data)

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
        Fix the layouts and calculate the locations of all the widgets.  This
        should be called once all Layouts have been added to the Frame and all
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
        # TODO: Fix internal use of buffer height - wait until this is retired.
        for y in range(self._canvas._buffer_height):
            self._canvas.print_at(
                " " * self._canvas.width, 0, y, colour, attr, bg)

    def _update(self, frame_no):
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
            self._canvas.print_at(
                self._title,
                (self._canvas.width - len(self._title)) // 2,
                self._canvas.start_line,
                colour, attr, bg)

            # And now the scroll bar
            if self._canvas.height > 5:
                # Sort out chars
                cursor = u"█" if self._canvas.unicode_aware else "O"
                back = u"░" if self._canvas.unicode_aware else "|"

                # Now draw...
                sb_height = self._canvas.height - 4
                try:
                    sb_pos = (self._canvas.start_line /
                              (self._max_height - self._canvas.height))
                    sb_pos = min(1, max(0, sb_pos))
                    sb_pos = max(int(sb_height * sb_pos) - 1, 0)
                except ZeroDivisionError:
                    sb_pos = 0
                (colour, attr, bg) = self.palette["scroll"]
                for dy in range(sb_height):
                    y = self._canvas.start_line + dy + 2
                    self._canvas.print_at(cursor if dy == sb_pos else back,
                                          self._canvas.width - 1, y,
                                          colour, attr, bg)

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
    def frame_update_count(self):
        """
        The number of frames before this Effect should be updated.
        """
        result = 1000000
        for layout in self._layouts:
            if layout.frame_update_count > 0:
                result = min(result, layout.frame_update_count)
        return result

    @property
    def reduce_cpu(self):
        """
        Whether this Frame should try to optimize refreshes to reduce CPU.
        """
        return self._reduce_cpu

    def clone(self, _, scene):
        """
        Create a clone of this Frame into a new Screen.

        :param scene: The new Scene object to clone into.
        """
        # Default implementation is to assume that the application creates a
        # new set of Frames and so we need to match up the data from the old
        # object to the new (using the name).
        if self._name is not None:
            for effect in scene.effects:
                if isinstance(effect, Frame):
                    if effect._name == self._name:
                        effect.data = self.data

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
        Save the current values in all the widgets back to the persistent data
        storage.

        :param validate: Whether to validate the data before saving.

        Calling this while setting the `data` field (e.g. in a widget callback)
        will have no effect.

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
        Make the specified location visible.  This is typically used by a widget
        to scroll the canvas such that it is visible.

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
                (y >= start_y) and (y < start_y + height)):
            # Already OK - quit now.
            return

        if y < start_y:
            self.canvas.scroll_to(y - 1 if self._has_border else y)
        else:
            line = y + h - self.canvas.height + (1 if self._has_border else 0)
            self.canvas.scroll_to(max(0, line))

    def rebase_event(self, event):
        """
        Rebase the coordinates of the passed event to frame-relative
        coordinates.

        :param event: The event to be rebased.
        :returns: A new event object appropriately re-based.
        """
        new_event = copy(event)
        if isinstance(new_event, MouseEvent):
            origin = self._canvas.origin
            new_event.x -= origin[0]
            new_event.y -= origin[1] - self._canvas.start_line
        return new_event

    def process_event(self, event):
        # Claim the input focus if a mouse clicked on this Frame.
        claimed_focus = False
        if isinstance(event, MouseEvent):
            new_event = self.rebase_event(event)
            if (0 <= new_event.x < self._canvas.width and
                0 <= new_event.y < self._canvas.height and
                    event.buttons > 0):
                self._scene.remove_effect(self)
                self._scene.add_effect(self)
                claimed_focus = True

        # No need to do anything if this Frame has no Layouts - and hence no
        # widgets.  Swallow all Keyboard events while we have focus.
        #
        # Also don't bother trying to process widgets if there is no defined
        # focus.  This means there is no enabled widget in the Frame.
        # TODO: Is concept of Frame focus well defined?
        if (self._focus < 0 or self._focus >= len(self._layouts) or
                not self._layouts):
            if event is not None and isinstance(event, KeyboardEvent):
                return
            else:
                # Don't allow mouse events to bubble down if this window owns
                # the Screen - as already calculated when taking te focus.
                return None if claimed_focus else event

        # Give the current widget in focus first chance to process the event.
        event = self._layouts[self._focus].process_event(event,
                                                         self._hover_focus)

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
                    event = None
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
                    event = None
            elif isinstance(event, MouseEvent):
                # Give layouts/widgets first dibs on the mouse message.
                for layout in self._layouts:
                    if layout.process_event(event, self._hover_focus) is None:
                        return

                # If no joy, check whether the scroll bar was clicked.
                if self._has_border:
                    # Don't use rebase as this converts to scrolled coordinates.
                    x = event.x - self._canvas.origin[0]
                    y = event.y - self._canvas.origin[1]
                    if (x == self.canvas.width - 1 and
                            1 < y < self.canvas.height - 2):
                        sb_height = self._canvas.height - 5
                        sb_pos = (y - 2) / sb_height
                        sb_pos *= self._max_height - self._canvas.height + 1
                        sb_pos = int(max(0, sb_pos))
                        self._canvas.print_at(str(sb_pos), 1, 1)
                        self._canvas.scroll_to(sb_pos)
                        return

        # Don't allow mouse events to bubble down if this window owns
        # the Screen - as already calculated when taking te focus.
        return None if claimed_focus else event


class Layout(object):
    """
    Widget layout handler.  All Widgets must be contained within a Layout within
    a Frame.  The Layout class is responsible for deciding the exact size and
    location of the widgets.  The logic uses similar ideas as used in modern
    web frameworks and is as follows.

    1.  The Frame owns one or more Layouts.  The Layouts stack one above each
        other when displayed - i.e. the first Layout in the Frame is above the
        second, etc.
    2.  Each Layout defines the horizontal constraints by defining columns
        as a percentage of the full canvas width.
    3.  The Widgets are assigned a column within the Layout that owns them.
    4.  The Layout then decides the exact size and location to make the
        Widget best fit the canvas as constrained by the above.
    """

    def __init__(self, columns, fill_frame=False):
        """
        :param columns: A list of numbers specifying the width of each column
            in this layout.
        :param fill_frame: Whether this Layout should attempt to fill the rest
            of the Frame.  Defaults to False.

        The Layout will automatically normalize the units used for the columns,
        e.g. converting [2, 6, 2] to [20%, 60%, 20%] of the available canvas.
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
        :param column: The column within the widget for this widget.  Defaults
                       to zero.
        """
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

        The force_column and force_widget parameters must both be set
        together or they will otherwise be ignored.

        :raises IndexError: if a force option specifies a bad column or widget,
            or if the whole Layout is readonly.
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
        for i, column in enumerate(self._columns):
            # For each column determine if we need a tab offset for labels.
            # Only allow labels to take up 1/3 of the column.
            if len(column) > 0:
                offset = max([0 if w.label is None else len(w.label) + 1
                              for w in column])
            else:
                offset = 0
            offset = int(min(offset,
                         width * self._column_sizes[i] // 3))

            # Possibly do 2 passes to allow one widget to fill remaining space
            # on the screen.
            fill_widget = None
            fill_height = 0
            for _ in range(2):
                # Now go through each widget getting them to resize to the
                # required width and label offset.
                y = start_y
                w = int(width * self._column_sizes[i])
                for widget in column:
                    h = widget.required_height(offset, w)
                    if h == Widget.FILL_FRAME:
                        if fill_widget is None:
                            # First pass - note down required filler.
                            fill_widget = widget
                        elif fill_widget == widget:
                            # Second pass - resize to calculated size
                            widget.set_layout(x, y, offset, w, fill_height)
                            h = fill_height
                            y += h
                        else:
                            # First pass, but a second widget - this is a bug.
                            raise Highlander("Too many Widgets filling Layout")
                    else:
                        widget.set_layout(x, y, offset, w, h)
                        y += h
                if fill_widget is None:
                    # No variable height widget - stop iterating.
                    break
                else:
                    # We need to figure out space left.  The Screen might be so
                    # small that there is no space, so make sure we always have
                    # at least one line.
                    fill_height = max(1, start_y + max_height - y)
            max_y = max(max_y, y)
            x += w
        if self.fill_frame:
            max_y = max(max_y, start_y + max_height)
        return max_y

    def _find_next_widget(self, direction, stay_in_col=False, start_at=None,
                          wrap=False):
        """
        Find the next widget to get the focus, stopping at the start/end of the
        list if hit.

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
        :returns: None if the Effect processed the event, else the original
                  event.
        """
        # Check whether this Layout is read-only - i.e. has no active focus.
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
                # Mouse event - rebase coordinates to Frame context.
                new_event = self._frame.rebase_event(event)
                if ((hover_focus and event.buttons >= 0) or
                        event.buttons > 0):
                    # Mouse click - look to move focus.
                    for i, column in enumerate(self._columns):
                        for j, widget in enumerate(column):
                            if widget.is_mouse_over(new_event):
                                self._frame.switch_focus(self, i, j)
                                widget.process_event(event)
                                return
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
        Save the current values in all the widgets back to the persistent data
        storage.

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

    def update_widgets(self):
        """
        Reset the values for any Widgets in this Layout based on the current
        Frame data store.
        """
        for column in self._columns:
            for widget in column:
                if widget.name in self._frame.data:
                    widget.value = self._frame.data[widget.name]
                elif widget.is_tab_stop:
                    widget.value = None

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

    def __init__(self, name, tab_stop=True):
        """
        :param name: The name of this Widget.
        :param tab_stop: Whether this widget should take focus or not when
                         tabbing around the Frame.
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

    @property
    def frame_update_count(self):
        """
        The number of frames before this Widget should be updated.
        """
        return 0

    @disabled.setter
    def disabled(self, new_value):
        self._is_disabled = new_value

    def register_frame(self, frame):
        """
        Register the Frame that owns this Widget.

        :param frame: The owning Frame.
        """
        self._frame = frame

    def set_layout(self, x, y, offset, w, h):
        """
        Set the size and position of the Widget.  This should not be called
        directly.  It is used by the :py:obj:`.Layout` class to arrange all
        widgets within the Frame.

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

    def focus(self):
        """
        Call this to give this Widget the input focus.
        """
        self._has_focus = True
        self._frame.move_to(self._x, self._y, self._h)

    def is_mouse_over(self, event, include_label=True):
        """
        Check if the specified mouse event is over this widget.

        :param event: The MouseEvent to check.
        :param include_label: Include space reserved for the label when
            checking for .
        :returns: True if the mouse is over the active parts of the widget.
        """
        # Disabled widgets should not react to the mouse.
        if self._is_disabled:
            return False

        # Check for any overlap
        if self._y <= event.y < self._y + self._h:
            if ((include_label and self._x <= event.x < self._x + self._w) or
                    (self._x + self._offset <= event.x < self._x + self._w)):
                return True

        return False

    def blur(self):
        """
        Call this to take the input focus from this Widget.
        """
        self._has_focus = False

    def _draw_label(self):
        """
        Draw the label for this widget if needed.
        """
        if self._label is not None:
            # Break the label up as required.
            if self._display_label is None:
                # noinspection PyTypeChecker
                self._display_label = _split_text(
                    self._label, self._offset, self._h)

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
        if self.disabled:
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
        :returns: None if the Effect processed the event, else the original
                  event.
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
    A simple text label.
    """

    def __init__(self, label):
        """
        :param label: The text to be displayed for the Label.
        """
        # Labels have no value and so should have no name for look-ups either.
        super(Label, self).__init__(None, tab_stop=False)
        # Although this is a label, we don't want it to contribute to the layout
        # tab calculations, so leave internal `_label` value as None.
        self._text = label

    def process_event(self, event):
        # Labels have no user interactions
        return event

    def update(self, frame_no):
        (colour, attr, bg) = self._frame.palette["label"]
        self._frame.canvas.print_at(
            self._text, self._x, self._y, colour, attr, bg)

    def reset(self):
        pass

    def required_height(self, offset, width):
        # Allow one line for text and a blank spacer before it.
        return 1

    @property
    def value(self):
        return self._value


class Divider(Widget):
    """
    A simple divider to break up a group of widgets.
    """

    def __init__(self, draw_line=True, height=1):
        """
        :param draw_line: Whether to draw a line in the centre of the gap.
        :param height: The required vertical gap.
        """
        # Dividers have no value and so should have no name for look-ups either.
        super(Divider, self).__init__(None, tab_stop=False)
        self._draw_line = draw_line
        self._required_height = height

    def process_event(self, event):
        # Dividers have no user interactions
        return event

    def update(self, frame_no):
        (colour, attr, bg) = self._frame.palette["borders"]
        if self._draw_line:
            horiz = u"─" if self._frame.canvas.unicode_aware else "-"
            self._frame.canvas.print_at(horiz * self._w,
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
    A Text widget is a single line input field.  It consists of an optional
    label and an entry box.
    """

    def __init__(self, label=None, name=None, on_change=None, validator=None):
        """
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        :param on_change: Optional function to call when text changes.
        :param validator: Optional definition of valid data for this widget.
            This can be a function (which takes the current value and returns
            True for valid content) or a regex string, which must match the
            entire allowed value.
        """
        super(Text, self).__init__(name)
        self._label = label
        self._column = 0
        self._start_column = 0
        self._on_change = on_change
        self._validator = validator

    def update(self, frame_no):
        self._draw_label()

        # Calculate new visible limits if needed.
        width = self._w - self._offset
        self._start_column = max(0, max(self._column - width + 1,
                                        min(self._start_column, self._column)))

        # Render visible portion of the text.
        (colour, attr, bg) = self._pick_colours("edit_text")
        text = self._value[self._start_column:self._start_column + width]
        text += " " * (width - len(text))
        self._frame.canvas.print_at(
            text,
            self._x + self._offset,
            self._y,
            colour, attr, bg)

        # Since we switch off the standard cursor, we need to emulate our own
        # if we have the input focus.
        if self._has_focus:
            self._draw_cursor(
                " " if self._column >= len(self._value) else
                self._value[self._column],
                frame_no,
                self._x + self._offset + self._column - self._start_column,
                self._y)

    def reset(self):
        # Reset to original data and move to end of the text.
        self._column = len(self._value)

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code == Screen.KEY_BACK:
                if self._column > 0:
                    # Delete character in front of cursor - use value to trigger
                    # events.
                    self.value = "".join([
                        self._value[:self._column - 1],
                        self._value[self._column:]])
                    self._column -= 1
            if event.key_code == Screen.KEY_DELETE:
                if self._column < len(self._value):
                    self.value = "".join([
                        self._value[:self._column],
                        self._value[self._column + 1:]])
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
                self.value = chr(event.key_code).join([
                    self._value[:self._column],
                    self._value[self._column:]])
                self._column += 1
            else:
                # Ignore any other key press.
                return event
        elif isinstance(event, MouseEvent):
            # Mouse event - rebase coordinates to Frame context.
            new_event = self._frame.rebase_event(event)
            if event.buttons != 0:
                if self.is_mouse_over(new_event, include_label=False):
                    self._column = min(
                        len(self._value),
                        new_event.x - self._x - self._offset +
                        self._start_column)
                    self._column = max(0, self._column)
                    return
            # Ignore other mouse events.
            return event
        else:
            # Ignore other events
            return event

    def required_height(self, offset, width):
        return 1

    @property
    def value(self):
        return self._value

    @property
    def frame_update_count(self):
        # Force refresh for cursor if needed.
        return 5 if self._has_focus and not self._frame.reduce_cpu else 0

    @value.setter
    def value(self, new_value):
        # Only trigger the notification after we've changed the value.
        old_value = self._value
        self._value = new_value if new_value else ""
        if old_value != self._value and self._on_change:
            self._on_change()
        if self._validator:
            if isinstance(self._validator, FunctionType):
                self._is_valid = self._validator(self._value)
            else:
                self._is_valid = re.match(self._validator,
                                          self._value) is not None


class CheckBox(Widget):
    """
    A CheckBox widget is used to ask for simple Boolean (i.e. yes/no) input.  It
    consists of an optional label (typically used for the first in a group of
    CheckBoxes), the box and a field name.
    """

    def __init__(self, text, label=None, name=None, on_change=None):
        """
        :param text: The text to explain this specific field to the user.
        :param label: An optional label for the widget.
        :param name: The internal name for the widget.
        :param on_change: Optional function to call when text changes.
        """
        super(CheckBox, self).__init__(name)
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
            new_event = self._frame.rebase_event(event)
            if event.buttons != 0:
                if self.is_mouse_over(new_event, include_label=False):
                    # Use property to trigger events.
                    self.value = not self._value
                    return
            # Ignore other mouse events.
            return event
        else:
            # Ignore other events
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
        self._value = new_value if new_value else False
        if old_value != self._value and self._on_change:
            self._on_change()


class RadioButtons(Widget):
    """
    A RadioButtons widget is used to ask for one of a list of values to be
    selected by the user. It consists of an optional label and then a list of
    selection bullets with field names.
    """

    def __init__(self, options, label=None, name=None, on_change=None):
        """
        :param options: A list of (text, value) tuples for each radio button.
        :param label: An optional label for the widget.
        :param name: The internal name for the widget.
        :param on_change: Optional function to call when text changes.
        """
        super(RadioButtons, self).__init__(name)
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
            fg, attr, bg = self._pick_colours("control", i == self._selection)
            fg2, attr2, bg2 = self._pick_colours("field", i == self._selection)
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
            new_event = self._frame.rebase_event(event)
            if event.buttons != 0:
                if self.is_mouse_over(new_event, include_label=False):
                    # Use property to trigger events.
                    self._selection = new_event.y - self._y
                    self.value = self._options[self._selection][1]
                    return
            # Ignore other mouse events.
            return event
        else:
            # Ignore non-keyboard events
            return event

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
    A TextBox is a simple widget for recording and displaying the text that has
    been typed into it (when it has the focus).  It consists of a simple
    framed box with option label.  It can take multi-line input.
    """

    def __init__(self, height, label=None, name=None, as_string=False,
                 on_change=None):
        """
        :param height: The required number of input lines for this TextBox.
        :param label: An optional label for the widget.
        :param name: The name for the TextBox.
        :param as_string: Use string with newline separator instead of a list
            for the value of this widget.
        :param on_change: Optional function to call when text changes.
        """
        super(TextBox, self).__init__(name)
        self._label = label
        self._line = 0
        self._column = 0
        self._start_line = 0
        self._start_column = 0
        self._required_height = height
        self._as_string = as_string
        self._on_change = on_change

    def update(self, frame_no):
        self._draw_label()

        # Calculate new visible limits if needed.
        width = self._w - self._offset
        height = self._h
        dx = dy = 0
        self._start_line = max(0, max(self._line - height + 1,
                                      min(self._start_line, self._line)))
        self._start_column = max(0, max(self._column - width + 1,
                                        min(self._start_column, self._column)))

        # Clear out the existing box content
        (colour, attr, bg) = self._pick_colours("edit_text")
        for i in range(height):
            self._frame.canvas.print_at(
                " " * width,
                self._x + self._offset + dx,
                self._y + i + dy,
                colour, attr, bg)

        # Render visible portion of the text.
        for i, text in enumerate(self._value):
            if self._start_line <= i < self._start_line + height:
                self._frame.canvas.print_at(
                    text[self._start_column:self._start_column + width],
                    self._x + self._offset + dx,
                    self._y + i + dy - self._start_line,
                    colour, attr, bg)

        # Since we switch off the standard cursor, we need to emulate our own
        # if we have the input focus.
        if self._has_focus:
            self._draw_cursor(
                " " if self._column >= len(self._value[self._line]) else
                self._value[self._line][self._column],
                frame_no,
                self._x + self._offset + self._column + dx - self._start_column,
                self._y + self._line + dy - self._start_line)

    def reset(self):
        # Reset to original data and move to end of the text.
        self._line = len(self._value) - 1
        self._column = len(self._value[self._line])

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
            if old_value != self._value and self._on_change:
                self._on_change()

        elif isinstance(event, MouseEvent):
            # Mouse event - rebase coordinates to Frame context.
            new_event = self._frame.rebase_event(event)
            if event.buttons != 0:
                if self.is_mouse_over(new_event, include_label=False):
                    self._line = max(0,
                                     new_event.y - self._y + self._start_line)
                    self._line = min(len(self._value) - 1, self._line)
                    self._column = min(
                        len(self._value[self._line]),
                        new_event.x - self._x - self._offset +
                        self._start_column)
                    self._column = max(0, self._column)
                    return
            # Ignore other mouse events.
            return event
        else:
            # Ignore other events
            return event

    def required_height(self, offset, width):
        return self._required_height

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

    def __init__(self, height, options, titles=None, label=None, name=None, on_change=None):
        """
        :param height: The required number of input lines for this widget.
        :param options: The options for each row in the widget.
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        :param on_change: Optional function to call when selection changes.
        """
        super(_BaseListBox, self).__init__(name)
        self._options = options
        self._titles = titles
        self._label = label
        self._line = 0
        self._start_line = 0
        self._required_height = height
        self._on_change = on_change

    def reset(self):
        # Reset selection - use value to trigger on_select
        if len(self._options) > 0:
            self._line = 0
            self.value = self._options[self._line][1]
        else:
            self._line = -1
            self.value = None

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
            else:
                # Ignore any other key press.
                return event
        elif isinstance(event, MouseEvent):
            # Mouse event - rebase coordinates to Frame context.
            new_event = self._frame.rebase_event(event)
            if event.buttons != 0:
                if (len(self._options) > 0 and
                        self.is_mouse_over(new_event, include_label=False)):
                    # Use property to trigger events.
                    self._line = min(new_event.y - self._y,
                                     len(self._options) - 1) + self._start_line
                    if self._titles and self._line > 0:
                        self._line -= 1
                    self.value = self._options[self._line][1]
                    return
            # Ignore other mouse events.
            return event
        else:
            # Ignore other events
            return event

    def required_height(self, offset, width):
        return self._required_height

    @property
    def start_line(self):
        """
        The line that will be drawn at the top of the visible section of this
        list.
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
        # Only trigger notification after we've changed selection
        old_value = self._value
        self._value = new_value
        for i, [_, value] in enumerate(self._options):
            if value == new_value:
                self._line = i
                break
        else:
            self._value = None
            self._line = -1
        if old_value != self._value and self._on_change:
            self._on_change()

    @property
    def options(self):
        """
        The list of options available for user selection - this is a list of
        tuples (<human readable string>, <internal value>).
        """
        return self._options

    @options.setter
    def options(self, new_value):
        self._options = new_value
        self.value = self._options[0][1] if len(self._options) > 0 else None


class ListBox(_BaseListBox):
    """
    A ListBox is a simple widget for displaying a list of options from which
    the user can select one option.
    """

    def __init__(self, height, options, label=None, name=None, on_change=None):
        """
        :param height: The required number of input lines for this ListBox.
        :param options: The options for each row in the widget.
        :param label: An optional label for the widget.
        :param name: The name for the ListBox.
        :param on_change: Optional function to call when selection changes.

        The `options` are a list of tuples, where the first value is the string
        to be displayed to the user and the second is an interval value to
        identify the entry to the program.  For example:

            options=[
                ("First option", 1),
                ("Second option", 2)
            ]
        """
        super(ListBox, self).__init__(
                height, options, label=label, name=name, on_change=on_change)

    def update(self, frame_no):
        self._draw_label()

        # Calculate new visible limits if needed.
        width = self._w - self._offset
        height = self._h
        dx = dy = 0

        # Clear out the existing box content
        (colour, attr, bg) = self._frame.palette["field"]
        for i in range(height):
            self._frame.canvas.print_at(
                " " * width,
                self._x + self._offset + dx,
                self._y + i + dy,
                colour, attr, bg)

        # Don't bother with anything else if there are no options to render.
        if len(self._options) <= 0:
            return

        # Render visible portion of the text.
        self._start_line = max(0, max(self._line - height + 1,
                                      min(self._start_line, self._line)))
        for i, (text, _) in enumerate(self._options):
            if self._start_line <= i < self._start_line + height:
                colour, attr, bg = self._pick_colours("field", i == self._line)
                self._frame.canvas.print_at(
                    "{:{width}}".format(text, width=width),
                    self._x + self._offset + dx,
                    self._y + i + dy - self._start_line,
                    colour, attr, bg)


class MultiColumnListBox(_BaseListBox):
    """
    A MultiColumnListBox is a widget for displaying a set of related data in
    columns, from which the user can select a line.
    """

    def __init__(self, height, columns, options, titles=None, label=None,
                 name=None, on_change=None):
        """
        :param height: The required number of input lines for this ListBox.
        :param columns: A list of widths and alignments for each column.
        :param options: The options for each row in the widget.
        :param titles: Optional list of titles for each column.  Must match
            the length of `columns`.
        :param label: An optional label for the widget.
        :param name: The name for the ListBox.
        :param on_change: Optional function to call when selection changes.

        The `columns` parameter is a list of integers or strings.  If it is an
        integer, this is the absolute width of the column in characters.  If it
        is a string, it must be of the format "[<align>]<width>[%]", where

        * <align> is the alignment string ("<" = left, ">" = right,
          "^" = centre)
        * <width> is the width in characters
        * % is an optional qualifier that says the number is a percentage of
          the width of the widget.

        Column widths need to encompass any space required between columns, so
        for example, if your column is 5 characters, allow 6 for an extra space
        at the end.  It is not possible to do this when you have a
        right-justified column next to a left-justified column, so this widget
        will automatically space them for you.

        The number of columns is for this widget is determined from the number
        of entries in the `columns` parameter.  The `options` list is then a
        list of tuples of the form ([val1, val2, ... , valn], index).  For
        example, this data provides 2 rows for a 3 column widget:

            options=[
                (["One", "row", "here"], 1),
                (["Second", "row", "here"], 2)
            ]

        The options list may be None and then can be set later using the
        `options` property on this widget.
        """
        super(MultiColumnListBox, self).__init__(
            height, options, titles=titles, label=label, name=name, on_change=on_change)
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

    def update(self, frame_no):
        self._draw_label()

        # Calculate new visible limits if needed.
        width = self._w - self._offset
        height = self._h
        dx = dy = 0

        # Clear out the existing box content
        (colour, attr, bg) = self._frame.palette["field"]
        for i in range(height):
            self._frame.canvas.print_at(
                " " * width,
                self._x + self._offset + dx,
                self._y + i + dy,
                colour, attr, bg)

        # Don't bother with anything else if there are no options to render.
        if len(self._options) <= 0:
            return

        # Allow space for titles if needed.
        if self._titles:
            dy += 1
            height -= 1
            row_dx = 0
            colour, attr, bg = self._frame.palette["title"]
            for i, [title, align, space] in enumerate(
                    zip(self._titles, self._align, self._spacing)):
                width = self._columns[i]
                if isinstance(width, float):
                    width = int(self._w * width)
                self._frame.canvas.print_at(
                    "{}{:{}{}}".format(" " * space, title, align, width),
                    self._x + self._offset + row_dx,
                    self._y,
                    colour, attr, bg)
                row_dx += width + space

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
                    if isinstance(width, float):
                        width = int(self._w * width)
                    if len(text) >= width:
                        text = text[:width - 3] + "..."
                    self._frame.canvas.print_at(
                        "{}{:{}{}}".format(" " * space, text, align, width),
                        self._x + self._offset + dx + row_dx,
                        self._y + i + dy - self._start_line,
                        colour, attr, bg)
                    row_dx += width + space


class Button(Widget):
    """
    A Button widget to be  displayed in a Frame.  It is typically used to
    represent a desired action for te user to invoke (e.g. a submit button on
    a form).
    """

    def __init__(self, text, on_click, label=None):
        """
        :param text: The text for the button.
        :param on_click: The function to invoke when the button is clicked.
        :param label: An optional label for the widget.
        """
        super(Button, self).__init__(None)
        # We nly ever draw the button with borders, so calculate that once now.
        self._text = "< {} >".format(text)
        self._on_click = on_click
        self._label = label

    def set_layout(self, x, y, offset, w, h):
        # Do the usual layout work. then recalculate exact x/w values for the
        # rendered button.
        super(Button, self).set_layout(x, y, offset, w, h)
        self._x += max(0, (self._w - self._offset - len(self._text)) // 2)
        self._w = min(self._w, len(self._text))

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
                return
            else:
                # Ignore any other key press.
                return event
        elif isinstance(event, MouseEvent):
            new_event = self._frame.rebase_event(event)
            if event.buttons != 0:
                if (self._x <= new_event.x < self._x + self._w and
                        self._y <= new_event.y < self._y + self._h):
                    self._on_click()
                    return
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
    A fixed implementation Frame that simply provides a standard message box
    dialog.
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
        :param on_close: Optional function to invoke on exit.  This MUST be a
            static method to work across screen resizing.
        :param has_shadow: optional flag to specify if dialog should have a
            shadow when drawn.

        The `on_close` method (if specified) will be called with one integer
        parameter that corresponds to the index of the button passed in the
        array of available `buttons`.
        """
        # Enforce API requirements
        assert on_close is None or type(on_close) == FunctionType, \
            "on_close must be a static fn"

        # Remember parameters for cloning.
        self._text = text
        self._buttons = buttons
        self._on_close = on_close

        # Decide on optimum width of the dialog.  Limit to 2/3 the screen width.
        width = max([len(x) for x in text.split("\n")])
        width = max(width + 4,
                    sum([len(x) + 4 for x in buttons]) + len(buttons) + 5)
        width = min(width, screen.width * 2 // 3)

        # Figure out the necessary message and allow for buttons and borders
        # when deciding on height.
        self._message = _split_text(text, width, screen.height - 4)
        height = len(self._message) + 4

        # Construct the Frame
        self._data = {"message": self._message}
        super(PopUpDialog, self).__init__(
            screen, height, width, self._data, has_shadow=has_shadow)

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

    def process_event(self, event):
        # Only allow this effect to handle events.
        super(PopUpDialog, self).process_event(event)
        return None

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
        # Just create the same dialog in the new Screen/Scene objects.
        scene.add_effect(
            PopUpDialog(screen, self._text, self._buttons, self._on_close))
