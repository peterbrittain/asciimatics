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
            widget.update()

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
    def update(self):
        """
        The update method is called whenever this widget needs to redraw itself.
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

        # @@@TODO: Fix hack!
        self._x = 0
        self._y = 0
        self._width = 80
        self._height = 10

    def update(self):
        box = Box(self._width, self._height).rendered_text
        for (i, line) in enumerate(box[0]):
            self._frame.screen.paint(
                line, self._x, self._y + i, transparent=False)
        if self._label is not None:
            self._frame.screen.paint(
                " {} ".format(self._label), self._x + 2, self._y)

        for i, text in enumerate(self._text.split("\n")):
            self._frame.screen.print_at(text, self._x + 1, self._y + i + 1)

    def reset(self):
        self._value = self._text

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            self._frame.screen.print_at(str(event.key_code) + "    ", 0, 20)
            # Special case processing for editing keys
            if event.key_code in [10, 13]:
                self._text += "\n"
            elif event.key_code == Screen.KEY_BACK:
                self._text = self._text[:-1]
            elif event.key_code > 0:
                self._text += chr(event.key_code)
            else:
                return event
        else:
            return event
