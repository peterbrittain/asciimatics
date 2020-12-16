"""This module implements the displaying of widgets appropriately"""
from wcwidth import wcswidth
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.exceptions import Highlander, InvalidFields
from asciimatics.screen import Screen
from asciimatics.utilities import _DotDict
from asciimatics.widgets.utilities import _euclidian_distance, logger
from asciimatics.widgets.widget import Widget

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

    __slots__ = ["_column_sizes", "_columns", "_frame", "_has_focus", "_live_col", "_live_widget",
                 "_fill_frame"]

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

        If you are adding this Widget to the Layout dynamically after starting to play the Scene,
        don't forget to ensure that the value is explicitly set before the next update.

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

    def clear_widgets(self):
        """
        Clear all widgets from this Layout.

        This method allows users of the Layout to dynamically recreate a new Layout.  After calling
        this method, you can add new widgetsback into the Layout and then need to call `fix` to
        force the Frame to recalculate the resulting new overall layout.
        """
        self._columns = [[] for _ in self._columns]

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

    def get_current_widget(self):
        """
        Return the current widget with the focus, or None if there isn't one.
        """
        return self._columns[self._live_col][self._live_widget] if self._has_focus else None

    def get_nearest_widget(self, target_widget, direction):
        """
        Find the nearest enabled widget to the specified target widget, bearing in mind the direction of travel.

        Direction of travel is defined to be the movement from current Layout to next.  This is important for the
        case where we wrap back to the beginning or end of the Layouts - and so should still only look for the
        widgets nearest the top/bottom (depending on direction of travel).

        This function may return None if there is no match (e.g. all widgets are disabled).

        :param target_widget: the target widget to match.
        :param direction: The direction of travel across Layouts.
        """
        best_distance = 999999999
        match = None
        for i, column in enumerate(self._columns):
            indexed_column = list(enumerate(column))
            if direction < 0:
                indexed_column = reversed(indexed_column)
            # Force this to be a list for python 2/3 compatibility.
            live_widgets = [x for x in filter(lambda x: x[1].is_tab_stop and not x[1].disabled, indexed_column)]
            try:
                j, candidate = live_widgets[0]
                new_distance = _euclidian_distance(target_widget, candidate)
                if new_distance < best_distance:
                    best_distance = new_distance
                    match = candidate, i, j
            except IndexError:
                pass
        return match

    def _find_nearest_horizontal_widget(self, direction):
        """
        Find the nearest widget to the left or right of the current widget with the focus.

        :param direction: The direction to move through the columns.
        """
        current_col = self._live_col
        current_widget = self._columns[self._live_col][self._live_widget]
        while True:
            current_col += direction
            # Check if we need to wrap back to the beginning or end of the columns.
            if current_col >= len(self._columns):
                current_col = 0
            if current_col < 0:
                current_col = len(self._columns) - 1
            # Check if we've got back where we started - if so we had no match and we're done.
            if self._live_col == current_col:
                return
            # OK - we're still looking.  FInd the closest live widget.
            live_widgets = filter(lambda x: x[1].is_tab_stop and not x[1].disabled,
                                  enumerate(self._columns[current_col]))
            best_distance = 999999999
            best_index = -1
            for index, widget in live_widgets:
                self._live_col = current_col
                # An exact match on line (i.e. same Y value) trumps any closest distance.  Break out now if we find
                # a match that way.
                if widget.get_location()[1] == current_widget.get_location()[1]:
                    self._live_col = current_col
                    self._live_widget = index
                    return
                new_distance = _euclidian_distance(current_widget, widget)
                if new_distance < best_distance:
                    best_distance = new_distance
                    best_index = index
            if best_index >= 0:
                self._live_col = current_col
                self._live_widget = best_index
                return

    def _find_next_widget(self, direction, stay_in_col=False):
        """
        Find the next widget to get the focus, following TAB logic

        :param direction: The direction to move through the widgets.
        :param stay_in_col: Whether to limit search to current column.  (Used for up/down in columns).
        """
        current_widget = self._live_widget
        current_col = self._live_col
        while 0 <= self._live_col < len(self._columns):
            self._live_widget += direction
            while 0 <= self._live_widget < len(self._columns[self._live_col]):
                widget = self._columns[self._live_col][self._live_widget]
                if widget.is_tab_stop and not widget.disabled:
                    return
                self._live_widget += direction
            if stay_in_col:
                break
            else:
                self._live_col += direction
                self._live_widget = -1 if direction > 0 else len(self._columns[self._live_col])
                if self._live_col == current_col:
                    break

        # We've exhausted our search - give up and stay where we were.
        self._live_widget = current_widget

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
                    self._find_nearest_horizontal_widget(-1)
                    self._columns[self._live_col][self._live_widget].focus()
                    event = None
                elif event.key_code == Screen.KEY_RIGHT:
                    # Move on to first widget in the next column.
                    self._columns[self._live_col][self._live_widget].blur()
                    self._find_nearest_horizontal_widget(1)
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
                # Don't bother with invisible widgets
                if widget.is_visible:
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
                logger.debug("Updating: %s", widget.name)
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

    def enable(self, columns=None):
        """
        Enable all widgets in the specified columns of  this Layout.

        :param columns: The list of columns to enable.  Defaults to all columns.
        """
        # Enable all widgets in required columns.
        for column in columns if columns else range(len(self._columns)):
            for widget in self._columns[column]:
                widget.disabled = False

    def disable(self, columns=None):
        """
        Disable all widgets in the specified columns of  this Layout.

        :param columns: The list of columns to disable.  Defaults to all columns.
        """
        # Disable all widgets in required columns.
        for column in columns if columns else range(len(self._columns)):
            for widget in self._columns[column]:
                widget.disabled = True

        # Update focus if needed.
        if columns is None or self._live_col in columns:
            self._find_next_widget(1)

