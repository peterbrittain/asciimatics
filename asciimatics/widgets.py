from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from builtins import object
from builtins import range
from future.utils import with_metaclass
from abc import ABCMeta, abstractmethod, abstractproperty
from asciimatics.effects import Effect
from asciimatics.event import KeyboardEvent
from asciimatics.renderers import Box
from asciimatics.screen import Screen


class Frame(Effect):
    """
    A Frame is a special Effect for controlling and displaying Widgets.  Widgets
    are GUI elements that can be used to create an application.
    """

    def __init__(self, screen):
        """
        :param screen: The Screen that owns this Frame.
        """
        super(Frame, self).__init__()
        self._screen = screen
        self._focus = 0
        self._layouts = []

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
        self._layouts[self._focus].focus()

    def _update(self, frame_no):
        for layout in self._layouts:
            layout.update(frame_no)

    @property
    def stop_frame(self):
        # Widgets have no defined end - always return -1.
        return -1

    @property
    def screen(self):
        """
        The Screen that owns this Frame.
        """
        return self._screen

    def reset(self):
        for layout in self._layouts:
            layout.reset()

    def process_event(self, event):
        # Give the current widget in focus first chance to process the event.
        event = self._layouts[self._focus].process_event(event)

        # If the underlying widgets did not process the event, try processing
        # it now.
        if event is not None:
            if isinstance(event, KeyboardEvent):
                if event.key_code == Screen.KEY_TAB:
                    # Move on to next widget.
                    self._layouts[self._focus].blur()
                    self._focus += 1
                    if self._focus >= len(self._layouts):
                        self._focus = 0
                    self._layouts[self._focus].focus(force_first=True)
                    event = None
                elif event.key_code == Screen.KEY_BACK_TAB:
                    # Move on to previous widget.
                    self._layouts[self._focus].blur()
                    self._focus -= 1
                    if self._focus < 0:
                        self._focus = len(self._layouts) - 1
                    self._layouts[self._focus].focus(force_last=True)
                    event = None
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
        as a percentage of the full screen width.
    3.  The Widgets are assigned a column within the Layout that owns them.
    4.  The Layout then decides the exact size and location to make the
        Widget best fit the screen as constrained by the above.
    """

    def __init__(self, columns):
        """
        :param columns: A list of numbers specifying the width of each column
                        in this layout.

        The Layout will automatically normalize the units used for the columns,
        e.g. converting [2, 6, 2] to [20%, 60%, 20%] of the available screen.
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

    def focus(self, force_first=False, force_last=False):
        """
        Call this to give this Layout the input focus.

        :param force_first: Optional parameter to force focus to first widget.
        :param force_last: Optional parameter to force focus to last widget.
        """
        self._has_focus = True
        if force_first:
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
            y = start_y
            w = int(self._frame.screen.width * self._column_sizes[i])
            for widget in column:
                h = widget.required_height
                widget.set_position(x, y, w, h)
                y += h
            max_y = max(max_y, y)
            x += w
        return max_y

    def _find_next_widget(self, direction):
        """
        Find the next widget to get the focus, stopping at the start/end of the
        list if hit.

        :param direction: The direction to move through the widgets
        """
        while 0 <= self._live_col < len(self._columns):
            self._live_widget += direction
            while 0 <= self._live_widget < len(self._columns[self._live_col]):
                if self._columns[self._live_col][self._live_widget].is_tab_stop:
                    break
                self._live_widget += direction
            if (0 <= self._live_widget < len(self._columns[self._live_col]) and
                    self._columns[
                        self._live_col][self._live_widget].is_tab_stop):
                break
            self._live_col += direction
            self._live_widget = \
                -1 if direction > 0 else len(self._columns[self._live_col])

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
        return event

    def update(self, frame_no):
        """
        Redraw the widgets inside this Layout.

        :param frame_no: The current frame to be drawn.
        """
        for column in self._columns:
            for widget in column:
                widget.update(frame_no)

    def reset(self):
        """
        Reset this Layout and the Widgets it contains.
        """
        # Reset all the widgets
        for column in self._columns:
            for widget in column:
                widget.reset()

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
        self._frame = None
        self._value = None
        self._has_focus = False
        self._x = self._y = 0
        self._w = self._h = 0

        # Public properties
        self.is_tab_stop = tab_stop

    def register_frame(self, frame):
        """
        Register the Frame that owns this Widget.
        :param frame: The owning Frame.
        """
        self._frame = frame

    def set_position(self, x, y, w, h):
        """
        Set the size and position of the Widget.
        """
        self._x = x
        self._y = y
        self._w = w
        self._h = h

    def focus(self):
        """
        Call this to give this Widget the input focus.
        """
        self._has_focus = True

    def blur(self):
        """
        Call this to give take the input focus from this Widget.
        """
        self._has_focus = False

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
    def value(self):
        """
        The value to return for this widget based on the user's input.
        """
        return self._value

    @abstractproperty
    def required_height(self):
        """
        The minimum required height for this widget.
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
        self._label = label

    def process_event(self, event):
        # Labels have no user interactions
        return event

    def update(self, frame_no):
        self._frame.screen.print_at(self._label, self._x, self._y + 1)

    def reset(self):
        pass

    @property
    def required_height(self):
        # Allow one line for text and a blank spacer before it.
        return 2


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
        if self._draw_line:
            self._frame.screen.print_at("-" * self._w,
                                        self._x,
                                        self._y + (self._required_height // 2))

    def reset(self):
        pass

    @property
    def required_height(self):
        # Allow one line for text and a blank spacer before it.
        return self._required_height


class Text(Widget):
    """
    A Text widget is a single line input field.  It consists of an optional
    label and an entry box.
    """

    def __init__(self, text, label=None, name=None):
        """
        :param text: The initial text to put in the widget.
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        """
        super(Text, self).__init__(name)
        self._text = text
        self._label = label
        self._column = 0
        self._start_column = 0

    def update(self, frame_no):
        # TODO: Sort out layouts with labels
        offset = 0
        width = self._w
        if self._label is not None:
            self._frame.screen.paint(self._label, self._x, self._y)
            offset = 10
            width -= 10

        # Calculate new visible limits if needed.
        self._start_column = max(0, max(self._column - width + 1,
                                        min(self._start_column, self._column)))

        # Render visible portion of the text.
        self._frame.screen.print_at(
            self._value[self._start_column:self._start_column + width],
            self._x + offset,
            self._y)

        # Since we switch off the standard cursor, we need to emulate our own
        # if we have the input focus.
        if self._has_focus:
            cursor = " "
            if frame_no % 10 < 5:
                attr = Screen.A_REVERSE
            else:
                attr = 0
            if self._column < len(self._value):
                cursor = self._value[self._column]
            self._frame.screen.print_at(
                cursor,
                self._x + offset + self._column - self._start_column,
                self._y,
                attr=attr)

    def reset(self):
        # Reset to original data and move to end of the text.
        self._value = self._text
        self._column = len(self._text)

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
        else:
            # Ignore non-keyboard events
            return event

    @property
    def required_height(self):
        return 1


class CheckBox(Widget):
    """
    A CheckBox widget is used to ask for simple Boolean (i.e. yes/no) input.  It
    consists of an optional label (typically used for teh first in a group of
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
        self._column = 0
        self._start_column = 0

    def update(self, frame_no):
        # TODO: Sort out layouts with labels
        offset = 0
        width = self._w
        if self._label is not None:
            self._frame.screen.paint(self._label, self._x, self._y)
            offset = 10
            width -= 10

        # Render visible portion of the text.
        self._frame.screen.print_at(
            "[{}] {}".format("X" if self._value else " ", self._text),
            self._x + offset,
            self._y,
            attr=Screen.A_BOLD if self._has_focus else Screen.A_NORMAL)

    def reset(self):
        self._value = False

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord(" "), 10, 13]:
                self._value = not self._value
            else:
                # Ignore any other key press.
                return event
        else:
            # Ignore non-keyboard events
            return event

    @property
    def required_height(self):
        return 1


