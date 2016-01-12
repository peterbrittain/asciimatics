from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from builtins import object
from builtins import range
from future.utils import with_metaclass
import time
from abc import ABCMeta, abstractmethod
import copy
import sys
import signal
from asciimatics.event import KeyboardEvent, MouseEvent
from .exceptions import ResizeScreenError, StopApplication, NextScene


# Keep track of last known screen output buffer so we can resize correctly.
_last_screen_buffer = None


class _AbstractCanvas(with_metaclass(ABCMeta, object)):
    """
    Abstract class to handle screen buffering.
    """

    # Characters for anti-aliasing line drawing.
    _line_chars = " ''^.|/7.\\|Ywbd#"

    def __init__(self, height, width, buffer_height):
        """
        :param height: The buffer height for this object.
        :param width: The buffer width for this object.
        :param buffer_height: The buffer height for this window.
        """
        super(_AbstractCanvas, self).__init__()

        # Create screen buffers.
        self.height = height
        self.width = width
        self._buffer_height = buffer_height
        self._screen_buffer = None
        self._double_buffer = None
        self._start_line = 0
        self._x = 0
        self._y = 0

        # Reset the screen ready to go...
        self.reset()

    def reset(self):
        """
        Reset the internal buffers for the abstract canvas.
        """
        # Reset our screen buffer
        self._start_line = 0
        self._x = self._y = None
        line = [(" ", Screen.COLOUR_WHITE, 0, 0) for _ in range(self.width)]
        self._screen_buffer = [
            copy.deepcopy(line) for _ in range(self._buffer_height)]
        self._double_buffer = copy.deepcopy(self._screen_buffer)
        self._reset()

    def scroll(self):
        """
        Scroll the abstract canvas up one line.
        """
        self._start_line += 1

    def scroll_to(self, line):
        """
        Scroll the abstract canvas to make a specific line.

        :param line: The line to scroll to.
        """
        self._start_line = line

    @abstractmethod
    def _reset(self):
        """
        Internal implementation required to reset underlying drawing
        interface.
        """

    @abstractmethod
    def refresh(self):
        """
        Refresh this object - this will draw to the underlying display
        interface.
        """

    def get_from(self, x, y):
        """
        Get the character at the specified location.

        :param x: The column (x coord) of the character.
        :param y: The row (y coord) of the character.

        :return: A 4-tuple of (ascii code, foreground, attributes, background)
                 for the character at the location.
        """
        if y < 0 or y >= self._buffer_height or x < 0 or x >= self.width:
            return None
        cell = self._double_buffer[y][x]
        return ord(cell[0]), cell[1], cell[2], cell[3]

    def print_at(self, text, x, y, colour=7, attr=0, bg=0, transparent=False):
        """
        Print the text at the specified location using the
        specified colour and attributes.

        :param text: The (single line) text to be printed.
        :param x: The column (x coord) for the start of the text.
        :param y: The line (y coord) for the start of the text.
        :param colour: The colour of the text to be displayed.
        :param attr: The cell attribute of the text to be displayed.
        :param bg: The background colour of the text to be displayed.
        :param transparent: Whether to print spaces or not, thus giving a
            transparent effect.

        The colours and attributes are the COLOUR_xxx and A_yyy constants
        defined in the Screen class.
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
                    self._double_buffer[y][x + i] = (c, colour, attr, bg)

    @property
    def start_line(self):
        """
        :return: The start line of the top of the canvas.
        """
        return self._start_line

    @property
    def dimensions(self):
        """
        :return: The full dimensions of the canvas as a (height, width) tuple.
        """
        return self.height, self.width

    def centre(self, text, y, colour=7, attr=0, colour_map=None):
        """
        Centre the text on the specified line (y) using the optional
        colour and attributes.

        :param text: The (single line) text to be printed.
        :param y: The line (y coord) for the start of the text.
        :param colour: The colour of the text to be displayed.
        :param attr: The cell attribute of the text to be displayed.
        :param colour_map: Colour/attribute list for multi-colour text.

        The colours and attributes are the COLOUR_xxx and A_yyy constants
        defined in the Screen class.
        """
        x = (self.width - len(text)) // 2
        self.paint(text, x, y, colour, attr, colour_map=colour_map)

    def paint(self, text, x, y, colour=7, attr=0, bg=0, transparent=False,
              colour_map=None):
        """
        Paint multi-colour text at the defined location.

        :param text: The (single line) text to be printed.
        :param x: The column (x coord) for the start of the text.
        :param y: The line (y coord) for the start of the text.
        :param colour: The default colour of the text to be displayed.
        :param attr: The default cell attribute of the text to be displayed.
        :param bg: The default background colour of the text to be displayed.
        :param transparent: Whether to print spaces or not, thus giving a
            transparent effect.
        :param colour_map: Colour/attribute list for multi-colour text.

        The colours and attributes are the COLOUR_xxx and A_yyy constants
        defined in the Screen class.
        colour_map is a list of tuples (foreground, attribute, background) that
        must be the same length as the passed in text (or None if no mapping is
        required).
        """
        if colour_map is None:
            self.print_at(text, x, y, colour, attr, bg, transparent)
        else:
            for i, c in enumerate(text):
                if len(colour_map[i]) > 0 and colour_map[i][0] is not None:
                    colour = colour_map[i][0]
                if len(colour_map[i]) > 1 and colour_map[i][1] is not None:
                    attr = colour_map[i][1]
                if len(colour_map[i]) > 2 and colour_map[i][2] is not None:
                    bg = colour_map[i][2]
                self.print_at(c, x + i, y, colour, attr, bg, transparent)

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

    def move(self, x, y):
        """
        Move the drawing cursor to the specified position.

        :param x: The column (x coord) for the location to check.
        :param y: The line (y coord) for the location to check.
        """
        self._x = int(round(x, 1)) * 2
        self._y = int(round(y, 1)) * 2

    def draw(self, x, y, char=None, colour=7, bg=0, thin=False):
        """
        Draw a line from drawing cursor to the specified position.  This uses a
        modified Bressenham algorithm, interpolating twice as many points to
        render down to anti-aliased characters when no character is specified,
        or uses standard algorithm plotting with the specified character.

        :param x: The column (x coord) for the location to check.
        :param y: The line (y coord) for the location to check.
        :param char: Optional character to use to draw the line.
        :param colour: Optional colour for plotting the line.
        :param bg: Optional background colour for plotting the line.
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
                    self.print_at(self._line_chars[next_chars[0]], px//2, py//2,
                                  colour, bg=bg)
                    if next_chars[1] != 0:
                        self.print_at(self._line_chars[next_chars[1]],
                                      px // 2, py // 2 + sy, colour, bg=bg)
                elif char == " ":
                    self.print_at(char, px // 2, py // 2, bg=bg)
                    self.print_at(char, px // 2, py // 2 + sy, bg=bg)
                else:
                    self.print_at(char, px // 2, py // 2, colour, bg=bg)
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
                    self.print_at(self._line_chars[next_chars[0]], px//2, py//2,
                                  colour, bg=bg)
                    if next_chars[1] != 0:
                        self.print_at(
                            self._line_chars[next_chars[1]], px//2 + sx, py//2,
                            colour, bg=bg)
                elif char == " ":
                    self.print_at(char, px // 2, py // 2, bg=bg)
                    self.print_at(char, px // 2 + sx, py // 2, bg=bg)
                else:
                    self.print_at(char, px // 2, py // 2, colour, bg=bg)


class Canvas(_AbstractCanvas):
    """
    A Canvas is an object that can be used to draw to the screen. It maintains
    its own buffer that will be flushed to the screen when `refresh()` is
    called.
    """

    def __init__(self, screen, height, width, x=None, y=None):
        """
        :param screen: The underlying Screen that will be drawn to on refresh.
        :param height: The height of the screen buffer to be used.
        :param width: The width of the screen buffer to be used.
        :param x: The x position for the top left corner of the Canvas.
        :param y: The y position for the top left corner of the Canvas.

        If either of the x or y positions is not set, the Canvas will default
        to centring within the current Screen for that location.
        """
        # Save off the screen details.
        # TODO: Fix up buffer logic once and for all!
        super(Canvas, self).__init__(height, width, 200)
        self._screen = screen
        self._dx = (screen.width - width) // 2 if x is None else x
        self._dy = (screen.height - height) // 2 if y is None else y

    def refresh(self):
        """
        Flush the canvas content to the underlying screen.
        """
        for y in range(self.height):
            for x in range(self.width):
                c = self._double_buffer[y + self._start_line][x]
                self._screen.print_at(
                    c[0], x + self._dx, y + self._dy, c[1], c[2], c[3])

    def _reset(self):
        # Nothing needed for a Canvas
        pass

    @property
    def origin(self):
        """
        The location of top left corner of the canvas on the Screen.

        :returns: A tuple (x, y) of the location
        """
        return self._dx, self._dy


class Screen(with_metaclass(ABCMeta, _AbstractCanvas)):
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

    #: Standard extended key codes.    
    KEY_ESCAPE = -1
    KEY_F1 = -2
    KEY_F2 = -3
    KEY_F3 = -4
    KEY_F4 = -5
    KEY_F5 = -6
    KEY_F6 = -7
    KEY_F7 = -8
    KEY_F8 = -9
    KEY_F9 = -10
    KEY_F10 = -11
    KEY_F11 = -12
    KEY_F12 = -13
    KEY_F13 = -14
    KEY_F14 = -15
    KEY_F15 = -16
    KEY_F16 = -17
    KEY_F17 = -18
    KEY_F18 = -19
    KEY_F19 = -20
    KEY_F20 = -21
    KEY_F21 = -22
    KEY_F22 = -23
    KEY_F23 = -24
    KEY_F24 = -25
    KEY_PRINT_SCREEN = -100
    KEY_INSERT = -101
    KEY_DELETE = -102
    KEY_HOME = -200
    KEY_END = -201
    KEY_LEFT = -203
    KEY_UP = -204
    KEY_RIGHT = -205
    KEY_DOWN = -206
    KEY_PAGE_UP = -207
    KEY_PAGE_DOWN = -208
    KEY_BACK = -300
    KEY_TAB = -301
    KEY_BACK_TAB = -302
    KEY_NUMPAD0 = -400
    KEY_NUMPAD1 = -401
    KEY_NUMPAD2 = -402
    KEY_NUMPAD3 = -403
    KEY_NUMPAD4 = -404
    KEY_NUMPAD5 = -405
    KEY_NUMPAD6 = -406
    KEY_NUMPAD7 = -407
    KEY_NUMPAD8 = -408
    KEY_NUMPAD9 = -409
    KEY_MULTIPLY = -410
    KEY_ADD = -411
    KEY_SUBTRACT = -412
    KEY_DECIMAL = -413
    KEY_DIVIDE = -414
    KEY_CAPS_LOCK = -500
    KEY_NUM_LOCK = -501
    KEY_SCROLL_LOCK = -502
    KEY_SHIFT = -600
    KEY_CONTROL = -601
    KEY_MENU = -602

    #  Colour palette for 8/16 colour terminals
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

    def __init__(self, height, width, buffer_height):
        """
        Don't call this constructor directly.
        """
        super(Screen, self).__init__(height, width, buffer_height)
        # Initialize base class variables - e.g. those used for drawing.
        self.height = height
        self.width = width
        self.colours = 0
        self._last_start_line = 0

        # Set up internal state for colours - used by children to determine
        # changes to text colour when refreshing the screen.
        self._colour = 0
        self._attr = 0
        self._bg = 0

    @classmethod
    def from_curses(cls, win, height=200):
        """
        Construct a new Screen from a curses windows.

        :param win: The curses window to use.
        :param height: The buffer height for this window (if using scrolling).

        This method is deprecated.  Please use :py:meth:`.wrapper` instead.
        """
        return _CursesScreen(win, height)

    @classmethod
    def from_blessed(cls, terminal, height=200):
        """
        Construct a new Screen from a blessed terminal.

        :param terminal: The blessed Terminal to use.
        :param height: The buffer height for this window (if using scrolling).

        This method is deprecated.  Please use :py:meth:`.wrapper` instead.
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

        This method is deprecated.  Please use :py:meth:`.wrapper` instead.
        """
        return _WindowsScreen(stdout, stdin, height)

    @classmethod
    def wrapper(cls, func, height=200, catch_interrupt=False):
        """
        Construct a new Screen for any platform.  This will initialize and tidy
        up the system as required around the underlying console subsystem.

        :param func: The function to call once the screen has been created.
        :param height: The buffer height for this window (if using scrolling).
        :param catch_interrupt: Whether to catch and prevent keyboard
            interrupts.  Defaults to False to maintain backwards compatibility.
        """
        if sys.platform == "win32":
            # I don't like this, but we need to track the last screen for
            # resizing commands in Windows 10.
            global _last_screen_buffer

            # Clone the standard output buffer so that we can do whatever we
            # need for the application, but restore the buffer at the end.
            # Note that we need to resize the clone to ensure that it is the
            # same size as the original in some versions of Windows.
            old_out = win32console.PyConsoleScreenBufferType(
                win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE))
            if _last_screen_buffer is None:
                info = old_out.GetConsoleScreenBufferInfo()
            else:
                info = _last_screen_buffer.GetConsoleScreenBufferInfo()
            win_out = win32console.CreateConsoleScreenBuffer()
            win_out.SetConsoleScreenBufferSize(info['Size'])
            win_out.SetConsoleActiveScreenBuffer()

            # Get the standard input buffer.
            win_in = win32console.PyConsoleScreenBufferType(
                win32console.GetStdHandle(win32console.STD_INPUT_HANDLE))

            # Hide the cursor.
            (size, visible) = win_out.GetConsoleCursorInfo()
            win_out.SetConsoleCursorInfo(1, 0)

            # Disable scrolling
            out_mode = win_out.GetConsoleMode()
            win_out.SetConsoleMode(
                out_mode & ~ win32console.ENABLE_WRAP_AT_EOL_OUTPUT)

            # Enable mouse input and disable ctrl-c if needed.
            in_mode = win_in.GetConsoleMode()
            new_mode = in_mode | win32console.ENABLE_MOUSE_INPUT
            if catch_interrupt:
                # Ignore ctrl-c handlers if specified.
                new_mode &= ~win32console.ENABLE_PROCESSED_INPUT
            win_in.SetConsoleMode(new_mode)

            try:
                # Create the screen and invoke the wrapped function.
                win_screen = _WindowsScreen(win_out, win_in, height)
                func(win_screen)

                # Only restore the screen if we are genuinely finished - and so
                # have not raised an exception.  This stops the restore from
                # overriding any resize events.
                old_out.SetConsoleActiveScreenBuffer()
                win_out = old_out
            finally:
                # Remember the last window buffer just in case.
                _last_screen_buffer = win_out

                # Reset the original screen settings.
                win_out.SetConsoleCursorInfo(size, visible)
                win_out.SetConsoleMode(out_mode)
                win_out.SetConsoleTextAttribute(7)
                win_in.SetConsoleMode(in_mode)
        else:
            def _wrapper(win):
                cur_screen = _CursesScreen(win,
                                           height,
                                           catch_interrupt=catch_interrupt)
                func(cur_screen)

            curses.wrapper(_wrapper)

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

    def _reset(self):
        """
        Reset the Screen.
        """
        self._last_start_line = 0
        self._colour = None
        self._attr = None
        self._bg = None

    def refresh(self):
        """
        Refresh the screen.
        """
        # Scroll the screen as required to minimize redrawing.
        if self._last_start_line != self._start_line:
            self._scroll(self._start_line - self._last_start_line)
            self._last_start_line = self._start_line

        # Now draw any deltas to the scrolled screen.
        for y in range(self.height):
            for x in range(self.width):
                new_cell = self._double_buffer[y + self._start_line][x]
                if self._screen_buffer[y + self._start_line][x] != new_cell:
                    self._change_colours(new_cell[1], new_cell[2], new_cell[3])
                    self._print_at(new_cell[0], x, y)
                    self._screen_buffer[y + self._start_line][x] = new_cell

    def clear(self):
        """
        Clear the Screen of all content.
        """
        # Clear the actual terminal
        self.reset()
        self._change_colours(Screen.COLOUR_WHITE, 0, 0)
        self._clear()

    def get_key(self):
        """
        Check for a key without waiting.  This method is deprecated.  Use
        :py:meth:`.get_event` instead.
        """
        event = self.get_event()
        if event and isinstance(event, KeyboardEvent):
            return event.key_code
        return None

    @abstractmethod
    def get_event(self):
        """
        Check for any events (e.g. key-press or mouse movement) without waiting.

        :returns: A :py:obj:`.Event` object if anything was detected, otherwise
                  it returns None.
        """

    @abstractmethod
    def has_resized(self):
        """
        Check whether the screen has been re-sized.

        :returns: True when the screen has been re-sized since the last check.
        """

    def getch(self, x, y):
        """
        Get the character at a specified location.  This method is deprecated.
        Use :py:meth:`.get_from` instead.

        :param x: The x coordinate.
        :param y: The y coordinate.
        """
        return self.get_from(x, y)

    def putch(self, text, x, y, colour=7, attr=0, bg=0, transparent=False):
        """
        Print text at the specified location.  This method is deprecated.  Use
        :py:meth:`.print_at` instead.

        :param text: The (single line) text to be printed.
        :param x: The column (x coord) for the start of the text.
        :param y: The line (y coord) for the start of the text.
        :param colour: The colour of the text to be displayed.
        :param attr: The cell attribute of the text to be displayed.
        :param bg: The background colour of the text to be displayed.
        :param transparent: Whether to print spaces or not, thus giving a
            transparent effect.
        """
        self.putch(text, x, y, colour, attr, bg, transparent)

    @staticmethod
    def _unhandled_event_default(event):
        """
        Default unhandled event handler for handling simple scene navigation.
        """
        if isinstance(event, KeyboardEvent):
            c = event.key_code
            if c in (ord("X"), ord("x"), ord("Q"), ord("q")):
                raise StopApplication("User terminated app")
            if c in (ord(" "), ord("\n")):
                raise NextScene()

    def play(self, scenes, stop_on_resize=False, unhandled_input=None,
             start_scene=None):
        """
        Play a set of scenes.

        :param scenes: a list of :py:obj:`.Scene` objects to play.
        :param stop_on_resize: Whether to stop when the screen is resized.
            Default is to carry on regardless - which will typically result
            in an error. This is largely done for back-compatibility.
        :param unhandled_input: Function to call for any input not handled
            by the Scenes/Effects being played.  Defaults to a function that
            closes the application on "Q" or "X" being pressed.
        :param start_scene: The old Scene to start from.  This must have name
            that matches the name of one of the Scenes passed in.

        :raises ResizeScreenError: if the screen is resized (and allowed by
            stop_on_resize).

        The unhandled input function just takes one parameter - the input
        event that was not handled.
        """
        # Set up default unhandled input handler if needed.
        if unhandled_input is None:
            unhandled_input = self._unhandled_event_default

        # Find the starting scene.  Default to first if no match.
        index = 0
        if start_scene is not None:
            for i, scene in enumerate(scenes):
                if scene.name == start_scene.name:
                    index = i
                    break
            else:
                # No match - ignore the old Scene.
                start_scene = None

        # Mainline loop for animations
        self.clear()
        while True:
            scene = scenes[index]
            try:
                frame = 0
                if scene.clear:
                    self.clear()
                # Reset the Scene - only pass in the old scene once (otherwise
                # we repeat the population when we loop through all the Scenes).
                scene.reset(old_scene=start_scene)
                if start_scene:
                    start_scene = None
                re_sized = skipped = False
                while (scene.duration < 0 or frame < scene.duration) \
                        and not re_sized and not skipped:
                    frame += 1
                    for effect in scene.effects:
                        effect.update(frame)
                        if effect.delete_count is not None:
                            effect.delete_count -= 1
                            if effect.delete_count == 0:
                                scene.remove_effect(effect)
                    self.refresh()
                    event = self.get_event()
                    while event is not None:
                        event = scene.process_event(event)
                        if event is not None:
                            unhandled_input(event)
                        event = self.get_event()
                    re_sized = self.has_resized()
                    time.sleep(0.05)

                # Break out of the function if mandated by caller.
                if re_sized:
                    if stop_on_resize:
                        scene.exit()
                        raise ResizeScreenError("Screen resized", scene)
            except NextScene as e:
                if e.name is None:
                    # Just allow next iteration of loop
                    index += 1
                    if index >= len(scenes):
                        index = 0
                else:
                    # Find the required scene.
                    index = 0
                    for i, scene in enumerate(scenes):
                        if scene.name == e.name:
                            index = i
                            break
                    else:
                        raise RuntimeError(
                            "Could not find Scene: '{}'".format(e.name))

            except StopApplication:
                # Time to stop  - just exit the function.
                return

            # Next iteration if nothing else has exited by now.
            scene.exit()

    @abstractmethod
    def _change_colours(self, colour, attr, bg):
        """
        Change current colour if required.

        :param colour: New colour to use.
        :param attr: New attributes to use.
        :param bg: New background colour to use.
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
    def _scroll(self, lines):
        """
        Scroll the window up or down.

        :param lines: Number of lines to scroll.  Negative numbers scroll down.
        """

    @abstractmethod
    def set_title(self, title):
        """
        Set the title for this terminal/console session.  This will typically
        change the text displayed in the window title bar.

        :param title: The title to be set.
        """

if sys.platform == "win32":
    import win32console
    import win32con
    import pywintypes

    class _WindowsScreen(Screen):
        """
        Windows screen implementation.
        """

        # Virtual key code mapping.
        _KEY_MAP = {
            win32con.VK_ESCAPE: Screen.KEY_ESCAPE,
            win32con.VK_F1: Screen.KEY_F1,
            win32con.VK_F2: Screen.KEY_F2,
            win32con.VK_F3: Screen.KEY_F3,
            win32con.VK_F4: Screen.KEY_F4,
            win32con.VK_F5: Screen.KEY_F5,
            win32con.VK_F6: Screen.KEY_F6,
            win32con.VK_F7: Screen.KEY_F7,
            win32con.VK_F8: Screen.KEY_F8,
            win32con.VK_F9: Screen.KEY_F9,
            win32con.VK_F10: Screen.KEY_F10,
            win32con.VK_F11: Screen.KEY_F11,
            win32con.VK_F12: Screen.KEY_F12,
            win32con.VK_F13: Screen.KEY_F13,
            win32con.VK_F14: Screen.KEY_F14,
            win32con.VK_F15: Screen.KEY_F15,
            win32con.VK_F16: Screen.KEY_F16,
            win32con.VK_F17: Screen.KEY_F17,
            win32con.VK_F18: Screen.KEY_F18,
            win32con.VK_F19: Screen.KEY_F19,
            win32con.VK_F20: Screen.KEY_F20,
            win32con.VK_F21: Screen.KEY_F21,
            win32con.VK_F22: Screen.KEY_F22,
            win32con.VK_F23: Screen.KEY_F23,
            win32con.VK_F24: Screen.KEY_F24,
            win32con.VK_PRINT: Screen.KEY_PRINT_SCREEN,
            win32con.VK_INSERT: Screen.KEY_INSERT,
            win32con.VK_DELETE: Screen.KEY_DELETE,
            win32con.VK_HOME: Screen.KEY_HOME,
            win32con.VK_END: Screen.KEY_END,
            win32con.VK_LEFT: Screen.KEY_LEFT,
            win32con.VK_UP: Screen.KEY_UP,
            win32con.VK_RIGHT: Screen.KEY_RIGHT,
            win32con.VK_DOWN: Screen.KEY_DOWN,
            win32con.VK_PRIOR: Screen.KEY_PAGE_UP,
            win32con.VK_NEXT: Screen.KEY_PAGE_DOWN,
            win32con.VK_BACK: Screen.KEY_BACK,
            win32con.VK_TAB: Screen.KEY_TAB,
        }

        _EXTRA_KEY_MAP = {
            win32con.VK_NUMPAD0: Screen.KEY_NUMPAD0,
            win32con.VK_NUMPAD1: Screen.KEY_NUMPAD1,
            win32con.VK_NUMPAD2: Screen.KEY_NUMPAD2,
            win32con.VK_NUMPAD3: Screen.KEY_NUMPAD3,
            win32con.VK_NUMPAD4: Screen.KEY_NUMPAD4,
            win32con.VK_NUMPAD5: Screen.KEY_NUMPAD5,
            win32con.VK_NUMPAD6: Screen.KEY_NUMPAD6,
            win32con.VK_NUMPAD7: Screen.KEY_NUMPAD7,
            win32con.VK_NUMPAD8: Screen.KEY_NUMPAD8,
            win32con.VK_NUMPAD9: Screen.KEY_NUMPAD9,
            win32con.VK_MULTIPLY: Screen.KEY_MULTIPLY,
            win32con.VK_ADD: Screen.KEY_ADD,
            win32con.VK_SUBTRACT: Screen.KEY_SUBTRACT,
            win32con.VK_DECIMAL: Screen.KEY_DECIMAL,
            win32con.VK_DIVIDE: Screen.KEY_DIVIDE,
            win32con.VK_CAPITAL: Screen.KEY_CAPS_LOCK,
            win32con.VK_NUMLOCK: Screen.KEY_NUM_LOCK,
            win32con.VK_SCROLL: Screen.KEY_SCROLL_LOCK,
            win32con.VK_SHIFT: Screen.KEY_SHIFT,
            win32con.VK_CONTROL: Screen.KEY_CONTROL,
            win32con.VK_MENU: Screen.KEY_MENU,
        }

        # Foreground colour lookup table.
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

        # Background colour lookup table.
        _BG_COLOURS = {
            Screen.COLOUR_BLACK: 0,
            Screen.COLOUR_RED: win32console.BACKGROUND_RED,
            Screen.COLOUR_GREEN: win32console.BACKGROUND_GREEN,
            Screen.COLOUR_YELLOW: (win32console.BACKGROUND_RED |
                                   win32console.BACKGROUND_GREEN),
            Screen.COLOUR_BLUE: win32console.BACKGROUND_BLUE,
            Screen.COLOUR_MAGENTA: (win32console.BACKGROUND_RED |
                                    win32console.BACKGROUND_BLUE),
            Screen.COLOUR_CYAN: (win32console.BACKGROUND_BLUE |
                                 win32console.BACKGROUND_GREEN),
            Screen.COLOUR_WHITE: (win32console.BACKGROUND_RED |
                                  win32console.BACKGROUND_GREEN |
                                  win32console.BACKGROUND_BLUE)
        }

        # Attribute lookup table
        _ATTRIBUTES = {
            0: lambda x: x,
            Screen.A_BOLD: lambda x: x | win32console.FOREGROUND_INTENSITY,
            Screen.A_NORMAL: lambda x: x,
            # Windows console uses a bitmap where background is the top nibble,
            # so we can reverse by swapping nibbles.
            Screen.A_REVERSE: lambda x: ((x & 15) * 16) + ((x & 240) // 16),
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
            # Save off the screen details and set up the scrolling pad.
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

            # Opt for compatibility with Linux by default
            self._map_all = False

        def map_all_keys(self, state):
            """
            Switch on extended keyboard mapping for this Screen.

            :param state: Boolean flag where true means map all keys.

            Enabling this setting will allow Windows to tell you when any key
            is pressed, including metakeys (like shift and control) and whether
            the numeric keypad keys have been used.

            .. warning::

                Using this means your application will not be compatible across
                all platforms.
            """
            self._map_all = state

        def get_event(self):
            """
            Check for any event without waiting.
            """
            # Look for a new event and consume it if there is one.
            while len(self._stdin.PeekConsoleInput(1)) > 0:
                event = self._stdin.ReadConsoleInput(1)[0]
                if (event.EventType == win32console.KEY_EVENT and
                        event.KeyDown):
                    # Translate keys into a KeyboardEvent object.
                    key_code = ord(event.Char)
                    if event.VirtualKeyCode in self._KEY_MAP:
                        key_code = self._KEY_MAP[event.VirtualKeyCode]

                    # Sadly, we are limited to Linux terminal input and so can't
                    # return modifier states in a cross-platform way.  If the
                    # user decided not to be cross-platform, so be it, otherwise
                    # map some standard bindings for extended keys.
                    if (self._map_all and
                            event.VirtualKeyCode in self._EXTRA_KEY_MAP):
                        key_code = self._EXTRA_KEY_MAP[event.VirtualKeyCode]
                    else:
                        if (event.VirtualKeyCode == win32con.VK_TAB and
                                event.ControlKeyState & win32con.SHIFT_PRESSED):
                            key_code = Screen.KEY_BACK_TAB
                    return KeyboardEvent(key_code)
                elif event.EventType == win32console.MOUSE_EVENT:
                    # Translate into a MouseEvent object.
                    button = 0
                    if event.EventFlags == 0:
                        # Button pressed - translate it.
                        if (event.ButtonState &
                                win32con.FROM_LEFT_1ST_BUTTON_PRESSED != 0):
                            button |= MouseEvent.LEFT_CLICK
                        if (event.ButtonState &
                                win32con.RIGHTMOST_BUTTON_PRESSED != 0):
                            button |= MouseEvent.RIGHT_CLICK
                    elif event.EventFlags & win32con.DOUBLE_CLICK != 0:
                        button |= MouseEvent.DOUBLE_CLICK

                    return MouseEvent(event.MousePosition.X,
                                      event.MousePosition.Y,
                                      button)

            # If we get here, we've fully processed the event queue and found
            # nothing interesting.
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

        def _change_colours(self, colour, attr, bg):
            """
            Change current colour if required.

            :param colour: New colour to use.
            :param attr: New attributes to use.
            :param bg: New background colour to use.
            """
            # Change attribute first as this will reset colours when swapping
            # modes.
            if colour != self._colour or attr != self._attr or self._bg != bg:
                new_attr = self._ATTRIBUTES[attr](
                    self._COLOURS[colour] + self._BG_COLOURS[bg])
                self._stdout.SetConsoleTextAttribute(new_attr)
                self._attr = attr
                self._colour = colour
                self._bg = bg

        def _print_at(self, text, x, y):
            """
            Print string at the required location.

            :param text: The text string to print.
            :param x: The x coordinate
            :param y: The Y coordinate
            """
            # We can throw temporary errors on resizing, so catch and ignore
            # them on the assumption that we'll resize shortly.
            try:
                # Move the cursor if necessary
                if x != self._x or y != self._y:
                    self._stdout.SetConsoleCursorPosition(
                        win32console.PyCOORDType(x, y))

                # Print the text at the required location and update the current
                # position.
                self._stdout.WriteConsole(text)
                self._x = x + len(text)
                self._y = y
            except pywintypes.error:
                pass

        def _scroll(self, lines):
            """
            Scroll the window up or down.

            :param lines: Number of lines to scroll.  Negative numbers scroll
                down.
            """
            # Scroll the visible screen up by one line
            info = self._stdout.GetConsoleScreenBufferInfo()['Window']
            rectangle = win32console.PySMALL_RECTType(info.Left, info.Top+lines,
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

        def set_title(self, title):
            """
            Set the title for this terminal/console session.  This will
            typically change the text displayed in the window title bar.

            :param title: The title to be set.
            """
            win32console.SetConsoleTitle(title)

else:
    # UNIX compatible platform - use curses
    import curses

    class _CursesScreen(Screen):
        """
        Curses screen implementation.
        """

        # Virtual key code mapping.
        _KEY_MAP = {
            27: Screen.KEY_ESCAPE,
            curses.KEY_F1: Screen.KEY_F1,
            curses.KEY_F2: Screen.KEY_F2,
            curses.KEY_F3: Screen.KEY_F3,
            curses.KEY_F4: Screen.KEY_F4,
            curses.KEY_F5: Screen.KEY_F5,
            curses.KEY_F6: Screen.KEY_F6,
            curses.KEY_F7: Screen.KEY_F7,
            curses.KEY_F8: Screen.KEY_F8,
            curses.KEY_F9: Screen.KEY_F9,
            curses.KEY_F10: Screen.KEY_F10,
            curses.KEY_F11: Screen.KEY_F11,
            curses.KEY_F12: Screen.KEY_F12,
            curses.KEY_F13: Screen.KEY_F13,
            curses.KEY_F14: Screen.KEY_F14,
            curses.KEY_F15: Screen.KEY_F15,
            curses.KEY_F16: Screen.KEY_F16,
            curses.KEY_F17: Screen.KEY_F17,
            curses.KEY_F18: Screen.KEY_F18,
            curses.KEY_F19: Screen.KEY_F19,
            curses.KEY_F20: Screen.KEY_F20,
            curses.KEY_F21: Screen.KEY_F21,
            curses.KEY_F22: Screen.KEY_F22,
            curses.KEY_F23: Screen.KEY_F23,
            curses.KEY_F24: Screen.KEY_F24,
            curses.KEY_PRINT: Screen.KEY_PRINT_SCREEN,
            curses.KEY_IC: Screen.KEY_INSERT,
            curses.KEY_DC: Screen.KEY_DELETE,
            curses.KEY_HOME: Screen.KEY_HOME,
            curses.KEY_END: Screen.KEY_END,
            curses.KEY_LEFT: Screen.KEY_LEFT,
            curses.KEY_UP: Screen.KEY_UP,
            curses.KEY_RIGHT: Screen.KEY_RIGHT,
            curses.KEY_DOWN: Screen.KEY_DOWN,
            curses.KEY_PPAGE: Screen.KEY_PAGE_UP,
            curses.KEY_NPAGE: Screen.KEY_PAGE_DOWN,
            curses.KEY_BACKSPACE: Screen.KEY_BACK,
            9: Screen.KEY_TAB,
            curses.KEY_BTAB: Screen.KEY_BACK_TAB,
            # Terminals translate keypad keys, so no need for a special
            # mapping here.

            # Terminals don't transmit meta keys (like control, shift, etc), so
            # there's no translation for them either.
        }

        def __init__(self, win, height=200, catch_interrupt=False):
            """
            :param win: The window object as returned by the curses wrapper
                method.
            :param height: The height of the screen buffer to be used.
            :param catch_interrupt: Whether to catch SIGINT or not.
            """
            # Save off the screen details.
            super(_CursesScreen, self).__init__(
                win.getmaxyx()[0], win.getmaxyx()[1], height)
            self._screen = win
            self._screen.keypad(1)

            # Set up basic colour schemes.
            self.colours = curses.COLORS

            # Disable the cursor.
            curses.curs_set(0)

            # Non-blocking key checks.
            self._screen.nodelay(1)

            # Set up signal handler for screen resizing.
            self._re_sized = False
            signal.signal(signal.SIGWINCH, self._resize_handler)

            # Catch SIGINTs and translated them to ctrl-c if needed.
            if catch_interrupt:
                # Ignore SIGINT signals.
                signal.signal(signal.SIGINT, self._catch_interrupt)

            # Enable mouse events
            curses.mousemask(curses.ALL_MOUSE_EVENTS |
                             curses.REPORT_MOUSE_POSITION)

            # Lookup the necessary escape codes in the terminfo database.
            self._move_y_x = curses.tigetstr("cup")
            self._up_line = curses.tigetstr("ri").decode("utf-8")
            self._down_line = curses.tigetstr("ind").decode("utf-8")
            self._fg_color = curses.tigetstr("setaf")
            self._bg_color = curses.tigetstr("setab")
            if curses.tigetflag("hs"):
                self._start_title = curses.tigetstr("tsl").decode("utf-8")
                self._end_title = curses.tigetstr("fsl").decode("utf-8")
            else:
                self._start_title = self._end_title = None
            self._a_normal = curses.tigetstr("sgr0").decode("utf-8")
            self._a_bold = curses.tigetstr("bold").decode("utf-8")
            self._a_reverse = curses.tigetstr("rev").decode("utf-8")
            self._a_underline = curses.tigetstr("smul").decode("utf-8")
            self._clear_screen = curses.tigetstr("clear").decode("utf-8")

            # Conversion from Screen attributes to curses equivalents.
            self._ATTRIBUTES = {
                Screen.A_BOLD: self._a_bold,
                Screen.A_NORMAL: self._a_normal,
                Screen.A_REVERSE: self._a_reverse,
                Screen.A_UNDERLINE: self._a_underline
            }

            # We'll actually break out into low-level output, so flush any
            # high level buffers now.
            self._screen.refresh()

        def _resize_handler(self, *_):
            """
            Window resize signal handler.  We don't care about any of the
            parameters passed in beyond the object reference.
            """
            curses.endwin()
            curses.initscr()
            self._re_sized = True

        def _scroll(self, lines):
            """
            Scroll the window up or down.

            :param lines: Number of lines to scroll.  Negative numbers scroll
                down.
            """
            if lines < 0:
                sys.stdout.write("{}{}".format(
                    curses.tparm(self._move_y_x, 0, 0).decode("utf-8")),
                    self._up_line * -lines)
            else:
                sys.stdout.write("{}{}".format(curses.tparm(
                    self._move_y_x, self.height, 0).decode("utf-8"),
                    self._down_line * lines))

        def _clear(self):
            """
            Clear the Screen of all content.
            """
            sys.stdout.write(self._clear_screen)
            sys.stdout.flush()

        def refresh(self):
            """
            Refresh the screen.
            """
            super(_CursesScreen, self).refresh()
            try:
                sys.stdout.flush()
            except IOError:
                pass

        @staticmethod
        def _catch_interrupt(signal_no, frame):
            """
            SIGINT handler.  We ignore the signal and frame info passed in.
            """
            # Stop pep-8 shouting at me for unused params I can't control.
            del signal_no, frame

            # The OS already caught the ctrl-c, so inject it now for the next
            # input.
            curses.ungetch(3)
            return

        def get_event(self):
            """
            Check for an event without waiting.
            """
            # Spin through notifications until we find something we want.
            key = self._screen.getch()
            while key != -1:
                if key == curses.KEY_RESIZE:
                    # Handle screen resize
                    self._re_sized = True
                elif key == curses.KEY_MOUSE:
                    # Handle a mouse event
                    _, x, y, _, bstate = curses.getmouse()
                    buttons = 0
                    # Some Linux modes only report clicks, so check for any
                    # button down or click events.
                    if (bstate & curses.BUTTON1_PRESSED != 0 or
                            bstate & curses.BUTTON1_CLICKED != 0):
                        buttons |= MouseEvent.LEFT_CLICK
                    if (bstate & curses.BUTTON3_PRESSED != 0 or
                            bstate & curses.BUTTON3_CLICKED != 0):
                        buttons |= MouseEvent.RIGHT_CLICK
                    if bstate & curses.BUTTON1_DOUBLE_CLICKED != 0:
                        buttons |= MouseEvent.DOUBLE_CLICK
                    return MouseEvent(x, y, buttons)
                else:
                    # Handle a genuine key press.
                    if key in self._KEY_MAP:
                        # self.print_at(str(self._KEY_MAP[key]) + "  ", 0, 30)
                        return KeyboardEvent(self._KEY_MAP[key])
                    elif key != -1:
                        # self.print_at(str(key) + "  ", 0, 30)
                        return KeyboardEvent(key)

                # Wasn't interesting - discard and look at the next event.
                key = self._screen.getch()

            return None

        def has_resized(self):
            """
            Check whether the screen has been re-sized.
            """
            re_sized = self._re_sized
            self._re_sized = False
            return re_sized

        def _change_colours(self, colour, attr, bg):
            """
            Change current colour if required.

            :param colour: New colour to use.
            :param attr: New attributes to use.
            :param bg: New background colour to use.
            """
            # Change attribute first as this will reset colours when swapping
            # modes.
            if attr != self._attr:
                sys.stdout.write(self._a_normal)
                if attr != 0:
                    sys.stdout.write(self._ATTRIBUTES[attr])
                self._attr = attr
                self._colour = None
                self._bg = None

            # Now swap colours if required.
            if colour != self._colour:
                sys.stdout.write(curses.tparm(
                    self._fg_color, colour).decode("utf-8"))
                self._colour = colour
            if bg != self._bg:
                sys.stdout.write(curses.tparm(
                    self._bg_color, bg).decode("utf-8"))
                self._bg = bg

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
                msg += curses.tparm(self._move_y_x, y, x).decode("utf-8")

            msg += text

            # Print the text at the required location and update the current
            # position.
            sys.stdout.write(msg)

        def set_title(self, title):
            """
            Set the title for this terminal/console session.  This will
            typically change the text displayed in the window title bar.

            :param title: The title to be set.
            """
            if self._start_line is not None:
                sys.stdout.write("{}{}{}".format(self._start_title, title,
                                                 self._end_title))

    class _BlessedScreen(Screen):
        """
        Blessed screen implementation.  This is deprecated as it doesn't support
        mouse input.
        """

        #: Conversion from Screen attributes to blessed equivalents.
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

        def get_event(self):
            """
            Check for any event without waiting.

            .. warning::

                Blessed does not support mouse events.
            """
            key = self._terminal.inkey(timeout=0)
            return KeyboardEvent(ord(key)) if key != "" else None

        def has_resized(self):
            """
            Check whether the screen has been re-sized.
            """
            re_sized = self._re_sized
            self._re_sized = False
            return re_sized

        def _change_colours(self, colour, attr, bg):
            """
            Change current colour if required.

            :param colour: New colour to use.
            :param attr: New attributes to use.
            :param bg: New background colour to use.
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
            if bg != self._bg:
                sys.stdout.write(self._terminal.on_color(bg))
                self._bg = bg

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

        def _scroll(self, lines):
            """
            Scroll the window up or down.

            :param lines: Number of lines to scroll.  Negative numbers scroll
                down.
            """
            if lines < 0:
                sys.stdout.write("{}{}".format(
                    self._terminal.move(0, 0),
                    self._terminal.move_up() * -lines))
            else:
                sys.stdout.write("{}{}".format(
                    self._terminal.move(self.height - 1, 0),
                    self._terminal.move_down() * lines))

        def _clear(self):
            """
            Clear the terminal.
            """
            sys.stdout.write(self._terminal.clear())

        def set_title(self, title):
            """
            Set the title for this terminal/console session.  This will
            typically change the text displayed in the window title bar.

            :param title: The title to be set.
            """
            pass
