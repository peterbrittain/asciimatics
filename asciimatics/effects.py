from abc import ABCMeta, abstractmethod
from random import randint, random
import curses


class Effect(object):
    """
    Abstract class to handle a special effect on the screen.  An Effect can
    cover anything from a static image at the start of the Scene through to
    dynamic animations that need to be redrawn for every frame.

    The basic interaction with a :py:obj:`.Scene` is as follows:

    1.  The Scene will call :py:meth:`.Effect.reset` for all Effects when it
        starts.
    2.  The Scene will determine the number of rames required (either through
        explicit configuration) or querying :py:obj:`.stop_frame` for every
        Effect.
    3.  It will then run the scene, calling :py:meth:`.Effect.update` for
        each effect that is in the scene.

    New Effects, therefore need to implement the abstract methods on this
    class to satisy the contract with Scene.
    """
    __metaclass__ = ABCMeta

    def __init__(self, start_frame=0, stop_frame=0):
        """
        Constructor for the effect.

        :param start_frame: Start index for the effect.
        :param stop_frame: Stop index for the effect.
        """
        self._start_frame = start_frame
        self._stop_frame = stop_frame

    def update(self, frame_no):
        """
        Process the animation effect for the specified frame number.

        :param frame_no: The index of the frame being generated.
        """
        if (frame_no > self._start_frame and
                (self._stop_frame == 0 or frame_no < self._stop_frame)):
            self._update(frame_no)

    @abstractmethod
    def reset(self):
        """
        Function to reset the effect when replaying the scene.
        """

    @abstractmethod
    def _update(self, frame_no):
        """
        This effect will be called every time the mainline animator
        creates a new frame to display on the screen.

        :param frame_no: The index of the frame being generated.
        """

    @property
    @abstractmethod
    def stop_frame(self):
        """
        Last frame for this effect.  A value of zero means no specific end.
        """


class Scroll(Effect):
    """
    Special effect to scroll the screen up at a required rate.
    """

    def __init__(self, screen, rate, start_frame=0):
        """
        Constructor.

        :param screen: The Screen being used for the Scene.
        :param rate: How many frames to wait between scrolling the screen.
        :param start_frame: Start index for the effect.
        """
        super(Scroll, self).__init__(start_frame)
        self._screen = screen
        self._rate = rate
        self._last_frame = None

    def reset(self):
        self._last_frame = 0

    def _update(self, frame_no):
        if (frame_no - self._last_frame) >= self._rate:
            self._screen.scroll()
            self._last_frame = frame_no

    @property
    def stop_frame(self):
        return 0


class Cycle(Effect):
    """
    Special effect to cycle the colours on some specified text from a
    Renderer.  The text is automatically centred to the width of the Screen.
    """

    def __init__(self, screen, renderer, y, start_frame=0):
        """
        Constructor.

        :param screen: The Screen being used for the Scene.
        :param renderer: The Renderer which is to be cycled.
        :param y: The line (y coordinate) for the start of the text.
        :param start_frame: Start index for the effect.
        """
        super(Cycle, self).__init__(start_frame)
        self._screen = screen
        self._renderer = renderer
        self._y = y
        self._colour = 0

    def reset(self):
        pass

    def _update(self, frame_no):
        if frame_no % 2 == 0:
            return

        y = self._y
        for line in self._renderer.rendered_text.split("\n"):
            if self._screen.is_visible(0, y):
                self._screen.centre(line, y, self._colour)
            y += 1
        self._colour = (self._colour + 1) % 8

    @property
    def stop_frame(self):
        return 0


