"""This module implements common func5ion for picker widgets"""
from abc import ABCMeta

from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.screen import Screen
from asciimatics.widgets.widget import Widget


class _BasePicker(Widget, metaclass=ABCMeta):
    """
    Common class for picker widgets.
    """

    __slots__ = ["_on_change", "_child", "_popup"]

    def __init__(self, popup, label=None, name=None, on_change=None, **kwargs):
        """
        :param popup: Class to use to handle popup widget.
        :param label: An optional label for the widget.
        :param name: The name for the widget.
        :param on_change: Optional function to call when the selected time changes.

        Also see the common keyword arguments in :py:obj:`.Widget`.
        """
        super().__init__(name, **kwargs)
        self._popup = popup
        self._label = label
        self._on_change = on_change
        self._child = None
        if on_change is None:
            raise RuntimeError("oops")

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
                self._child = self._popup(self)
                self.frame.scene.add_effect(self._child)

        return event

    def required_height(self, offset, width):
        return 1

    @property
    def value(self):
        """
        The current selected time.
        """
        return self._value

    @value.setter
    def value(self, new_value):
        # Only trigger the notification after we've changed the value.
        old_value = self._value
        self._value = new_value
        if old_value != self._value and self._on_change:
            self._on_change()