class TextBox(Widget):
    """
    A TextBox is a simple widget for recording and displaying the text that has
    been typed into it (when it has the focus).  It consists of a simple
    framed box with option label.  It can take multi-line input.
    """

    def __init__(self, text, height, name=None):
        """
        :param text: The initial text to put in the TextBox.
        :param height: The required number of input lines for this TextBox.
        :param name: The name for the TextBox.
        """
        super(TextBox, self).__init__(name)
        self._text = text
        self._line = 0
        self._column = 0
        self._start_line = 0
        self._start_column = 0
        self._required_height = height

    def update(self, frame_no):
        # Calculate new visible limits if needed.
        self._start_line = max(0, max(self._line - self._h + 3,
                                      min(self._start_line, self._line)))
        self._start_column = max(0, max(self._column - self._w + 3,
                                        min(self._start_column, self._column)))

        # Create box rendered text now.
        box = Box(self._w, self._h).rendered_text

        # Redraw the frame and label if needed.
        for (i, line) in enumerate(box[0]):
            self._frame.screen.paint(
                line, self._x, self._y + i, transparent=False)
        # TODO: Consider if still needed with standalone labels
        # if self._label is not None:
        #     self._frame.screen.paint(
        #         " {} ".format(self._label), self._x + 2, self._y)

        # Render visible portion of the text.
        for i, text in enumerate(self._value):
            if self._start_line <= i < self._start_line + self._h - 2:
                self._frame.screen.print_at(
                    text[self._start_column:self._start_column + self._w - 2],
                    self._x + 1,
                    self._y + i + 1 - self._start_line)

        # Since we switch off the standard cursor, we need to emulate our own
        # if we have the input focus.
        if self._has_focus:
            cursor = " "
            if frame_no % 10 < 5:
                attr = Screen.A_REVERSE
            else:
                attr = 0
                if self._column < len(self.value[self._line]):
                    cursor = self.value[self._line][self._column]
            self._frame.screen.print_at(
                cursor,
                self._x + self._column + 1 - self._start_column,
                self._y + self._line + 1 - self._start_line,
                attr=attr)

    def reset(self):
        # Reset to original data and move to end of the text.
        self._value = self._text.split("\n")
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

    @property
    def required_height(self):
        # Allow for extra border lines
        return self._required_height + 2