class BannerText(Effect):
    """
    Special effect to scroll some text (from a Renderer) horizontally like a
    banner.
    """

    def __init__(self, screen, renderer, y, colour, start_frame=0,
                 stop_frame=0):
        """
        Constructor.

        :param screen: The Screen being used for the Scene.
        :param renderer: The renderer to be scrolled
        :param y: The line (y coordinate) for the start of the text.
        :param colour: The curses colour attribute to use for the text.
        :param start_frame: Start index for the effect.
        :param stop_frame: Stop index for the effect.
        """
        super(BannerText, self).__init__(start_frame, stop_frame)
        self._screen = screen
        self._renderer = renderer
        self._y = y
        self._colour = colour
        self._text_pos = None
        self._scr_pos = None

    def reset(self):
        self._text_pos = 0
        self._scr_pos = self._screen.width

    def _update(self, frame_no):
        if self._scr_pos == 0 and self._text_pos < self._renderer.max_width:
            self._text_pos += 1

        if self._scr_pos > 0:
            self._scr_pos -= 1

        for (offset, line) in enumerate(
                self._renderer.rendered_text.split("\n")):
            line += " "
            end_pos = min(
                len(line),
                self._text_pos + self._screen.width - self._scr_pos - 1)
            self._screen.putch(line[self._text_pos:end_pos],
                               self._scr_pos,
                               self._y + offset,
                               self._colour)

    @property
    def stop_frame(self):
        return self._start_frame + self._renderer.max_width + self._screen.width


class Print(Effect):
    """
    Special effect that simply prints the specified text (from a Renderer) at
    the required location.
    """

    def __init__(self, screen, renderer, y, x=None, colour=curses.COLOR_BLACK,
                 clear=False, transparent=True, start_frame=0, stop_frame=0):
        """
        Constructor.

        :param screen: The Screen being used for the Scene.
        :param renderer: The renderer to be printed.
        :param x: The column (x coordinate) for the start of the text.
                  If not specified, defaults to centring the text on screen.
        :param y: The line (y coordinate) for the start of the text.
        :param colour: The curses colour attribute to use for the text.
        :param clear: Whether to clear the text before stopping.
        :param start_frame: Start index for the effect.
        :param stop_frame: Stop index for the effect.
        """
        super(Print, self).__init__(start_frame, stop_frame)
        self._screen = screen
        self._renderer = renderer
        self._transparent = transparent
        self._y = y
        self._x = ((self._screen.width - renderer.max_width) / 2 if x is None
                   else x)
        self._colour = colour
        self._clear = clear

    def reset(self):
        pass  # Nothing required

    def _update(self, frame_no):
        if frame_no == self._stop_frame - 1 and self._clear:
            for i in range(0, self._renderer.max_height):
                self._screen.putch(
                    " " * self._renderer.max_width, self._x, self._y + i)
        elif frame_no % 4 == 0:
            for (i, line) in enumerate(
                    self._renderer.rendered_text.split("\n")):
                self._screen.putch(line, self._x, self._y + i, self._colour,
                                   transparent=self._transparent)

    @property
    def stop_frame(self):
        return self._stop_frame


class Mirage(Effect):
    """
    Special effect to make bits of the specified text appear over time.  This
    is automatically centred.
    """

    def __init__(self, screen, renderer, y, colour, start_frame=0,
                 stop_frame=0):
        """
        Constructor.

        :param screen: The Screen being used for the Scene.
        :param renderer: The renderer to be displayed.
        :param y: The line (y coordinate) for the start of the text.
        :param colour: The curses colour attribute to use for the text.
        :param start_frame: Start index for the effect.
        :param stop_frame: Stop index for the effect.
        """
        super(Mirage, self).__init__(start_frame, stop_frame)
        self._screen = screen
        self._renderer = renderer
        self._y = y
        self._colour = colour

    def reset(self):
        pass

    def _update(self, frame_no):
        if frame_no % 2 == 0:
            return

        y = self._y
        for line in self._renderer.rendered_text.split("\n"):
            if self._screen.is_visible(0, y):
                x = (self._screen.width - len(line)) / 2
                for c in line:
                    if c != " " and random() > 0.85:
                        self._screen.putch(c, x, y, self._colour)
                    x += 1
            y += 1

    @property
    def stop_frame(self):
        return self._stop_frame


