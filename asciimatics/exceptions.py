from __future__ import division
from __future__ import absolute_import
from __future__ import print_function


class ResizeScreenError(Exception):
    """
    Asciimatics raises this Exception if the terminal is resized while playing
    a Scene (and the Screen has been told not to ignore a resizing event).
    """

    def __init__(self, message):
        """
        :param message: Error message for this exception.
        """
        self._message = message

    def __str__(self):
        """
        Printable form of the exception.
        """
        return self._message
