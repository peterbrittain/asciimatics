from __future__ import division
from __future__ import absolute_import
from __future__ import print_function


class ResizeScreenError(Exception):
    """
    Asciimatics raises this Exception if the terminal is resized while playing
    a Scene (and the Screen has been told not to ignore a resizing event).
    """

    def __init__(self, message, name=None):
        """
        :param message: Error message for this exception.
        :param name: Next Scene to invoke.  Defaults to next in the list.
        """
        self._name = name
        self._message = message

    def __str__(self):
        """
        Printable form of the exception.
        """
        return self._message

    @property
    def name(self):
        """
        The name of the Scene that was running when the Screen resized.
        """
        return self._name


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

    @property
    def name(self):
        """
        The name of the next Scene to invoke.
        """
        return self._name

class Highlander(Exception):
    """
    There can be only one Layout or Widget with certain options set (designed
    to fill the rest of the screen).  If you hit this exception you have
    a bug in your application.

    If you don't get the name, take a look at this link:
    https://en.wikipedia.org/wiki/Highlander_(film)
    """