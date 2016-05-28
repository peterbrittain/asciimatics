class Event(object):
    """
    A class to hold information about an input event.  The exact contents
    varies from event to event.  See specific classes for more information.
    """


class KeyboardEvent(Event):
    """
    This event represents a key press.  Its key field is the `key_code`.  This
    is the ordinal representation of the key (taking into account keyboard
    state - e.g. caps lock) if possible, or an extended key code (the `KEY_xxx`
    constants in the :py:obj:`.Screen` class) where not.
    """
    def __init__(self, key_code):
        self.key_code = key_code

    def __repr__(self):
        return "KeyboardEvent: {}".format(self.key_code)


class MouseEvent(Event):
    """
    The event represents a mouse move or click.  Allowed values for the buttons
    are any bitwise combination of `LEFT_CLICK`, `RIGHT_CLICK` and
    `DOUBLE_CLICK`.
    """

    # Mouse button states - bitwise flags
    LEFT_CLICK = 1
    RIGHT_CLICK = 2
    DOUBLE_CLICK = 4

    def __init__(self, x, y, buttons):
        self.x = x
        self.y = y
        self.buttons = buttons

    def __repr__(self):
        return "MouseEvent ({}, {}) {}".format(self.x, self.y, self.buttons)