class _Star(object):
    """
    Simple class to represent a single star for the Stars special effect.
    """

    _star_chars = "..+..   ...x...  ...*...         "

    def __init__(self, screen):
        """
        Constructor.

        :param screen: The Screen being used for the Scene.
        """
        self._screen = screen
        self._cycle = None
        self._old_char = None
        self._respawn()

    def _respawn(self):
        """
        Pick a random location for the star making sure it does
        not overwrite an existing piece of text.
        """
        self._cycle = randint(0, len(self._star_chars))
        (height, width) = self._screen.dimensions
        while True:
            self._x = randint(0, width - 1)
            self._y = randint(0, height - 1)
            if self._screen.getch(self._x, self._y) == 32:
                break
        self._old_char = " "

    def update(self):
        """
        Draw the star.
        """
        if not self._screen.is_visible(self._x, self._y):
            return

        cur_char = self._screen.getch(self._x, self._y)
        if cur_char not in (ord(self._old_char), 32):
            self._respawn()

        self._cycle += 1
        if self._cycle >= len(self._star_chars):
            self._cycle = 0

        new_char = self._star_chars[self._cycle]
        if new_char == self._old_char:
            return

        self._screen.putch(new_char, self._x, self._y)
        self._old_char = new_char


class Stars(Effect):
    """
    Add random stars to the screen and make them twinkle.
    """

    def __init__(self, screen, count, start_frame=0):
        """
        Constructor.  Create the required number of stars.

        :param screen: The Screen being used for the Scene.
        :param count: The number of starts to create.
        :param start_frame: Start index for the effect.
        """
        super(Stars, self).__init__(start_frame)
        self._screen = screen
        self._max = count
        self._stars = []

    def reset(self):
        self._stars = [_Star(self._screen) for x in range(self._max)]

    def _update(self, frame_no):
        for star in self._stars:
            star.update()

    @property
    def stop_frame(self):
        return 0


class _Trail(object):
    """
    Track a single trail  for a falling character effect (a la Matrix).
    """

    def __init__(self, screen, x):
        """
        Constructor.  Create tral for  column (x) on the screen.

        :param screen: The Screen being used for the Scene.
        :param x: The column (y coordinate) for this trail to use.
        """
        self._screen = screen
        self._x = x
        self._y = 0
        self._life = 0
        self._rate = 0
        self._clear = True
        self._maybe_reseed(True)

    def _maybe_reseed(self, normal):
        """
        Randomnly create a new column once this one is finished.
        """
        self._y += self._rate
        self._life -= 1
        if self._life <= 0:
            self._clear = not self._clear if normal else True
            self._rate = randint(1, 2)
            if self._clear:
                self._y = 0
                self._life = self._screen.height / self._rate
            else:
                self._y = randint(0, self._screen.height / 2)
                self._life = \
                    randint(1, self._screen.height - self._y) / self._rate

    def update(self, reseed):
        """
        Update that trail!
        """
        if self._clear:
            for i in range(0, 3):
                self._screen.putch(" ",
                                   self._x,
                                   self._screen.start_line + self._y + i)
            self._maybe_reseed(reseed)
        else:
            for i in range(0, 3):
                self._screen.putch(chr(randint(32, 126)),
                                   self._x,
                                   self._screen.start_line + self._y + i,
                                   curses.COLOR_GREEN)
            for i in range(4, 6):
                self._screen.putch(chr(randint(32, 126)),
                                   self._x,
                                   self._screen.start_line + self._y + i,
                                   curses.COLOR_GREEN,
                                   curses.A_BOLD)
            self._maybe_reseed(reseed)


class Matrix(Effect):
    """
    Matrix-like falling green letters.
    """

    def __init__(self, screen, start_frame=0, stop_frame=0):
        """
        Constructor.

        :param screen: The Screen being used for the Scene.
        :param start_frame: Start index for the effect.
        :param stop_frame: Stop index for the effect.
        """
        super(Matrix, self).__init__(start_frame, stop_frame)
        self._screen = screen
        self._chars = None

    def reset(self):
        self._chars = [_Trail(self._screen, x) for x in
                       range(self._screen.width)]

    def _update(self, frame_no):
        if frame_no % 2 == 0:
            for char in self._chars:
                char.update((self._stop_frame == 0) or (
                    self._stop_frame - frame_no > 100))

    @property
    def stop_frame(self):
        return self._stop_frame


