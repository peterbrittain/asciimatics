from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from builtins import object
from builtins import range
from future.utils import with_metaclass
import os
import time
from abc import ABCMeta, abstractmethod
import copy
import sys
import signal
from .exceptions import ResizeScreenError


class Screen(with_metaclass(ABCMeta, object)):
    """
    Class to track basic state of the screen.  This constructs the necessary
    resources to allow us to do the ASCII animations.

    This is an abstract class that will build the correct concrete class for
    you when you call :py:meth:`.wrapper`.

    It is still permitted to call the class methods - e.g.
    :py:meth:`.from_curses` or :py:meth:`.from_blessed`, however these are
    deprecated and may be removed in future major releases.

    Note that you need to define the required height for your screen buffer.
    This is important if you plan on using any Effects that will scroll the
    screen vertically (e.g. Scroll).  It must be big enough to handle the
    full scrolling of your selected Effect.
    """

    #: Attribute styles supported by Screen formatting functions
    A_BOLD = 1
    A_NORMAL = 2
    A_REVERSE = 3
    A_UNDERLINE = 4

    #: Standard colours supported by Screen formatting functions
    COLOUR_BLACK = 0
    COLOUR_RED = 1
    COLOUR_GREEN = 2
    COLOUR_YELLOW = 3
    COLOUR_BLUE = 4
    COLOUR_MAGENTA = 5
    COLOUR_CYAN = 6
    COLOUR_WHITE = 7

    # Colour palette for 8/16 colour terminals
    _8_palette = [
        0x00, 0x00, 0x00,
        0x80, 0x00, 0x00,
        0x00, 0x80, 0x00,
        0x80, 0x80, 0x00,
        0x00, 0x00, 0x80,
        0x80, 0x00, 0x80,
        0x00, 0x80, 0x80,
        0xc0, 0xc0, 0xc0,
    ] + [0x00 for _ in range(248 * 3)]

    # Colour palette for 256 colour terminals
    _256_palette = [
        0x00, 0x00, 0x00,
        0x80, 0x00, 0x00,
        0x00, 0x80, 0x00,
        0x80, 0x80, 0x00,
        0x00, 0x00, 0x80,
        0x80, 0x00, 0x80,
        0x00, 0x80, 0x80,
        0xc0, 0xc0, 0xc0,
        0x80, 0x80, 0x80,
        0xff, 0x00, 0x00,
        0x00, 0xff, 0x00,
        0xff, 0xff, 0x00,
        0x00, 0x00, 0xff,
        0xff, 0x00, 0xff,
        0x00, 0xff, 0xff,
        0xff, 0xff, 0xff,
        0x00, 0x00, 0x00,
        0x00, 0x00, 0x5f,
        0x00, 0x00, 0x87,
        0x00, 0x00, 0xaf,
        0x00, 0x00, 0xd7,
        0x00, 0x00, 0xff,
        0x00, 0x5f, 0x00,
        0x00, 0x5f, 0x5f,
        0x00, 0x5f, 0x87,
        0x00, 0x5f, 0xaf,
        0x00, 0x5f, 0xd7,
        0x00, 0x5f, 0xff,
        0x00, 0x87, 0x00,
        0x00, 0x87, 0x5f,
        0x00, 0x87, 0x87,
        0x00, 0x87, 0xaf,
        0x00, 0x87, 0xd7,
        0x00, 0x87, 0xff,
        0x00, 0xaf, 0x00,
        0x00, 0xaf, 0x5f,
        0x00, 0xaf, 0x87,
        0x00, 0xaf, 0xaf,
        0x00, 0xaf, 0xd7,
        0x00, 0xaf, 0xff,
        0x00, 0xd7, 0x00,
        0x00, 0xd7, 0x5f,
        0x00, 0xd7, 0x87,
        0x00, 0xd7, 0xaf,
        0x00, 0xd7, 0xd7,
        0x00, 0xd7, 0xff,
        0x00, 0xff, 0x00,
        0x00, 0xff, 0x5f,
        0x00, 0xff, 0x87,
        0x00, 0xff, 0xaf,
        0x00, 0xff, 0xd7,
        0x00, 0xff, 0xff,
        0x5f, 0x00, 0x00,
        0x5f, 0x00, 0x5f,
        0x5f, 0x00, 0x87,
        0x5f, 0x00, 0xaf,
        0x5f, 0x00, 0xd7,
        0x5f, 0x00, 0xff,
        0x5f, 0x5f, 0x00,
        0x5f, 0x5f, 0x5f,
        0x5f, 0x5f, 0x87,
        0x5f, 0x5f, 0xaf,
        0x5f, 0x5f, 0xd7,
        0x5f, 0x5f, 0xff,
        0x5f, 0x87, 0x00,
        0x5f, 0x87, 0x5f,
        0x5f, 0x87, 0x87,
        0x5f, 0x87, 0xaf,
        0x5f, 0x87, 0xd7,
        0x5f, 0x87, 0xff,
        0x5f, 0xaf, 0x00,
        0x5f, 0xaf, 0x5f,
        0x5f, 0xaf, 0x87,
        0x5f, 0xaf, 0xaf,
        0x5f, 0xaf, 0xd7,
        0x5f, 0xaf, 0xff,
        0x5f, 0xd7, 0x00,
        0x5f, 0xd7, 0x5f,
        0x5f, 0xd7, 0x87,
        0x5f, 0xd7, 0xaf,
        0x5f, 0xd7, 0xd7,
        0x5f, 0xd7, 0xff,
        0x5f, 0xff, 0x00,
        0x5f, 0xff, 0x5f,
        0x5f, 0xff, 0x87,
        0x5f, 0xff, 0xaf,
        0x5f, 0xff, 0xd7,
        0x5f, 0xff, 0xff,
        0x87, 0x00, 0x00,
        0x87, 0x00, 0x5f,
        0x87, 0x00, 0x87,
        0x87, 0x00, 0xaf,
        0x87, 0x00, 0xd7,
        0x87, 0x00, 0xff,
        0x87, 0x5f, 0x00,
        0x87, 0x5f, 0x5f,
        0x87, 0x5f, 0x87,
        0x87, 0x5f, 0xaf,
        0x87, 0x5f, 0xd7,
        0x87, 0x5f, 0xff,
        0x87, 0x87, 0x00,
        0x87, 0x87, 0x5f,
        0x87, 0x87, 0x87,
        0x87, 0x87, 0xaf,
        0x87, 0x87, 0xd7,
        0x87, 0x87, 0xff,
        0x87, 0xaf, 0x00,
        0x87, 0xaf, 0x5f,
        0x87, 0xaf, 0x87,
        0x87, 0xaf, 0xaf,
        0x87, 0xaf, 0xd7,
        0x87, 0xaf, 0xff,
        0x87, 0xd7, 0x00,
        0x87, 0xd7, 0x5f,
        0x87, 0xd7, 0x87,
        0x87, 0xd7, 0xaf,
        0x87, 0xd7, 0xd7,
        0x87, 0xd7, 0xff,
        0x87, 0xff, 0x00,
        0x87, 0xff, 0x5f,
        0x87, 0xff, 0x87,
        0x87, 0xff, 0xaf,
        0x87, 0xff, 0xd7,
        0x87, 0xff, 0xff,
        0xaf, 0x00, 0x00,
        0xaf, 0x00, 0x5f,
        0xaf, 0x00, 0x87,
        0xaf, 0x00, 0xaf,
        0xaf, 0x00, 0xd7,
        0xaf, 0x00, 0xff,
        0xaf, 0x5f, 0x00,
        0xaf, 0x5f, 0x5f,
        0xaf, 0x5f, 0x87,
        0xaf, 0x5f, 0xaf,
        0xaf, 0x5f, 0xd7,
        0xaf, 0x5f, 0xff,
        0xaf, 0x87, 0x00,
        0xaf, 0x87, 0x5f,
        0xaf, 0x87, 0x87,
        0xaf, 0x87, 0xaf,
        0xaf, 0x87, 0xd7,
        0xaf, 0x87, 0xff,
        0xaf, 0xaf, 0x00,
        0xaf, 0xaf, 0x5f,
        0xaf, 0xaf, 0x87,
        0xaf, 0xaf, 0xaf,
        0xaf, 0xaf, 0xd7,
        0xaf, 0xaf, 0xff,
        0xaf, 0xd7, 0x00,
        0xaf, 0xd7, 0x5f,
        0xaf, 0xd7, 0x87,
        0xaf, 0xd7, 0xaf,
        0xaf, 0xd7, 0xd7,
        0xaf, 0xd7, 0xff,
        0xaf, 0xff, 0x00,
        0xaf, 0xff, 0x5f,
        0xaf, 0xff, 0x87,
        0xaf, 0xff, 0xaf,
        0xaf, 0xff, 0xd7,
        0xaf, 0xff, 0xff,
        0xd7, 0x00, 0x00,
        0xd7, 0x00, 0x5f,
        0xd7, 0x00, 0x87,
        0xd7, 0x00, 0xaf,
        0xd7, 0x00, 0xd7,
        0xd7, 0x00, 0xff,
        0xd7, 0x5f, 0x00,
        0xd7, 0x5f, 0x5f,
        0xd7, 0x5f, 0x87,
        0xd7, 0x5f, 0xaf,
        0xd7, 0x5f, 0xd7,
        0xd7, 0x5f, 0xff,
        0xd7, 0x87, 0x00,
        0xd7, 0x87, 0x5f,
        0xd7, 0x87, 0x87,
        0xd7, 0x87, 0xaf,
        0xd7, 0x87, 0xd7,
        0xd7, 0x87, 0xff,
        0xd7, 0xaf, 0x00,
        0xd7, 0xaf, 0x5f,
        0xd7, 0xaf, 0x87,
        0xd7, 0xaf, 0xaf,
        0xd7, 0xaf, 0xd7,
        0xd7, 0xaf, 0xff,
        0xd7, 0xd7, 0x00,
        0xd7, 0xd7, 0x5f,
        0xd7, 0xd7, 0x87,
        0xd7, 0xd7, 0xaf,
        0xd7, 0xd7, 0xd7,
        0xd7, 0xd7, 0xff,
        0xd7, 0xff, 0x00,
        0xd7, 0xff, 0x5f,
        0xd7, 0xff, 0x87,
        0xd7, 0xff, 0xaf,
        0xd7, 0xff, 0xd7,
        0xd7, 0xff, 0xff,
        0xff, 0x00, 0x00,
        0xff, 0x00, 0x5f,
        0xff, 0x00, 0x87,
        0xff, 0x00, 0xaf,
        0xff, 0x00, 0xd7,
        0xff, 0x00, 0xff,
        0xff, 0x5f, 0x00,
        0xff, 0x5f, 0x5f,
        0xff, 0x5f, 0x87,
        0xff, 0x5f, 0xaf,
        0xff, 0x5f, 0xd7,
        0xff, 0x5f, 0xff,
        0xff, 0x87, 0x00,
        0xff, 0x87, 0x5f,
        0xff, 0x87, 0x87,
        0xff, 0x87, 0xaf,
        0xff, 0x87, 0xd7,
        0xff, 0x87, 0xff,
        0xff, 0xaf, 0x00,
        0xff, 0xaf, 0x5f,
        0xff, 0xaf, 0x87,
        0xff, 0xaf, 0xaf,
        0xff, 0xaf, 0xd7,
        0xff, 0xaf, 0xff,
        0xff, 0xd7, 0x00,
        0xff, 0xd7, 0x5f,
        0xff, 0xd7, 0x87,
        0xff, 0xd7, 0xaf,
        0xff, 0xd7, 0xd7,
        0xff, 0xd7, 0xff,
        0xff, 0xff, 0x00,
        0xff, 0xff, 0x5f,
        0xff, 0xff, 0x87,
        0xff, 0xff, 0xaf,
        0xff, 0xff, 0xd7,
        0xff, 0xff, 0xff,
        0x08, 0x08, 0x08,
        0x12, 0x12, 0x12,
        0x1c, 0x1c, 0x1c,
        0x26, 0x26, 0x26,
        0x30, 0x30, 0x30,
        0x3a, 0x3a, 0x3a,
        0x44, 0x44, 0x44,
        0x4e, 0x4e, 0x4e,
        0x58, 0x58, 0x58,
        0x62, 0x62, 0x62,
        0x6c, 0x6c, 0x6c,
        0x76, 0x76, 0x76,
        0x80, 0x80, 0x80,
        0x8a, 0x8a, 0x8a,
        0x94, 0x94, 0x94,
        0x9e, 0x9e, 0x9e,
        0xa8, 0xa8, 0xa8,
        0xb2, 0xb2, 0xb2,
        0xbc, 0xbc, 0xbc,
        0xc6, 0xc6, 0xc6,
        0xd0, 0xd0, 0xd0,
        0xda, 0xda, 0xda,
        0xe4, 0xe4, 0xe4,
        0xee, 0xee, 0xee,
    ]

    # Characters for anti-aliasing line drawing.
    _line_chars = " ''^.|/7.\\|Ywbd#"

    def __init__(self, height, width):
        """
        Don't call this constructor directly.
        """
        # Initialize base class variables - e.g. those used for drawing.
        self.height = height
        self.width = width
        self.colours = 0
        self._start_line = 0
        self._x = 0
        self._y = 0

    @classmethod
    def from_curses(cls, win, height=200):
        """
        Construct a new Screen from a curses windows.

        :param win: The curses window to use.
        :param height: The buffer height for this window (if using scrolling).
        """
        return _CursesScreen(win, height)

    @classmethod
    def from_blessed(cls, terminal, height=200):
        """
        Construct a new Screen from a blessed terminal.

        :param terminal: The blessed Terminal to use.
        :param height: The buffer height for this window (if using scrolling).
        """
        return _BlessedScreen(terminal, height)

    @classmethod
    def from_windows(cls, stdout, stdin, height=200):
        """
        Construct a new Screen from a Windows console.

        :param stdout: The Windows PyConsoleScreenBufferType for stdout returned
            from win32console.
        :param stdin: The Windows PyConsoleScreenBufferType for stdin returned
            from win32console.
        :param height: The buffer height for this window (if using scrolling).
        """
        return _WindowsScreen(stdout, stdin, height)

    @classmethod
    def wrapper(cls, func, height=200):
        """
        Construct a new Screen for any platform.  This will initialize and tidy
        up the system as required around the underlying console subsystem.

        :param func: The function to call once the screen has been created.
        :param height: The buffer height for this window (if using scrolling).
        """
        if sys.platform == "win32":
            # Get the standard input/output buffers.
            win_out = win32console.PyConsoleScreenBufferType(
                win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE))
            win_in = win32console.PyConsoleScreenBufferType(
                win32console.GetStdHandle(win32console.STD_INPUT_HANDLE))

            # Hide the cursor.
            (size, visible) = win_out.GetConsoleCursorInfo()
            win_out.SetConsoleCursorInfo(1, 0)

            # Disable scrolling
            mode = win_out.GetConsoleMode()
            win_out.SetConsoleMode(
                mode & ~ win32console.ENABLE_WRAP_AT_EOL_OUTPUT)
            try:
                win_screen = _WindowsScreen(win_out, win_in, height)
                func(win_screen)
            finally:
                win_out.SetConsoleCursorInfo(size, visible)
                win_out.SetConsoleMode(mode)
                win_out.SetConsoleTextAttribute(7)
        else:
            def _wrapper(win):
                cur_screen = _CursesScreen(win, height)
                func(cur_screen)

            curses.wrapper(_wrapper)

    @property
    def start_line(self):
        """
        :return: The start line of the top of the window in the display buffer.
        """
        return self._start_line

    @property
    def dimensions(self):
        """
        :return: The full dimensions of the display buffer as a (height,
            width) tuple.
        """
        return self.height, self.width

    @property
    def palette(self):
        """
        :return: A palette compatible with the PIL.
        """
        if self.colours < 256:
            # Use the ANSI colour set.
            return self._8_palette
        else:
            return self._256_palette

    @abstractmethod
    def scroll(self):
        """
        Scroll the Screen up one line.
        """

    @abstractmethod
    def clear(self):
        """
        Clear the Screen of all content.
        """

    @abstractmethod
    def refresh(self):
        """
        Refresh the screen.
        """

    @abstractmethod
    def get_key(self):
        """
        Check for a key without waiting.
        """

    @abstractmethod
    def has_resized(self):
        """
        Check whether the screen has been re-sized.

        :returns: True when the screen has been re-sized since the last check.
        """

    @abstractmethod
    def getch(self, x, y):
        """
        Get the character at the specified location.

        :param x: The column (x coord) of the character.
        :param y: The row (y coord) of the character.

        :return: A tuple of the ASCII code of the character at the location
                 and the attributes for that character.
        """

    @abstractmethod
    def putch(self, text, x, y, colour=7, attr=0, transparent=False):
        """
        Print the text at the specified location using the
        specified colour and attributes.

        :param text: The (single line) text to be printed.
        :param x: The column (x coord) for the start of the text.
        :param y: The line (y coord) for the start of the text.
        :param colour: The colour of the text to be displayed.
        :param attr: The cell attribute of the text to be displayed.
        :param transparent: Whether to print spaces or not, thus giving a
            transparent effect.

        See curses for definitions of the colour and attribute values.
        """

    def centre(self, text, y, colour=7, attr=0, colour_map=None):
        """
        Centre the text on the specified line (y) using the optional
        colour and attributes.

        :param text: The (single line) text to be printed.
        :param y: The line (y coord) for the start of the text.
        :param colour: The colour of the text to be displayed.
        :param attr: The cell attribute of the text to be displayed.
        :param colour_map: Colour/attribute list for multi-colour text.

        See curses for definitions of the colour and attribute values.
        """
        x = (self.width - len(text)) // 2
        self.paint(text, x, y, colour, attr, colour_map=colour_map)

    def paint(self, text, x, y, colour=7, attr=0, transparent=False,
              colour_map=None):
        """
        Paint multi-colour text at the defined location.

        :param text: The (single line) text to be printed.
        :param x: The column (x coord) for the start of the text.
        :param y: The line (y coord) for the start of the text.
        :param colour: The default colour of the text to be displayed.
        :param attr: The default cell attribute of the text to be displayed.
        :param transparent: Whether to print spaces or not, thus giving a
            transparent effect.
        :param colour_map: Colour/attribute list for multi-colour text.

        See curses for definitions of the colour and attribute values.  The
        colour_map is a list of tuples (colour, attribute) that must be the
        same length as the passed in text (or None if no mapping is required).
        """
        if colour_map is None:
            self.putch(text, x, y, colour, attr, transparent)
        else:
            for i, c in enumerate(text):
                if colour_map[i][0] is None:
                    self.putch(c, x + i, y, colour, attr, transparent)
                else:
                    self.putch(c, x + i, y, colour_map[i][0], colour_map[i][1],
                               transparent)

    def is_visible(self, x, y):
        """
        Return whether the specified location is on the visible screen.

        :param x: The column (x coord) for the location to check.
        :param y: The line (y coord) for the location to check.
        """
        return ((x >= 0) and
                (x <= self.width) and
                (y >= self._start_line) and
                (y < self._start_line + self.height))

    def play(self, scenes, stop_on_resize=False):
        """
        Play a set of scenes.

        :param scenes: a list of :py:obj:`.Scene` objects to play.
        :param stop_on_resize: Whether to stop when the screen is resized.
            Default is to carry on regardless - which will typically result
            in an error. This is largely done for back-compatibility.

        :raises ResizeScreenError: if the screen is resized (and allowed by
            stop_on_resize).
        """
        self.clear()
        while True:
            for scene in scenes:
                frame = 0
                if scene.clear:
                    self.clear()
                scene.reset()
                re_sized = False
                while (scene.duration < 0 or frame < scene.duration) and \
                        not re_sized:
                    frame += 1
                    for effect in scene.effects:
                        effect.update(frame)
                    self.refresh()
                    c = self.get_key()
                    if c in (ord("X"), ord("x"), ord("Q"), ord("q")):
                        return
                    if c in (ord(" "), ord("\n")):
                        break
                    re_sized = self.has_resized()
                    time.sleep(0.05)

                # Break out of the function if mandated by caller.
                if re_sized:
                    if stop_on_resize:
                        raise ResizeScreenError("Resized terminal")

    def move(self, x, y):
        """
        Move the drawing cursor to the specified position.

        :param x: The column (x coord) for the location to check.
        :param y: The line (y coord) for the location to check.
        """
        self._x = int(round(x, 1)) * 2
        self._y = int(round(y, 1)) * 2

    def draw(self, x, y, char=None, colour=7, thin=False):
        """
        Draw a line from drawing cursor to the specified position.  This uses a
        modified Bressenham algorithm, interpolating twice as many points to
        render down to anti-aliased characters when no character is specified,
        or uses standard algorithm plotting with the specified character.

        :param x: The column (x coord) for the location to check.
        :param y: The line (y coord) for the location to check.
        :param char: Optional character to use to draw the line.
        :param colour: Optional colour for plotting the line.
        :param thin: Optional width of anti-aliased line.
        """
        # Define line end points.
        x0 = self._x
        y0 = self._y
        x1 = int(round(x, 1)) * 2
        y1 = int(round(y, 1)) * 2

        # Remember last point for next line.
        self._x = x1
        self._y = y1

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)

        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1

        x_range = range(0, 2) if sx > 0 else range(1, -1, -1)
        y_range = range(0, 2) if sy > 0 else range(1, -1, -1)

        x = x0
        y = y0

        if dx > dy:
            err = dx
            while x != x1:
                next_chars = [0, 0]
                px = x & ~1
                py = y & ~1
                for ix in x_range:
                    if y >= py and y - py < 2:
                        next_chars[0] |= 2 ** ix * 4 ** (y % 2)
                    else:
                        next_chars[1] |= 2 ** ix * 4 ** (y % 2)
                    if not thin:
                        if y + sy >= py and y + sy - py < 2:
                            next_chars[0] |= 2 ** ix * 4 ** ((y + sy) % 2)
                        else:
                            next_chars[1] |= 2 ** ix * 4 ** ((y + sy) % 2)
                    err -= 2 * dy
                    if err < 0:
                        y += sy
                        err += 2 * dx
                    x += sx

                if char is None:
                    self.putch(self._line_chars[next_chars[0]], px//2, py//2,
                               colour)
                    if next_chars[1] != 0:
                        self.putch(self._line_chars[next_chars[1]],
                                   px // 2, py // 2 + sy, colour)
                elif char == " ":
                    self.putch(char, px // 2, py // 2)
                    self.putch(char, px // 2, py // 2 + sy)
                else:
                    self.putch(char, px // 2, py // 2, colour)
        else:
            err = dy
            while y != y1:
                next_chars = [0, 0]
                px = x & ~1
                py = y & ~1
                for iy in y_range:
                    if x >= px and x - px < 2:
                        next_chars[0] |= 2 ** (x % 2) * 4 ** iy
                    else:
                        next_chars[1] |= 2 ** (x % 2) * 4 ** iy
                    if not thin:
                        if x + sx >= px and x + sx - px < 2:
                            next_chars[0] |= 2 ** ((x + sx) % 2) * 4 ** iy
                        else:
                            next_chars[1] |= 2 ** ((x + sx) % 2) * 4 ** iy
                    err -= 2 * dx
                    if err < 0:
                        x += sx
                        err += 2 * dy
                    y += sy

                if char is None:
                    self.putch(self._line_chars[next_chars[0]], px//2, py//2,
                               colour)
                    if next_chars[1] != 0:
                        self.putch(
                            self._line_chars[next_chars[1]], px//2 + sx, py//2,
                            colour)
                elif char == " ":
                    self.putch(char, px // 2, py // 2)
                    self.putch(char, px // 2 + sx, py // 2)
                else:
                    self.putch(char, px // 2, py // 2, colour)


class _BufferedScreen(with_metaclass(ABCMeta, Screen)):
    """
    Abstract class to handle screen buffering when not using curses.
    """

    def __init__(self, height, width, buffer_height):
        """
        :param height: The buffer height for this window.
        :param width: The buffer width for this window.
        :param buffer_height: The buffer height for this window.
        """
        # Save off the screen details and se up the scrolling pad.
        super(_BufferedScreen, self).__init__(height, width)

        # Create screen buffers (required to reduce flicker).
        self._screen_buffer = None
        self._double_buffer = None
        self._buffer_height = buffer_height

        # Remember current state so we don't keep programming colours/attributes
        # and move commands unnecessarily.
        self._colour = None
        self._attr = None
        self._x = None
        self._y = None
        self._last_start_line = 0

    def scroll(self):
        """
        Scroll the Screen up one line.
        """
        self._start_line += 1

    def clear(self):
        """
        Clear the Screen of all content.
        """
        # Clear the actual terminal
        self._change_colours(self.COLOUR_WHITE, 0)
        self._clear()
        self._start_line = self._last_start_line = 0
        self._x = self._y = None

        # Reset our screen buffer
        line = [(" ", 7, 0) for _ in range(self.width)]
        self._screen_buffer = [
            copy.deepcopy(line) for _ in range(self._buffer_height)]
        self._double_buffer = copy.deepcopy(self._screen_buffer)

    def refresh(self):
        """
        Refresh the screen.
        """
        # Scroll the screen as required to minimize redrawing.
        for _ in range(self._start_line - self._last_start_line):
            self._scroll()
        self._last_start_line = self._start_line

        # Now draw any deltas to the scrolled screen.
        for y in range(self.height):
            for x in range(self.width):
                new_cell = self._double_buffer[y + self._start_line][x]
                if self._screen_buffer[y + self._start_line][x] != new_cell:
                    self._change_colours(new_cell[1], new_cell[2])
                    self._print_at(new_cell[0], x, y)
                    self._screen_buffer[y + self._start_line][x] = new_cell

    def getch(self, x, y):
        """
        Get the character at the specified location.

        :param x: The column (x coord) of the character.
        :param y: The row (y coord) of the character.

        :return: A tuple of the ASCII code of the character at the location
                 and the attributes for that character.
        """
        cell = self._screen_buffer[y][x]
        return ord(cell[0]), cell[1] + cell[2] * 256

    def putch(self, text, x, y, colour=7, attr=0, transparent=False):
        """
        Print the text at the specified location using the
        specified colour and attributes.

        :param text: The (single line) text to be printed.
        :param x: The column (x coord) for the start of the text.
        :param y: The line (y coord) for the start of the text.
        :param colour: The colour of the text to be displayed.
        :param attr: The cell attribute of the text to be displayed.
        :param transparent: Whether to print spaces or not, thus giving a
            transparent effect.

        See curses for definitions of the colour and attribute values.
        """
        # Trim text to the buffer.
        if y < 0 or y >= self._buffer_height:
            return
        if x < 0:
            text = text[-x:]
            x = 0
        if x + len(text) >= self.width:
            text = text[:self.width - x]

        if len(text) > 0:
            for i, c in enumerate(text):
                if c != " " or not transparent:
                    self._double_buffer[y][x + i] = (c, colour, attr)

    @abstractmethod
    def _change_colours(self, colour, attr):
        """
        Change current colour if required.

        :param colour: New colour to use
        :param attr: New attributes to use
        """

    @abstractmethod
    def _print_at(self, text, x, y):
        """
        Print string at the required location.

        :param text: The text string to print.
        :param x: The x coordinate
        :param y: The Y coordinate
        """

    @abstractmethod
    def _clear(self):
        """
        Clear the window.
        """

    @abstractmethod
    def _scroll(self):
        """
        Scroll the window up one line.
        """


if sys.platform == "win32":
    import win32console

    class _WindowsScreen(_BufferedScreen):
        """
        Windows screen implementation.
        """

        # Colour lookup table.
        _COLOURS = {
            Screen.COLOUR_BLACK: 0,
            Screen.COLOUR_RED: win32console.FOREGROUND_RED,
            Screen.COLOUR_GREEN: win32console.FOREGROUND_GREEN,
            Screen.COLOUR_YELLOW: (win32console.FOREGROUND_RED |
                                   win32console.FOREGROUND_GREEN),
            Screen.COLOUR_BLUE: win32console.FOREGROUND_BLUE,
            Screen.COLOUR_MAGENTA: (win32console.FOREGROUND_RED |
                                    win32console.FOREGROUND_BLUE),
            Screen.COLOUR_CYAN: (win32console.FOREGROUND_BLUE |
                                 win32console.FOREGROUND_GREEN),
            Screen.COLOUR_WHITE: (win32console.FOREGROUND_RED |
                                  win32console.FOREGROUND_GREEN |
                                  win32console.FOREGROUND_BLUE)
        }

        # Attribute lookup table
        _ATTRIBUTES = {
            0: lambda x: x,
            Screen.A_BOLD: lambda x: x | win32console.FOREGROUND_INTENSITY,
            Screen.A_NORMAL: lambda x: x,
            # Windows console uses a bitmap where background is the top nibble,
            # so we can reverse by simply multiplying by 16.
            Screen.A_REVERSE: lambda x: x * 16,
            Screen.A_UNDERLINE: lambda x: x
        }

        def __init__(self, stdout, stdin, buffer_height):
            """
            :param stdout: The win32console PyConsoleScreenBufferType object for
                stdout.
            :param stdin: The win32console PyConsoleScreenBufferType object for
                stdin.
            :param buffer_height: The buffer height for this window (if using
                scrolling).
            """
            # Save off the screen details and se up the scrolling pad.
            info = stdout.GetConsoleScreenBufferInfo()['Window']
            width = info.Right - info.Left + 1
            height = info.Bottom - info.Top + 1
            super(_WindowsScreen, self).__init__(height, width, buffer_height)

            # Save off the console details.
            self._stdout = stdout
            self._stdin = stdin
            self._last_width = None
            self._last_height = None

            # Windows is limited to the ANSI colour set.
            self.colours = 8

        def get_key(self):
            """
            Check for a key without waiting.
            """
            # Look for a new keypress and consume it if there is one.
            if len(self._stdin.PeekConsoleInput(1)) > 0:
                event = self._stdin.ReadConsoleInput(1)[0]
                if (event.EventType == win32console.KEY_EVENT and
                        not event.KeyDown):
                    return ord(event.Char)
            return None

        def has_resized(self):
            """
            Check whether the screen has been re-sized.
            """
            # Get the current Window dimensions and check them against last
            # time.
            re_sized = False
            info = self._stdout.GetConsoleScreenBufferInfo()['Window']
            width = info.Right - info.Left + 1
            height = info.Bottom - info.Top + 1
            if self._last_width is not None and (
                    width != self._last_width or height != self._last_height):
                re_sized = True
            self._last_width = width
            self._last_height = height
            return re_sized

        def _change_colours(self, colour, attr):
            """
            Change current colour if required.

            :param colour: New colour to use
            :param attr: New attributes to use
            """
            # Change attribute first as this will reset colours when swapping
            # modes.
            if colour != self._colour or attr != self._attr:
                new_attr = self._ATTRIBUTES[attr](self._COLOURS[colour])
                self._stdout.SetConsoleTextAttribute(new_attr)
                self._attr = attr
                self._colour = colour

        def _print_at(self, text, x, y):
            """
            Print string at the required location.

            :param text: The text string to print.
            :param x: The x coordinate
            :param y: The Y coordinate
            """
            # Move the cursor if necessary
            if x != self._x or y != self._y:
                self._stdout.SetConsoleCursorPosition(
                    win32console.PyCOORDType(x, y))

            # Print the text at the required location and update the current
            # position.
            self._stdout.WriteConsole(text)
            self._x = x + len(text)
            self._y = y

        def _scroll(self):
            """
            Scroll up by one line.
            """
            # Scroll the visible screen up by one line
            info = self._stdout.GetConsoleScreenBufferInfo()['Window']
            rectangle = win32console.PySMALL_RECTType(info.Left, info.Top + 1,
                                                      info.Right, info.Bottom)
            new_pos = win32console.PyCOORDType(0, info.Top)
            self._stdout.ScrollConsoleScreenBuffer(
                rectangle, None, new_pos, " ", 0)

        def _clear(self):
            """
            Clear the terminal.
            """
            info = self._stdout.GetConsoleScreenBufferInfo()['Window']
            width = info.Right - info.Left + 1
            height = info.Bottom - info.Top + 1
            box_size = width * height
            self._stdout.FillConsoleOutputAttribute(
                0, box_size, win32console.PyCOORDType(0, 0))
            self._stdout.FillConsoleOutputCharacter(
                u" ", box_size, win32console.PyCOORDType(0, 0))
            self._stdout.SetConsoleCursorPosition(
                win32console.PyCOORDType(0, 0))
else:
    # UNIX compatible platform - use curses
    import curses

    class _CursesScreen(Screen):
        """
        Curses screen implementation.
        """

        #: Conversion from Screen attributes to curses equivalents.
        _ATTRIBUTES = {
            Screen.A_BOLD: curses.A_BOLD,
            Screen.A_NORMAL: curses.A_NORMAL,
            Screen.A_REVERSE: curses.A_REVERSE,
            Screen.A_UNDERLINE: curses.A_UNDERLINE
        }

        def __init__(self, win, height=200):
            """
            :param win: The window object as returned by the curses wrapper
                method.
            :param height: The height of the screen buffer to be used.
            """
            # Save off the screen details and se up the scrolling pad.
            super(_CursesScreen, self).__init__(
                win.getmaxyx()[0], win.getmaxyx()[1])
            self._screen = win
            self.buffer_height = height
            self._pad = curses.newpad(self.buffer_height, self.width)

            # Set up basic colour schemes.
            self.colours = curses.COLORS
            for i in range(1, self.colours):
                curses.init_pair(i, i, curses.COLOR_BLACK)
            for i in range(0, self.colours):
                curses.init_pair(i + self.colours, curses.COLOR_BLACK, i)

            # Disable the cursor.
            curses.curs_set(0)

            # Non-blocking key checks.
            self._pad.nodelay(1)

            # Set up signal handler for screen resizing.
            self._re_sized = False
            signal.signal(signal.SIGWINCH, self._resize_handler)

        def _resize_handler(self, *_):
            """
            Window resize signal handler.  We don't care about any of the
            parameters passed in beyond the object reference.
            """
            curses.endwin()
            curses.initscr()
            self._re_sized = True

        def scroll(self):
            """
            Scroll the Screen up one line.
            """
            self._start_line += 1

        def clear(self):
            """
            Clear the Screen of all content.
            """
            self._pad.clear()
            self._start_line = 0

        def refresh(self):
            """
            Refresh the screen.
            """
            (h, w) = self._screen.getmaxyx()
            self._pad.refresh(self._start_line,
                              0,
                              0,
                              0,
                              h - 1,
                              w - 1)

        def get_key(self):
            """
            Check for a key without waiting.
            """
            key = self._pad.getch()
            if key == curses.KEY_RESIZE:
                self._re_sized = True
            return key

        def has_resized(self):
            """
            Check whether the screen has been re-sized.
            """
            re_sized = self._re_sized
            self._re_sized = False
            return re_sized

        def getch(self, x, y):
            """
            Get the character at the specified location.

            :param x: The column (x coord) of the character.
            :param y: The row (y coord) of the character.

            :return: A tuple of the ASCII code of the character at the location
                     and the attributes for that character.
            """
            curses_rc = self._pad.inch(y, x)
            return curses_rc & 0xff, curses_rc & 0xff >> 8

        def putch(self, text, x, y, colour=7, attr=0, transparent=False):
            """
            Print the text at the specified location using the
            specified colour and attributes.

            :param text: The (single line) text to be printed.
            :param x: The column (x coord) for the start of the text.
            :param y: The line (y coord) for the start of the text.
            :param colour: The colour of the text to be displayed.
            :param attr: The cell attribute of the text to be displayed.
            :param transparent: Whether to print spaces or not, thus giving a
                transparent effect.

            See curses for definitions of the colour and attribute values.
            """
            # Crop to pad size
            if y < 0:
                return
            if x < 0:
                text = text[-x:]
                x = 0
            if x + len(text) >= self.width:
                text = text[:self.width - x]

            # Convert attribute to curses equivalent
            attr = self._ATTRIBUTES[attr] if attr in self._ATTRIBUTES else 0

            # Print whatever is left
            if len(text) > 0:
                if transparent:
                    for i, c in enumerate(text):
                        if c != " ":
                            self._pad.addstr(
                                y, x + i, c, curses.color_pair(colour) | attr)
                else:
                    self._pad.addstr(
                        y, x, text, curses.color_pair(colour) | attr)

    class _BlessedScreen(_BufferedScreen):
        """
        Blessed screen implementation.
        """

        #: Conversion from Screen attributes to curses equivalents.
        ATTRIBUTES = {
            Screen.A_BOLD: lambda term: term.bold,
            Screen.A_NORMAL: lambda term: "",
            Screen.A_REVERSE: lambda term: term.reverse,
            Screen.A_UNDERLINE: lambda term: term.underline
        }

        def __init__(self, terminal, height):
            """
            :param terminal: The blessed Terminal object.
            :param height: The buffer height for this window (if using
                scrolling).
            """
            # Save off the screen details and se up the scrolling pad.
            super(_BlessedScreen, self).__init__(
                terminal.height, terminal.width, height)

            # Save off terminal.
            self._terminal = terminal

            # Set up basic colour schemes.
            self.colours = terminal.number_of_colors

            # Set up signal handler for screen resizing.
            self._re_sized = False
            signal.signal(signal.SIGWINCH, self._resize_handler)

        def _resize_handler(self, *_):
            """
            Window resize signal handler.  We don't care about any of the
            parameters passed in beyond the object reference.
            """
            self._re_sized = True

        def refresh(self):
            """
            Refresh the screen.
            """
            # Flush screen buffer to get all updates after doing the common
            # processing.  Exact timing of the signal can interrupt the
            # flush, raising an EINTR IOError, which we can safely ignore.
            super(_BlessedScreen, self).refresh()
            try:
                sys.stdout.flush()
            except IOError:
                pass

        def get_key(self):
            """
            Check for a key without waiting.
            """
            key = self._terminal.inkey(timeout=0)
            return ord(key) if key != "" else None

        def has_resized(self):
            """
            Check whether the screen has been re-sized.
            """
            re_sized = self._re_sized
            self._re_sized = False
            return re_sized

        def _change_colours(self, colour, attr):
            """
            Change current colour if required.

            :param colour: New colour to use
            :param attr: New attributes to use
            """
            # Change attribute first as this will reset colours when swapping
            # modes.
            if attr != self._attr:
                sys.stdout.write(
                    self._terminal.normal + self._terminal.on_color(0))
                if attr != 0:
                    sys.stdout.write(self.ATTRIBUTES[attr](self._terminal))
                self._attr = attr
                self._colour = None

            # Now swap colours if required.
            if colour != self._colour:
                sys.stdout.write(self._terminal.color(colour))
                self._colour = colour

        def _print_at(self, text, x, y):
            """
            Print string at the required location.

            :param text: The text string to print.
            :param x: The x coordinate
            :param y: The Y coordinate
            """
            # Move the cursor if necessary
            msg = ""
            if x != self._x or y != self._y:
                msg += self._terminal.move(y, x)

            msg += text

            # Print the text at the required location and update the current
            # position.
            sys.stdout.write(msg)
            self._x = x + len(text)
            self._y = y

        def _scroll(self):
            """
            Scroll up by one line.
            """
            print(self._terminal.move(self.height - 1, 0))

        def _clear(self):
            """
            Clear the terminal.
            """
            sys.stdout.write(self._terminal.clear())
