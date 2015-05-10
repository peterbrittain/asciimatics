import curses
import os
import time
from abc import ABCMeta, abstractmethod

#: Attribute styles supported by Screen formatting functions
A_BOLD = 1
A_NORMAL = 2
A_REVERSE = 3
A_UNDERLINE = 4

#: Standard colours cupported by Screen formatting functions
COLOUR_BLACK = 0
COLOUR_RED = 1
COLOUR_GREEN = 2
COLOUR_YELLOW = 3
COLOUR_BLUE = 4
COLOUR_MAGENTA = 5
COLOUR_CYAN = 6
COLOUR_WHITE = 7


class Screen(object):
    """
    Class to track basic state of the screen.  This constructs the necessary
    resources to allow us to do the ASCII animations.

    This is an abstract class that will build the correct concrete class for
    you when you call the class methods :py:obj:`.from_curses` or
    :py:obj:`.from_blessed`.

    Note that you need to define the required height for your screen buffer.
    This is important if you plan on using any Effects that will scroll the
    screen vertically (e.g. Scroll).  It must be big enough to handle the
    full scrolling of your selected Effect.
    """

    # This is an abstract class.
    __metaclass__ = ABCMeta

    # Colour palette for 256 colour xterm
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
        # Iinitialize base class variables - e.g. those used for drawing.
        self.height = height
        self.width = width
        self._start_line = None
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
    def from_blessed(cls, terminal):
        """
        Construct a new Screen from a blessed terminal.

        :param terminal: The blessed Terminal to use.
        """
        return _BlessedScreen(terminal)

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
        x = (self.width - len(text))/2
        self.paint(text, x, y, colour, attr, colour_map=colour_map)

    def paint(self, text, x, y, colour=7, attr=0, transparent=False,
              colour_map=None):
        """
        Paint multi-colour text at the defined location.

        :param text: The (single line) text to be printed.
        :param x: The columen (x coord) for the start of the text.
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
                    self.putch(c, x+i, y, colour, attr, transparent)
                else:
                    self.putch(c, x+i, y, colour_map[i][0], colour_map[i][1],
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

    def play(self, scenes):
        """
        Play a set of scenes.

        :param scenes: a list of :py:obj:`.Scene` objects to play.
        """
        while True:
            for scene in scenes:
                frame = 0
                if scene.clear:
                    self.clear()
                scene.reset()
                while scene.duration < 0 or frame < scene.duration:
                    # self.putch(
                    #    str(scene.duration - frame) + " ", 0, self._start_line)
                    frame += 1
                    for effect in scene.effects:
                        effect.update(frame)
                    self.refresh()
                    c = self.get_key()
                    if c in (ord("X"), ord("x")):
                        return
                    if c in (ord(" "), ord("\n")):
                        break
                    # curses.napms(50)
                    time.sleep(0.05)

    def move(self, x, y):
        """
        Move the drawing cursor to the specified position.

        :param x: The column (x coord) for the location to check.
        :param y: The line (y coord) for the location to check.
        """
        self._x = int(round(x, 1))
        self._y = int(round(y, 1))

    def draw(self, x, y, char=None, colour=None, thin=False):
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
        x0 = self._x * 2
        y0 = self._y * 2
        x1 = int(round(x, 1)) * 2
        y1 = int(round(y, 1)) * 2

        dx = abs(x1-x0)
        dy = abs(y1-y0)

        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1

        x_range = range(0, 2) if sx > 0 else range(1, -1, -1)
        y_range = range(0, 2) if sy > 0 else range(1, -1, -1)

        x = x0
        y = y0

        if dx > dy:
            err = dx
            while x != x1 + 2 * sx:
                next_chars = [0, 0]
                iy = y & ~1
                for ix in x_range:
                    if y >= iy and y - iy < 2:
                        next_chars[0] |= 2 ** ix * 4 ** (y % 2)
                    else:
                        next_chars[1] |= 2 ** ix * 4 ** (y % 2)
                    if not thin:
                        if y + sy >= iy and y + sy - iy < 2:
                            next_chars[0] |= 2 ** ix * 4 ** ((y+sy) % 2)
                        else:
                            next_chars[1] |= 2 ** ix * 4 ** ((y+sy) % 2)
                    err -= 2*dy
                    if err < 0:
                        y += sy
                        err += 2*dx
                    x += sx

                if char is None:
                    self.putch(self._line_chars[next_chars[0]], x/2, iy/2,
                               colour)
                    if next_chars[1] != 0:
                        self.putch(self._line_chars[next_chars[1]],
                                   x/2, iy/2+sy, colour)
                elif char == " ":
                    self.putch(char, x/2, iy/2)
                    self.putch(char, x/2, iy/2+sy)
                else:
                    self.putch(char, x/2, iy/2, colour)
        else:
            err = dy
            while y != y1 + 2 * sy:
                next_chars = [0, 0]
                ix = x & ~1
                for iy in y_range:
                    if x >= ix and x - ix < 2:
                        next_chars[0] |= 2 ** (x % 2) * 4 ** iy
                    else:
                        next_chars[1] |= 2 ** (x % 2) * 4 ** iy
                    if not thin:
                        if x + sx >= ix and x + sx - ix < 2:
                            next_chars[0] |= 2 ** ((x+sx) % 2) * 4 ** iy
                        else:
                            next_chars[1] |= 2 ** ((x+sx) % 2) * 4 ** iy
                    err -= 2*dx
                    if err < 0:
                        x += sx
                        err += 2*dy
                    y += sy

                if char is None:
                    self.putch(self._line_chars[next_chars[0]], ix/2, y/2,
                               colour)
                    if next_chars[1] != 0:
                        self.putch(
                            self._line_chars[next_chars[1]], ix/2+sx, y/2,
                            colour)
                elif char == " ":
                    self.putch(char, ix/2, y/2)
                    self.putch(char, ix/2+sx, y/2)
                else:
                    self.putch(char, ix/2, y/2, colour)


class _CursesScreen(Screen):
    """
    Curses screen implementation.
    """

    #: Conversion from Screen attributes to curses equivalents.
    ATTRIBUTES = {
        A_BOLD: curses.A_BOLD,
        A_NORMAL: curses.A_NORMAL,
        A_REVERSE: curses.A_REVERSE,
        A_UNDERLINE: curses.A_UNDERLINE
    }

    def __init__(self, win, height=200):
        """
        :param win: The window object as returned by the curses wrapper method.
        :param height: The height of the screen buffer to be used.
        """
        # Save off the screen details and se up the scrolling pad.
        super(_CursesScreen, self).__init__(
            win.getmaxyx()[0], win.getmaxyx()[1])
        self._screen = win
        self.buffer_height = height
        self._pad = curses.newpad(self.buffer_height, self.width)

        # Set up basic colour schemes.
        self.colours = 8
        if os.environ['TERM'] == 'xterm-256color':
            self.colours = 256
        for i in range(1, self.colours):
            curses.init_pair(i, i, curses.COLOR_BLACK)
        for i in range(0, self.colours):
            curses.init_pair(i + self.colours, curses.COLOR_BLACK, i)

        # Disable the cursor.
        curses.curs_set(0)

        # Non-blocking key checks.
        self._pad.nodelay(1)

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
        (self.height, self.width) = self._screen.getmaxyx()
        self._pad.refresh(self._start_line,
                          0,
                          0,
                          0,
                          self.height - 1,
                          self.width - 1)

    def get_key(self):
        """
        Check for a key without waiting.
        """
        return self._pad.getch()

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
        attr = self.ATTRIBUTES[attr] if attr in self.ATTRIBUTES else 0

        # Print whatever is left
        if len(text) > 0:
            if transparent:
                for i, c in enumerate(text):
                    if c != " ":
                        self._pad.addstr(
                            y, x+i, c, curses.color_pair(colour) | attr)
            else:
                self._pad.addstr(y, x, text, curses.color_pair(colour) | attr)


class _BlessedScreen(Screen):
    """
    Blessed screen implementation.
    """

    #: Conversion from Screen attributes to curses equivalents.
    ATTRIBUTES = {
        A_BOLD: lambda term, text: term.bold(text),
        A_NORMAL: lambda term, text: text,
        A_REVERSE: lambda term, text: term.reverse(text),
        A_UNDERLINE: lambda term, text: term.underline(text)
    }

    def __init__(self, terminal):
        """
        :param terminal: The blessed Terminal object.
        """
        # Save off the screen details and se up the scrolling pad.
        super(_BlessedScreen, self).__init__(terminal.height, terminal.width)
        self._terminal = terminal

        # Set up basic colour schemes.
        self.colours = terminal.number_of_colors

    def scroll(self):
        """
        Scroll the Screen up one line.
        """
        self._start_line += 1
        print self._terminal.move(self.height-1, 0)

    def clear(self):
        """
        Clear the Screen of all content.
        """
        print self._terminal.on_color(0) + self._terminal.color(1) + \
            self._terminal.clear()
        self._start_line = 0

    def refresh(self):
        """
        Refresh the screen.
        """
        # Blessed has no screen buffer - hence this is a NOOP.
        pass

    def get_key(self):
        """
        Check for a key without waiting.
        """
        key = self._terminal.inkey(timeout=0)
        return ord(key) if key != "" else None

    def getch(self, x, y):
        """
        Get the character at the specified location.

        :param x: The column (x coord) of the character.
        :param y: The row (y coord) of the character.

        :return: A tuple of the ASCII code of the character at the location
                 and the attributes for that character.
        """
        # TODO: Fix this!
        return ord(" "), 0

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
        # Trim text to the visible screen.
        y -= self._start_line
        if y < 0 or y >= self.height:
            return
        if x < 0:
            text = text[-x:]
            x = 0
        if x + len(text) >= self.width:
            text = text[:self.width - x]

        # Convert attribute to blessed equivalent.
        attr = self.ATTRIBUTES[attr] \
            if attr in self.ATTRIBUTES else lambda p, q: q

        if len(text) > 0:
            if transparent:
                for i, c in enumerate(text):
                    if c != " ":
                        print (self._terminal.move(y, x+i) +
                               self._terminal.color(colour) +
                               attr(self._terminal, c) +
                               self._terminal.color(colour) +
                               self._terminal.on_color(0) +
                               self._terminal.move_up)
            else:
                print(self._terminal.move(y, x) +
                      self._terminal.color(colour) +
                      attr(self._terminal, text) +
                      self._terminal.color(colour) +
                      self._terminal.on_color(0) +
                      self._terminal.move_up)
                # self._pad.addstr(y, x, text, curses.color_pair(colour) | attr)
