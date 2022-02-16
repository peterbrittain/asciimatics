# -*- coding: utf-8 -*-
"""This module defines a class to display widgets"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from builtins import range
from copy import copy, deepcopy
from logging import getLogger
from wcwidth import wcswidth
from asciimatics.effects import Effect
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.exceptions import Highlander, InvalidFields
from asciimatics.screen import Screen, Canvas
from asciimatics.utilities import BoxTool
from asciimatics.widgets.scrollbar import _ScrollBar
from asciimatics.widgets.utilities import THEMES

# Logging
logger = getLogger(__name__)


class _BorderManager:
    def __init__(self, frame, has_border, can_scroll):
        """
        Helper class to manage the border and scroll bar attached to a frame.
        Allows for different character to be used in the border and the
        changes in sizing requirements with borders on and off with scroll
        bars on and off.

        :param frame: frame being manager
        :param has_border: True if the frame has a border
        :param can_scroll: True if the frame has a scroll bar
        """
        self._frame = frame
        self.has_border = has_border
        self.scroll_bar = None
        self.box = BoxTool(frame.canvas.unicode_aware)
        if can_scroll:
            scroll_y = 2
            scroll_height = frame.canvas.height - 4
            if not has_border:
                scroll_height = frame.canvas.height - 2
                scroll_y = 1

            self.scroll_bar = _ScrollBar(
                frame.canvas, frame.palette, frame.canvas.width - 1, scroll_y, scroll_height, 
                frame.get_scroll_pos, frame.set_scroll_pos, absolute=True
            )

        # Optimization for non-unicode displays to avoid slow unicode calls.
        self.string_len = wcswidth if frame._canvas.unicode_aware else len

    @property
    def can_scroll(self):
        return self.scroll_bar is not None

    def get_rectangle(self):
        """
        Returns the bounding box defined by the usable space left after
        borders and/or scroll bars are accounted for.

        :returns: Tuple containing, x, y, height and width of bounding box
        """
        if self.has_border:
            x = 1
            y = self._frame.canvas.start_line + 1

            h = self._frame.canvas.height - 2
            w = self._frame.canvas.width - 2
        else:
            x = 0
            y = self._frame.canvas.start_line
            h = self._frame.canvas.height
            w = self._frame.canvas.width

            if self.can_scroll:
                w -= 1

        return x, y, h, w

    def draw(self):
        """
        Draws the border and/or scroll bars onto the frame managed by this
        object.
        """
        frame = self._frame

        if self.has_border:
            # Draw the basic border first.
            (colour, attr, bg) = frame.palette["borders"]
            for dy in range(frame.canvas.height):
                y = frame.canvas.start_line + dy
                if dy == 0:
                    frame.canvas.print_at(
                        self.box.box_top(frame.canvas.width), 0, y, colour, attr, bg
                    )
                elif dy == frame.canvas.height - 1:
                    frame.canvas.print_at(
                        self.box.box_bottom(frame.canvas.width), 0, y, colour, attr, bg
                    )
                else:
                    frame.canvas.print_at(self.box.v, 0, y, colour, attr, bg)
                    frame.canvas.print_at(self.box.v, frame.canvas.width - 1, y, colour, attr, bg)

            # Now the title
            (colour, attr, bg) = frame.palette["title"]
            title_width = self.string_len(frame.title)
            frame.canvas.print_at(
                frame.title, (frame.canvas.width - title_width) // 2, frame.canvas.start_line, 
                colour, attr, bg
            )

        if self.can_scroll and frame.canvas.height > 5:
            self.scroll_bar.update()


class Frame(Effect):
    """
    A Frame is a special Effect for controlling and displaying Widgets.

    It is similar to a window as used in native GUI applications.  Widgets are text UI elements
    that can be used to create an interactive application within your Frame.
    """

    #: Colour palette for the widgets within the Frame.  Each entry should be
    #: a 3-tuple of (foreground colour, attribute, background colour).
    palette = {}

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
        :param has_border: Whether the frame has a border box. Defaults to True.
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
        """
        super(Frame, self).__init__(screen)
        self._focus = 0
        self._max_height = 0
        self._layouts = []
        self._effects = []
        self._canvas = Canvas(screen, height, width, x, y)
        self._data = None
        self._on_load = on_load
        self._hover_focus = hover_focus
        self._initial_data = data if data else {}
        self._title = None
        self.title = title  # Use property to re-format text as required.
        self._has_shadow = has_shadow
        self._reduce_cpu = reduce_cpu
        self._is_modal = is_modal
        self._has_focus = False
        self._border_mgr = _BorderManager(self, has_border, can_scroll)

        # A unique name is needed for cloning.  Try our best to get one!
        self._name = title if name is None else name

        # Flag to catch recursive calls inside the data setting.  This is
        # typically caused by callbacks subsequently trying to re-use functions.
        self._in_call = False

        # Now set up any passed data - use the public property to trigger any
        # necessary updates.
        self.data = deepcopy(self._initial_data)

        # Ensure that we have the default palette in place
        self._theme = None
        self.set_theme("default")

    def get_scroll_pos(self):
        """
        Get current position for scroll bar.
        """
        if self._canvas.height >= self._max_height:
            return 0
        return self._canvas.start_line / (self._max_height - self._canvas.height + 1)

    def set_scroll_pos(self, pos):
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
        # Remove any focus now before we reset...
        if self._has_focus:
            try:
                self._layouts[self._focus].blur()
            except IndexError:
                pass

        # Do up to 2 passes in case we have a variable height Layout.
        fill_layout = None
        fill_height = y = 0
        for _ in range(2):
            # Pick starting point/height - varies for borders.
            x, y, height, width = self._border_mgr.get_rectangle()
            start_y = y

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

            # Can stop now if no fill required.
            if fill_layout is None:
                break

            # We hit a variable height Layout - figure out the available space and reset everything
            # to the new values.
            fill_height = max(1, start_y + height - y)

        # Remember the resulting height of the underlying Layouts.
        self._max_height = y

        # Reset text
        if self._has_focus:
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
        self._border_mgr.draw()

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
        if theme in THEMES:
            self._theme = theme
            self.palette = THEMES[theme]
            if self._border_mgr.can_scroll:
                self._border_mgr.scroll_bar.palette = self.palette

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
            return layout.get_current_widget()
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

    @property
    def border_box(self):
        """
        Instance of :class:`~asciimatics.utilities.BoxTool` that specifies the characters used to
        draw the border to this frame. You can change the border character style by modifying the
        :attr:`style` property on this object. Allowed styles are defined in
        :mod:`~asciimatics.constants`.

        """
        return self._border_mgr.box

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
                    # Using protected access to our own class type on purpose.
                    # pylint: disable=protected-access
                    logger.debug("Cloning: %s", effect._name)
                    if effect._name == self._name:
                        effect.set_theme(self._theme)
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
        start_x, start_y, height, width = self._border_mgr.get_rectangle()

        if ((start_x <= x < start_x + width) and (y >= start_y) and (y + h < start_y + height)):
            # Already OK - quit now.
            return

        if y < start_y:
            self._canvas.scroll_to(y - 1 if self._border_mgr.has_border else y)
        else:
            line = y + h - self._canvas.height + (1 if self._border_mgr.has_border else 0)
            self._canvas.scroll_to(max(0, line))

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

    def _find_next_tab_stop(self, direction):
        old_focus = self._focus
        self._focus += direction
        while self._focus != old_focus:
            if self._focus < 0:
                self._focus = len(self._layouts) - 1
            if self._focus >= len(self._layouts):
                self._focus = 0
            try:
                if direction > 0:
                    self._layouts[self._focus].focus(force_first=True)
                else:
                    self._layouts[self._focus].focus(force_last=True)
                break
            except IndexError:
                self._focus += direction

    def _switch_to_nearest_vertical_widget(self, direction):
        """
        Find the nearest widget above or below the current widget with the focus.

        This should only be called by the Frame when normal Layout navigation fails and so this needs to find
        the nearest widget in the next available Layout.  It will not search the existing Layout for a closer
        match.

        :param direction: The direction to move through the Layouts.
        """
        current_widget = self._layouts[self._focus].get_current_widget()
        focus = self._focus
        focus += direction
        while self._focus != focus:
            if focus < 0:
                focus = len(self._layouts) - 1
            if focus >= len(self._layouts):
                focus = 0
            match = self._layouts[focus].get_nearest_widget(current_widget, direction)
            if match:
                self.switch_focus(self._layouts[focus], match[1], match[2])
                return
            focus += direction

    def process_event(self, event):
        # Rebase any mouse events into Frame coordinates now.
        old_event = event
        event = self.rebase_event(event)

        # Claim the input focus if a mouse clicked on this Frame.
        claimed_focus = False
        if isinstance(event, MouseEvent) and event.buttons > 0:
            if (0 <= event.x < self._canvas.width and
                    self._canvas.start_line <= event.y < self._canvas.start_line + self._canvas.height):
                self._scene.remove_effect(self)
                self._scene.add_effect(self, reset=False)
                # No need to set focus - mouse event processing later will do that.
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
                # calculated when taking the focus - or is modal.
                return None if claimed_focus or self._is_modal else old_event

        # Give the current widget in focus first chance to process the event.
        event = self._layouts[self._focus].process_event(event, self._hover_focus)
        logger.debug("Current widget left event: %s", event)

        # If the underlying widgets did not process the event, try processing
        # it now.
        if event is not None:
            if isinstance(event, KeyboardEvent):
                if event.key_code == Screen.KEY_TAB:
                    # Move on to next widget.
                    self._layouts[self._focus].blur()
                    self._find_next_tab_stop(1)
                    # Find next tab stop will have already set the new focus.
                    old_event = None
                elif event.key_code == Screen.KEY_BACK_TAB:
                    # Move on to previous widget.
                    self._layouts[self._focus].blur()
                    self._find_next_tab_stop(-1)
                    # Find next tab stop will have already set the new focus.
                    old_event = None
                if event.key_code == Screen.KEY_DOWN:
                    # Move on to nearest vertical widget in the next Layout
                    self._switch_to_nearest_vertical_widget(1)
                    old_event = None
                elif event.key_code == Screen.KEY_UP:
                    # Move on to nearest vertical widget in the next Layout
                    self._switch_to_nearest_vertical_widget(-1)
                    old_event = None
            elif isinstance(event, MouseEvent):
                # Give layouts/widgets first dibs on the mouse message.
                for layout in self._layouts:
                    if layout.process_event(event, self._hover_focus) is None:
                        return None

                # If no joy, check whether the scroll bar was clicked.
                if self._border_mgr.can_scroll:
                    if self._border_mgr.scroll_bar.process_event(event):
                        return None

        # Don't allow events to bubble down if this window owns the Screen (as already
        # calculated when taking the focus) or if the Frame is modal or we handled the
        # event.
        return None if claimed_focus or self._is_modal or event is None else old_event
