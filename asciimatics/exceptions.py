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


class StopApplication(Exception):
    """
    Any component can raise this exception to tell Asciimatics to stop running.
    If playing a Scene (i.e. inside `Screen.play()`) the Screen will return
    to the calling function.  When used at any other time, the exception will
    need to be caught by the application using Asciimatics.
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


class NextScene(Exception):
    """
    Any component can raise this exception to tell Asciimatics to move to the
    next Scene being played.  Only effective inside `Screen.play()`.
    """

    def __init__(self, name=None):
        """
        :param name: Next Scene to invoke.  Defaults to next in the list.
        """
        self._name = name