class Wipe(Effect):
    """
    Wipe the screen down from top to bottom.
    """

    def __init__(self, screen, start_frame=0, stop_frame=0):
        """
        Constructor.  

        :param screen: The Screen being used for the Scene.
        :param start_frame: Start index for the effect.
        :param stop_frame: Stop index for the effect.
        """
        super(Wipe, self).__init__(start_frame, stop_frame)
        self._screen = screen
        self._y = None

    def reset(self):
        self._y = 0

    def _update(self, frame_no):
        if frame_no % 2 == 0:
            if self._screen.is_visible(0, self._y):
                self._screen.putch(" " * self._screen.width, 0, self._y)
            self._y += 1

    @property
    def stop_frame(self):
        return self._stop_frame


class Sprite(Effect):
    """
    An animated character capable of following a path around the screen.
    """

    def __init__(self, screen, renderer_dict, path, colour=0, start_frame=0,
                 stop_frame=0):
        """
        Constructor.

        :param screen: The Screen being used for the Scene.
        :param renderer_dict: A dictionary of Renderers to use for displaying
        the Sprite.
        :param path: The Path for the Sprite to follow.
        :param colour: The colour to use to render the Sprite.
        :param start_frame: Start index for the effect.
        :param stop_frame: Stop index for the effect.
        """
        super(Sprite, self).__init__(start_frame, stop_frame)
        self._screen = screen
        self._renderer_dict = renderer_dict
        self._path = path
        self._index = None
        self._colour = colour
        self._old_height = None
        self._old_width = None
        self._old_x = None
        self._old_y = None
        self._dir_count = 0
        self._dir_x = None
        self._dir_y = None
        self._old_direction = None
        self.reset()

    def reset(self):
        self._dir_count = 0
        self._dir_x = None
        self._dir_y = None
        self._old_direction = None
        self._path.reset()

    def _update(self, frame_no):
        if frame_no % 2 == 0:
            # Blank out the old sprite if moved.
            if self._old_x is not None and self._old_y is not None:
                for i in range(0, self._old_height - 1):
                    self._screen.putch(
                        " " * self._old_width, self._old_x, self._old_y + i, 0)

            # Figure out the direction of the sprite, if enough time has
            # elapsed.
            (x, y) = self._path.next_pos()
            if self._dir_count % 3 == 0:
                direction = None
                if self._dir_x is not None:
                    dx = (x - self._dir_x) / 2
                    dy = y - self._dir_y
                    if dx * dx > dy * dy:
                        direction = "left" if dx < 0 else "right"
                    elif dx == 0 and dy == 0:
                        direction = "default"
                    else:
                        direction = "up" if dy < 0 else "down"
                self._dir_x = x
                self._dir_y = y
            else:
                direction = self._old_direction
            self._dir_count += 1

            # If no data - pick the default
            if direction not in self._renderer_dict:
                direction = "default"

            # Now we've done the directions, centre the sprite on the path.
            x -= self._renderer_dict[direction].max_width / 2
            y -= self._renderer_dict[direction].max_height / 2

            # Update the path index for the sprite if needed.
            if self._path.is_finished():
                self._path.reset()

            # Draw the new sprite.
            # self._screen.putch(str(x)+","+str(y)+" ", 0, 0)
            for (i, line) in enumerate(
                    self._renderer_dict[direction].rendered_text.split("\n")):
                    self._screen.putch(line, x, y + i, self._colour)

            # Remember what we need to clear up next frame.
            self._old_width = self._renderer_dict[direction].max_width
            self._old_height = self._renderer_dict[direction].max_height
            self._old_direction = direction
            self._old_x = x
            self._old_y = y

    @property
    def stop_frame(self):
        return self._stop_frame
