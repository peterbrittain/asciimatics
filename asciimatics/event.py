"""
This module defines basic input events.  For more details, see
http://asciimatics.readthedocs.io/en/latest/.html
"""


class Event():
    """
    A class to hold information about an input event.

    The exact contents varies from event to event.  See specific classes for more information.
    """


class KeyboardEvent(Event):
    """
    An event that represents a key press.

    Its key field is the `key_code`.  This is the ordinal representation of the key (taking into
    account keyboard state - e.g. caps lock) if possible, or an extended key code (the `KEY_xxx`
    constants in the :py:obj:`.Screen` class) where not.
    """

    def __init__(self, key_code):
        """
        :param key_code: the ordinal value of the key that was pressed.
        """
        self.key_code = key_code

    def __repr__(self):
        """
        :returns: a string representation of the keyboard event.
        """
        return f"KeyboardEvent: {self.key_code}"


class MouseEvent(Event):
    """
    An event that represents a mouse move or click.

    Allowed values for the buttons are any bitwise combination of
    `LEFT_CLICK`, `RIGHT_CLICK` and `DOUBLE_CLICK`.
    """

    # Mouse button states - bitwise flags
    LEFT_CLICK = 1
    RIGHT_CLICK = 2
    DOUBLE_CLICK = 4

    def __init__(self, x, y, buttons):
        """
        :param x: The X coordinate of the mouse event.
        :param y: The Y coordinate of the mouse event.
        :param buttons: A bitwise flag for any mouse buttons that were pressed (if any).
        """
        self.x = x
        self.y = y
        self.buttons = buttons

    def __repr__(self):
        """
        :returns: a string representation of the mouse event.
        """
        return f"MouseEvent ({self.x}, {self.y}) {self.buttons}"
