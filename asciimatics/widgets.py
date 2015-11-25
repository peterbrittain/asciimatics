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
        self._widgets = []

    def _update(self, frame_no):
        for widget in self._widgets:
            widget.update(frame_no)

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
        for widget in self._widgets:
            widget.reset()

    def add(self, widget):
        """
        Add a widget to the Frame.

        :param widget: The Widget to be added.
        """
        widget.register_frame(self)
        self._widgets.append(widget)

    def process_event(self, event):
        for widget in self._widgets:
            event = widget.process_event(event)
            if event is None:
                break
        return event

    def resize(self):
        # @@@TODO: handle dynamic sizing
        pass


class Widget(with_metaclass(ABCMeta, object)):
    """
    A Widget is a re-usable component that can be used to create a simple GUI.
    """

    def __init__(self, label):
        """
        :param label: The label for this Widget.
        """
        super(Widget, self).__init__()
        self._label = label
        self._frame = None
        self._value = None

    def register_frame(self, frame):
        """
        Register the Frame that owns this Widget.
        :param frame: The owning Frame.
        """
        self._frame = frame

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


class TextBox(Widget):
    """
    A TextBox is a simple widget for recording and displaying the text that has
    been typed into it (when it has the focus).  It consists of a simple
    framed box with option label.  It can take multi-line input.
    """

    def __init__(self, text, label=None):
        """
        :param text: The initial text to put in the TextBox.
        :param label: The label for the TextBox.
        """
        super(TextBox, self).__init__(label)
        self._text = text
        self._line = 0
        self._column = 0
        self._start_line = 0
        self._start_column = 0

        # @@@TODO: Fix hack!
        self._x = 20
        self._y = 5
        self._width = 40
        self._height = 10

        # Create box rendered text now.
        self._box = Box(self._width, self._height).rendered_text

    def update(self, frame_no):
        # Calculate new visible limits if needed.
        self._start_line = max(0, max(self._line - self._height + 3,
                                      min(self._start_line, self._line)))
        self._start_column = max(0, max(self._column - self._width + 3,
                                        min(self._start_column, self._column)))

        # Redraw the frame and label if needed.
        for (i, line) in enumerate(self._box[0]):
            self._frame.screen.paint(
                line, self._x, self._y + i, transparent=False)
        if self._label is not None:
            self._frame.screen.paint(
                " {} ".format(self._label), self._x + 2, self._y)

        # Render visible portion of the text.
        for i, text in enumerate(self._value):
            if self._start_line <= i < self._start_line + self._height - 2:
                self._frame.screen.print_at(
                    text[self._start_column:self._start_column + self._width-2],
                    self._x + 1,
                    self._y + i + 1 - self._start_line)

        # Since we switch off the standard cursor, we need to emulate our own.
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
            elif event.key_code >= ord(" "):
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
