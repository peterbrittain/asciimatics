from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from builtins import object
from copy import copy
from future.utils import with_metaclass
from abc import ABCMeta, abstractmethod
from asciimatics.effects import Effect
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.renderers import Box
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
        if len(current_line + token) > width:
            result.append(current_line.rstrip())
            current_line = token
        else:
            current_line += token + " "
    else:
        result.append(current_line.rstrip())

    # Check for a height overrun and truncate.
    if len(result) > height:
        result = result[:height]
        result[height - 1] = result[height - 1][:width-3] + "..."

    # Very small columns could be shorter than individual words - truncate
    # each line if necessary.
    for i, line in enumerate(result):
        if len(line) > width:
            result[i] = line[:width-3] + "..."
    return result


class Frame(Effect):
    """
    A Frame is a special Effect for controlling and displaying Widgets.  Widgets
    are GUI elements that can be used to create an application.
    """

    # Colour palette for the widgets within the Frame.
    palette = {
        "background":
            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "disabled":
            (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "label":
            (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "borders":
            (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLUE),
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

    def __init__(self, screen, height, width, data=None, on_load=None):
        """
        :param screen: The Screen that owns this Frame.
        :param width: The desired width of the Frame.
        :param height: The desired height of the Frame.
        :param data: optional data dict to initialize any widgets in the frame.
        :param on_load: optional function to call whenever the Frame reloads.
        """
        super(Frame, self).__init__()
        self._focus = 0
        self._layouts = []
        self._canvas = Canvas(screen, height, width)
        self._data = None
        self.data = data
        self._on_load = on_load

    def add_layout(self, layout):
        """
        Add a Layout to the Frame.

        :param layout: The Layout to be added.
        """
        layout.register_frame(self)
        self._layouts.append(layout)

    def fix(self):
        """
        Fix the layouts and calculate the locations of all the widgets.  This
        should be called once all Layouts have been added to the Frame and all
        widgets added to the Layouts.
        """
        y = 0
        for layout in self._layouts:
            y = layout.fix(y)
        self._layouts[self._focus].focus(force_first=True)
        self._clear()

    def _clear(self):
        """
        Clear the current canvas.
        """
        # It's orders of magnitude faster to reset with a print like this
        # instead of recreating the screen buffers.
        (colour, attr, bg) = self.palette["background"]
        # TODO: Fix internal use of buffer height.
        for y in range(self._canvas._buffer_height):
            self._canvas.print_at(
                " " * self._canvas.width, 0, y, colour, attr, bg)

    def _update(self, frame_no):
        # Update all the widgets and then push to the screen.
        for layout in self._layouts:
            layout.update(frame_no)
        self._canvas.refresh()
        self._clear()

    @property
    def data(self):
        """
        Data dictionary containing values from the contained widgets.
        """
        # Make sure we have an up-to-date copy.
        # TODO: Fix this if needed.
        # self.save()
        return self._data

    @data.setter
    def data(self, new_value):
        # Do a key-by-key copy to allow for dictionary-like objects - e.g.
        # sqlite3 Row class.
        self._data = {}
        if new_value is not None:
            for key in new_value.keys():
                self._data[key] = new_value[key]

        # Now update any widgets as needed.
        for layout in self._layouts:
            layout.update_widgets()

    @property
    def stop_frame(self):
        # Widgets have no defined end - always return -1.
        return -1

    @property
    def canvas(self):
        """
        The Canvas that backs this Frame.
        """
        return self._canvas

    def reset(self):
        # Now reset the individual widgets.
        self._canvas.reset()
        for layout in self._layouts:
            layout.reset()
            layout.blur()

        # Set up active widget.
        self._focus = 0
        self._layouts[self._focus].focus(force_first=True)

        # Call the on_load function now if specified.
        if self._on_load is not None:
            self._on_load()

    def save(self):
        """
        Save the current values in all the widgets back to the persistent data
        storage.
        """
        for layout in self._layouts:
            layout.save()

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

    def process_event(self, event):
        # Give the current widget in focus first chance to process the event.
        event = self._layouts[self._focus].process_event(event)

        # If the underlying widgets did not process the event, try processing
        # it now.
        if event is not None:
            if isinstance(event, KeyboardEvent):
                if event.key_code in [Screen.KEY_TAB, Screen.KEY_DOWN]:
                    # Move on to next widget.
                    self._layouts[self._focus].blur()
                    self._focus += 1
                    if self._focus >= len(self._layouts):
                        self._focus = 0
                    self._layouts[self._focus].focus(force_first=True)
                    event = None
                elif event.key_code in [Screen.KEY_BACK_TAB, Screen.KEY_UP]:
                    # Move on to previous widget.
                    self._layouts[self._focus].blur()
                    self._focus -= 1
                    if self._focus < 0:
                        self._focus = len(self._layouts) - 1
                    self._layouts[self._focus].focus(force_last=True)
                    event = None
            elif isinstance(event, MouseEvent):
                for layout in self._layouts:
                    if layout.process_event(event) is None:
                        return
        return event


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

    def __init__(self, columns):
        """
        :param columns: A list of numbers specifying the width of each column
                        in this layout.

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

        The force_column and force_widget parameters must both be set or unset
        together.
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
        Call this to give take the input focus from this Layout.
        """
        self._has_focus = False
        self._columns[self._live_col][self._live_widget].blur()

    def fix(self, start_y):
        """
        Fix the location and size of all the Widgets in this Layout.

        :param start_y: The start line for the Layout.
        :returns: The next line to be used for any further Layouts.
        """
        x = 0
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
                         self._frame.canvas.width * self._column_sizes[i] // 3))

            # Now go through each widget getting them to resize to the required
            # width and label offset.
            y = start_y
            w = int(self._frame.canvas.width * self._column_sizes[i])
            for widget in column:
                h = widget.required_height(offset, w)
                widget.set_layout(x, y, offset, w, h)
                y += h
            max_y = max(max_y, y)
            x += w
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

    def process_event(self, event):
        """
        Process any input event.

        :param event: The event that was triggered.
        :returns: None if the Effect processed the event, else the original
                  event.
        """
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
                    self._columns[self._live_col][self._live_widget].blur()
                    self._find_next_widget(1, stay_in_col=True)
                    self._columns[self._live_col][self._live_widget].focus()
                    event = None
                elif event.key_code == Screen.KEY_UP:
                    # Move on to previous widget, unless it is the first in the
                    # Layout.
                    self._columns[self._live_col][self._live_widget].blur()
                    self._find_next_widget(-1, stay_in_col=True)
                    self._columns[self._live_col][self._live_widget].focus()
                    event = None
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
                # TODO: convert to formal function.  Also consider rebasing all mouse events.
                new_event = copy(event)
                new_event.x -= self._frame._canvas._dx
                new_event.y -= self._frame._canvas._dy - self._frame._canvas._start_line
                if event.buttons >= 0:
                    # Mouse click - look to move focus.
                    for i, column in enumerate(self._columns):
                        for j, widget in enumerate(column):
                            # TODO: Formalise this test as API.
                            if (widget._x <= new_event.x < widget._x + widget._w and
                                    widget._y <= new_event.y < widget._y + widget._h):
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

    def save(self):
        """
        Save the current values in all the widgets back to the persistent data
        storage.
        """
        for column in self._columns:
            for widget in column:
                if widget.name is not None:
                    # TODO: Fix this hack!
                    self._frame._data[widget.name] = widget.value

    def update_widgets(self):
        """
        Reset te values for any Widgets in this Layout based on the current
        Frame data store.
        """
        for column in self._columns:
            for widget in column:
                if widget.name in self._frame.data:
                    widget.value = self._frame.data[widget.name]
                else:
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

    def register_frame(self, frame):
        """
        Register the Frame that owns this Widget.
        :param frame: The owning Frame.
        """
        self._frame = frame

    def set_layout(self, x, y, offset, w, h):
        """
        Set the size and position of the Widget.

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
        if not self._frame.canvas.is_visible(self._x, self._y):
            if self._y < self._frame.canvas.start_line:
                self._frame.canvas.scroll_to(self._y)
            else:
                line = max(0, self._y - self._frame.canvas.height + self._h)
                self._frame.canvas.scroll_to(line)

    def blur(self):
        """
        Call this to give take the input focus from this Widget.
        """
        self._has_focus = False

    def _draw_label(self):
        """
        Draw the label for this widget if needed.
        """
        if self._label is not None:
            # Break the label up as required.
            if self._display_label is None:
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
        if frame_no % 10 < 5:
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

    @property
    def value(self):
        """
        The value to return for this widget based on the user's input.
        """
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

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
            self._frame.canvas.print_at("-" * self._w,
                                        self._x,
                                        self._y + (self._required_height // 2),
                                        colour, attr, bg)

    def reset(self):
        pass

    def required_height(self, offset, width):
        # Allow one line for text and a blank spacer before it.
        return self._required_height


class Text(Widget):
    """
    A Text widget is a single line input field.  It consists of an optional
    label and an entry box.
    """

    def __init__(self, label=None, name=None):
        """
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        """
        super(Text, self).__init__(name)
        self._label = label
        self._column = 0
        self._start_column = 0

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
        if self._value is None:
            self._value = ""
        self._column = len(self._value)

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code == Screen.KEY_BACK:
                if self._column > 0:
                    # Delete character in front of cursor.
                    self._value = "".join([
                        self._value[:self._column - 1],
                        self._value[self._column:]])
                    self._column -= 1
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
            elif 32 <= event.key_code < 256:
                # Insert any visible text at the current cursor position.
                self._value = chr(event.key_code).join([
                    self._value[:self._column],
                    self._value[self._column:]])
                self._column += 1
            else:
                # Ignore any other key press.
                return event
        elif isinstance(event, MouseEvent):
            # Mouse event - rebase coordinates to Frame context.
            # TODO: convert to formal function.  Also consider rebasing all mouse events.
            new_event = copy(event)
            new_event.x -= self._frame._canvas._dx
            new_event.y -= self._frame._canvas._dy - self._frame._canvas._start_line
            if event.buttons != 0:
                # Mouse click - move cursor.
                # TODO: Formalise this test as API.
                if (self._x <= new_event.x < self._x + self._w and
                        self._y <= new_event.y < self._y + self._h):
                    self._column = max(
                        0,
                        min(len(self._value),
                            new_event.x - self._x - self._offset + self._start_column))
                    return
            # Ignore other mouse events.
            return event
        else:
            # Ignore other events
            return event

    def required_height(self, offset, width):
        return 1


class CheckBox(Widget):
    """
    A CheckBox widget is used to ask for simple Boolean (i.e. yes/no) input.  It
    consists of an optional label (typically used for the first in a group of
    CheckBoxes), the box and a field name.
    """

    def __init__(self, text, label=None, name=None):
        """
        :param text: The text to explain this specific field to the user.
        :param label: An optional label for the widget.
        :param name: The internal name for the widget.
        """
        super(CheckBox, self).__init__(name)
        self._text = text
        self._label = label

    def update(self, frame_no):
        self._draw_label()

        # Render this checkbox.
        (colour, attr, bg) = self._pick_colours("control", self._has_focus)
        self._frame.canvas.print_at(
            "[{}] ".format("X" if self._value else " "),
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
                self._value = not self._value
            else:
                # Ignore any other key press.
                return event
        elif isinstance(event, MouseEvent):
            # Mouse event - rebase coordinates to Frame context.
            # TODO: convert to formal function.  Also consider rebasing all mouse events.
            new_event = copy(event)
            new_event.x -= self._frame._canvas._dx
            new_event.y -= self._frame._canvas._dy - self._frame._canvas._start_line
            if event.buttons != 0:
                # Mouse click - move cursor.
                # TODO: Formalise this test as API.
                if (self._x <= new_event.x < self._x + self._w and
                        self._y <= new_event.y < self._y + self._h):
                    self._value = not self._value
                    return
            # Ignore other mouse events.
            return event
        else:
            # Ignore other events
            return event

    def required_height(self, offset, width):
        return 1


class RadioButtons(Widget):
    """
    A RadioButtons widget is used to ask for one of a list of values to be
    selected by the user. It consists of an optional label and then a list of
    selection bullets with field names.
    """

    def __init__(self, options, label=None, name=None):
        """
        :param options: A list of (text, value) tuples for each radio button.
        :param label: An optional label for the widget.
        :param name: The internal name for the widget.
        """
        super(RadioButtons, self).__init__(name)
        self._options = options
        self._label = label
        self._selection = 0
        self._start_column = 0

    def update(self, frame_no):
        self._draw_label()

        # Render the list of radio buttons.
        for i, (text, _) in enumerate(self._options):
            fg, attr, bg = self._pick_colours("control", i == self._selection)
            fg2, attr2, bg2 = self._pick_colours("field", i == self._selection)
            check = "X" if i == self._selection else " "
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
        for i, (_, value) in enumerate(self._options):
            if self._value == value:
                self._selection = i
                break
        else:
            self._selection = 0

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            # Don't swallow keys if at limits of the list.
            if event.key_code == Screen.KEY_UP and self._selection > 0:
                self._selection -= 1
                self._value = self._options[self._selection][1]
            elif (event.key_code == Screen.KEY_DOWN and
                    self._selection < len(self._options) - 1):
                self._selection += 1
                self._value = self._options[self._selection][1]
            else:
                # Ignore any other key press.
                return event
        elif isinstance(event, MouseEvent):
            # Mouse event - rebase coordinates to Frame context.
            # TODO: convert to formal function.  Also consider rebasing all mouse events.
            new_event = copy(event)
            new_event.x -= self._frame._canvas._dx
            new_event.y -= self._frame._canvas._dy - self._frame._canvas._start_line
            if event.buttons != 0:
                # Mouse click - move cursor.
                # TODO: Formalise this test as API.
                if (self._x <= new_event.x < self._x + self._w and
                        self._y <= new_event.y < self._y + self._h):
                    self._selection = new_event.y - self._y
                    self._value = self._options[self._selection][1]
                    return
            # Ignore other mouse events.
            return event
        else:
            # Ignore non-keyboard events
            return event

    def required_height(self, offset, width):
        return len(self._options)


class TextBox(Widget):
    """
    A TextBox is a simple widget for recording and displaying the text that has
    been typed into it (when it has the focus).  It consists of a simple
    framed box with option label.  It can take multi-line input.
    """

    def __init__(self, height, label=None, name=None, as_string=False):
        """
        :param height: The required number of input lines for this TextBox.
        :param label: An optional label for the widget.
        :param name: The name for the TextBox.
        :param as_string: Use "\n" separated string instead of a list for the
            value of this widget.
        """
        super(TextBox, self).__init__(name)
        self._label = label
        self._line = 0
        self._column = 0
        self._start_line = 0
        self._start_column = 0
        self._required_height = height
        self._as_string = as_string
        # TODO: Fix up logic to either make edit fields have boxes that merge, or just delete this code.
        self._add_border = False

    def update(self, frame_no):
        self._draw_label()

        # Calculate new visible limits if needed.
        width = self._w - self._offset
        height = self._h
        dx = dy = 0
        if self._add_border:
            height -= 2
            width -= 2
            dx = dy = 1
        self._start_line = max(0, max(self._line - height + 1,
                                      min(self._start_line, self._line)))
        self._start_column = max(0, max(self._column - width + 1,
                                        min(self._start_column, self._column)))

        # Redraw the box frame if needed.
        if self._add_border:
            (colour, attr, bg) = self._frame.palette["borders"]
            box = Box(width + 2, height + 2).rendered_text
            for (i, line) in enumerate(box[0]):
                self._frame.canvas.paint(
                    line, self._x + self._offset, self._y + i, colour, attr, bg)

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
        if self._value is None:
            self._value = [""]
        self._line = len(self._value) - 1
        self._column = len(self._value[self._line])

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
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
                        self._value[self._line] += self._value.pop(self._line+1)
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
            elif 32 <= event.key_code < 256:
                # Insert any visible text at the current cursor position.
                self._value[self._line] = chr(event.key_code).join([
                    self._value[self._line][:self._column],
                    self._value[self._line][self._column:]])
                self._column += 1
            else:
                # Ignore any other key press.
                return event
        else:
            # Ignore non-keyboard events
            return event

    def required_height(self, offset, width):
        # Allow for extra border lines
        return self._required_height + 2

    # TODO: Standardize the value interface for all widgets.
    @property
    def value(self):
        """
        The value to return for this widget based on the user's input.
        """
        if self._value is None:
            self._value = [""]
        return "\n".join(self._value) if self._as_string else self._value

    @value.setter
    def value(self, new_value):
        if new_value is None:
            self._value = [""]
        elif self._as_string:
            self._value = new_value.split("\n")
        else:
            self._value = new_value


class ListBox(Widget):
    """
    A ListBox is a simple widget for displaying a list of options from which
    the user can select one option.
    """

    def __init__(self, height, options, label=None, name=None, on_select=None):
        """
        :param height: The required number of input lines for this TextBox.
        :param label: An optional label for the widget.
        :param name: The name for the TextBox.
        """
        super(ListBox, self).__init__(name)
        self._options = options
        self._label = label
        self._line = 0
        self._start_line = 0
        self._required_height = height
        self._on_select = on_select

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

    def reset(self):
        # Reset selection - use value to trigger on_select
        if len(self._options) > 0:
            self._line = 0
            self.value = self._options[self._line][1]
        else:
            self._line = None
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
        else:
            # Ignore non-keyboard events
            return event

    def required_height(self, offset, width):
        # Allow for extra border lines
        return self._required_height + 2

    @property
    def value(self):
        """
        The value to return for this widget based on the user's input.
        """
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        for i, (_, value) in enumerate(self._options):
            if value == new_value:
                self._line = i
                break
        else:
            self._value = None
            self._line = None
        if self._on_select:
            self._on_select()

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
        self._text = text
        self._on_click = on_click
        self._label = label

    def update(self, frame_no):
        self._draw_label()

        # Render this button centrally in the available space
        button = "< {} >".format(self._text)
        dx = max(0, (self._w - self._offset - len(button)) // 2)
        (colour, attr, bg) = self._pick_colours("button")
        self._frame.canvas.print_at(
            button,
            self._x + self._offset + dx,
            self._y,
            colour, attr, bg)

    def reset(self):
        self._value = False

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord(" "), 10, 13]:
                self._on_click()
            else:
                # Ignore any other key press.
                return event
        elif isinstance(event, MouseEvent):
            # TODO: convert to formal function.  Also consider rebasing all mouse events.
            new_event = copy(event)
            new_event.x -= self._frame._canvas._dx
            new_event.y -= self._frame._canvas._dy - self._frame._canvas._start_line
            if event.buttons != 0:
                if (self._x <= new_event.x < self._x + self._w and
                        self._y <= new_event.y < self._y + self._h):
                    self._on_click()
        # Ignore other events
        return event

    def required_height(self, offset, width):
        return 1


class PopUpDialog(Frame):
    """
    A fixed implementation Frame that simply provides a standard message box
    dialog.
    """

    # Override standard palette for pop-ups
    _normal = (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_RED)
    _bold = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_RED)
    palette = {
        "background": _normal,
        "label": _bold,
        "borders": _normal,
        "edit_text": _normal,
        "focus_edit_text": _bold,
        "field": _normal,
        "focus_field": _bold,
        "button": _normal,
        "focus_button": _bold,
        "control": _normal,
        "focus_control": _bold,
    }

    def __init__(self, screen, text, buttons):
        """
        :param screen: The Screen that owns this dialog.
        :param text: The message text to display.
        :param buttons: A list of button names to display.
        """
        # Always make the dialog 2/3 of the screen width.
        width = screen.width * 2 // 3

        # Figure out the necessary message and allow for buttons and borders
        # when deciding on height.
        self._message = _split_text(text, width, screen.height - 4)
        height = len(self._message) + 3

        # Construct the Frame
        self._data = {"message": self._message}
        super(PopUpDialog, self).__init__(screen, self._data, height, width)

        # Build up the message box
        layout = Layout([100])
        self.add_layout(layout)
        layout.add_widget(TextBox(len(self._message), name="message"))
        layout2 = Layout([1 for _ in buttons])
        self.add_layout(layout2)
        for i, button in enumerate(buttons):
            layout2.add_widget(Button(button, self._destroy), i)
        self.fix()

    def _destroy(self):
        self._scene.remove_effect(self)
