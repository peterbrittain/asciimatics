import curses
import os


class Screen(object):
    """
    Class to track basic state of the screen.  This constructs the necessary
    curses resources to allow us to do the ASCII animations.

    Note that all you really need to do with this class is instantiate it
    with the window object returned by the curses wrapper() method and the
    required height for your screen buffer.  This latter is important if you
    plan on using any Effects that will scroll the screen vertically (e.g.
    Scroll).  It must be big enough to handle the full scrolling of your
    selected Effect.
    """

    _256_palette = [
        '000000',
        '800000',
        '008000',
        '808000',
        '000080',
        '800080',
        '008080',
        'c0c0c0',
        '808080',
        'ff0000',
        '00ff00',
        'ffff00',
        '0000ff',
        'ff00ff',
        '00ffff',
        'ffffff',
        '000000',
        '00005f',
        '000087',
        '0000af',
        '0000d7',
        '0000ff',
        '005f00',
        '005f5f',
        '005f87',
        '005faf',
        '005fd7',
        '005fff',
        '008700',
        '00875f',
        '008787',
        '0087af',
        '0087d7',
        '0087ff',
        '00af00',
        '00af5f',
        '00af87',
        '00afaf',
        '00afd7',
        '00afff',
        '00d700',
        '00d75f',
        '00d787',
        '00d7af',
        '00d7d7',
        '00d7ff',
        '00ff00',
        '00ff5f',
        '00ff87',
        '00ffaf',
        '00ffd7',
        '00ffff',
        '5f0000',
        '5f005f',
        '5f0087',
        '5f00af',
        '5f00d7',
        '5f00ff',
        '5f5f00',
        '5f5f5f',
        '5f5f87',
        '5f5faf',
        '5f5fd7',
        '5f5fff',
        '5f8700',
        '5f875f',
        '5f8787',
        '5f87af',
        '5f87d7',
        '5f87ff',
        '5faf00',
        '5faf5f',
        '5faf87',
        '5fafaf',
        '5fafd7',
        '5fafff',
        '5fd700',
        '5fd75f',
        '5fd787',
        '5fd7af',
        '5fd7d7',
        '5fd7ff',
        '5fff00',
        '5fff5f',
        '5fff87',
        '5fffaf',
        '5fffd7',
        '5fffff',
        '870000',
        '87005f',
        '870087',
        '8700af',
        '8700d7',
        '8700ff',
        '875f00',
        '875f5f',
        '875f87',
        '875faf',
        '875fd7',
        '875fff',
        '878700',
        '87875f',
        '878787',
        '8787af',
        '8787d7',
        '8787ff',
        '87af00',
        '87af5f',
        '87af87',
        '87afaf',
        '87afd7',
        '87afff',
        '87d700',
        '87d75f',
        '87d787',
        '87d7af',
        '87d7d7',
        '87d7ff',
        '87ff00',
        '87ff5f',
        '87ff87',
        '87ffaf',
        '87ffd7',
        '87ffff',
        'af0000',
        'af005f',
        'af0087',
        'af00af',
        'af00d7',
        'af00ff',
        'af5f00',
        'af5f5f',
        'af5f87',
        'af5faf',
        'af5fd7',
        'af5fff',
        'af8700',
        'af875f',
        'af8787',
        'af87af',
        'af87d7',
        'af87ff',
        'afaf00',
        'afaf5f',
        'afaf87',
        'afafaf',
        'afafd7',
        'afafff',
        'afd700',
        'afd75f',
        'afd787',
        'afd7af',
        'afd7d7',
        'afd7ff',
        'afff00',
        'afff5f',
        'afff87',
        'afffaf',
        'afffd7',
        'afffff',
        'd70000',
        'd7005f',
        'd70087',
        'd700af',
        'd700d7',
        'd700ff',
        'd75f00',
        'd75f5f',
        'd75f87',
        'd75faf',
        'd75fd7',
        'd75fff',
        'd78700',
        'd7875f',
        'd78787',
        'd787af',
        'd787d7',
        'd787ff',
        'd7af00',
        'd7af5f',
        'd7af87',
        'd7afaf',
        'd7afd7',
        'd7afff',
        'd7d700',
        'd7d75f',
        'd7d787',
        'd7d7af',
        'd7d7d7',
        'd7d7ff',
        'd7ff00',
        'd7ff5f',
        'd7ff87',
        'd7ffaf',
        'd7ffd7',
        'd7ffff',
        'ff0000',
        'ff005f',
        'ff0087',
        'ff00af',
        'ff00d7',
        'ff00ff',
        'ff5f00',
        'ff5f5f',
        'ff5f87',
        'ff5faf',
        'ff5fd7',
        'ff5fff',
        'ff8700',
        'ff875f',
        'ff8787',
        'ff87af',
        'ff87d7',
        'ff87ff',
        'ffaf00',
        'ffaf5f',
        'ffaf87',
        'ffafaf',
        'ffafd7',
        'ffafff',
        'ffd700',
        'ffd75f',
        'ffd787',
        'ffd7af',
        'ffd7d7',
        'ffd7ff',
        'ffff00',
        'ffff5f',
        'ffff87',
        'ffffaf',
        'ffffd7',
        'ffffff',
        '080808',
        '121212',
        '1c1c1c',
        '262626',
        '303030',
        '3a3a3a',
        '444444',
        '4e4e4e',
        '585858',
        '626262',
        '6c6c6c',
        '767676',
        '808080',
        '8a8a8a',
        '949494',
        '9e9e9e',
        'a8a8a8',
        'b2b2b2',
        'bcbcbc',
        'c6c6c6',
        'd0d0d0',
        'dadada',
        'e4e4e4',
        'eeeeee',
    ]

    def __init__(self, win, height=200):
        """
        :param win: The window object as returned by the curses wrapper method.
        :param height: The height of the screen buffer to be used.
        """
        # Save off the screen details and se up the scrolling pad.
        self._screen = win
        (self.height, self.width) = self._screen.getmaxyx()
        self.buffer_height = height
        self._pad = curses.newpad(self.buffer_height, self.width)

        # Set up basic colour schemes.
        self.colours = 8
        if os.environ['TERM'] == 'xterm-256color':
            self.colours = 256
        for i in range(1, self.colours - 1):
            curses.init_pair(i, i, curses.COLOR_BLACK)

        # Disable the cursor.
        curses.curs_set(0)

        # Non-blocking key checks.
        self._pad.nodelay(1)

        # Ensure that the screen is clear and ready to go.
        self._start_line = None
        self.clear()

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
        return self._pad.getmaxyx()

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

    def putch(self, text, x, y, colour=0, attr=0, transparent=False):
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
        if y < 0:
            return
        if x < 0:
            text = text[-x:]
            x = 0
        if x + len(text) >= self.width:
            text = text[:self.width - x]
        if len(text) > 0:
            if transparent:
                for i, c in enumerate(text):
                    if c != " ":
                        self._pad.addstr(
                            y, x+i, c, curses.color_pair(colour) | attr)
            else:
                self._pad.addstr(y, x, text, curses.color_pair(colour) | attr)

    def centre(self, text, y, colour=0, attr=0, colour_map=None):
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

    def paint(self, text, x, y, colour=0, attr=0, transparent=False,
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

        See curses for definitions of the colour and attribute values.
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
                    curses.napms(50)
