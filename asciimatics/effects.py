# -*- coding: utf-8 -*-
"""
This module defines `Effects` which can be used for animations.  For more details see
http://asciimatics.readthedocs.io/en/latest/animation.html
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from builtins import chr
from builtins import object
from builtins import range
from future.utils import with_metaclass
from abc import ABCMeta, abstractmethod, abstractproperty
from random import randint, random, choice
from math import sin, cos, pi
from asciimatics.paths import DynamicPath
from asciimatics.screen import Screen
import datetime


class Effect(with_metaclass(ABCMeta, object)):
    """
    Abstract class to handle a special effect on the screen.  An Effect can
    cover anything from a static image at the start of the Scene through to
    dynamic animations that need to be redrawn for every frame.

    The basic interaction with a :py:obj:`.Scene` is as follows:

    1.  The Scene will register with the Effect when it as added using
        :py:meth:`.register_scene`.
    2.  The Scene will call :py:meth:`.Effect.reset` for all Effects when it
        starts.
    3.  The Scene will determine the number of frames required (either through
        explicit configuration or querying :py:obj:`.stop_frame` for every
        Effect).
    4.  It will then run the scene, calling :py:meth:`.Effect.update` for
        each effect that is in the scene.  The base Effect will then call the
        abstract method _update() if the effect should be visible.
    5.  If any keys are pressed or the mouse moved/clicked, the scene will call
        :py:meth:`.Effect.process_event` for each event, allowing the effect to
        act on it if needed.

    New Effects, therefore need to implement the abstract methods on this
    class to satisfy the contract with Scene.  Since most effects don't require
    user interaction, the default process_event() implementation will ignore the
    event (and so effects don't need to implement this method unless needed).
    """

    def __init__(self, screen, start_frame=0, stop_frame=0, delete_count=None):
        """
        :param screen: The Screen that will render this Effect.
        :param start_frame: Start index for the effect.
        :param stop_frame: Stop index for the effect.
        :param delete_count: Number of frames before this effect is deleted.
        """
        self._screen = screen
        self._start_frame = start_frame
        self._stop_frame = stop_frame
        self._delete_count = delete_count
        self._scene = None

    def update(self, frame_no):
        """
        Process the animation effect for the specified frame number.

        :param frame_no: The index of the frame being generated.
        """
        if (frame_no >= self._start_frame and
                (self._stop_frame == 0 or frame_no < self._stop_frame)):
            self._update(frame_no)

    def register_scene(self, scene):
        """
        Register the Scene that owns this Effect.

        :param scene: The Scene to be registered
        """
        self._scene = scene

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

    @abstractproperty
    def stop_frame(self):
        """
        Last frame for this effect.  A value of zero means no specific end.
        """

    @property
    def delete_count(self):
        """
        The number of frames before this Effect should be deleted.
        """
        return self._delete_count

    @property
    def screen(self):
        """
        The Screen that will render this Effect.
        """
        return self._screen

    @delete_count.setter
    def delete_count(self, value):
        self._delete_count = value

    @property
    def frame_update_count(self):
        """
        The number of frames before this Effect should be updated.

        Increasing this number potentially reduces the CPU load of a Scene (if
        no other Effect needs to be scheduled sooner), but can affect perceived
        responsiveness of the Scene if it is too long.  Handle with care!

        A value of 0 means refreshes are not required beyond a response to an
        input event.  It defaults to 1 for all Effects.
        """
        return 1

    @property
    def safe_to_default_unhandled_input(self):
        """
        Whether it is safe to use the default handler for any unhandled input
        from this Effect.

        A value of False means that asciimatics should not use the default
        handler.  This is typically the case for Frames.
        """
        return True

    @property
    def scene(self):
        """
        The Scene that owns this Effect.
        """
        return self._scene

    # pylint: disable=no-self-use
    def process_event(self, event):
        """
        Process any input event.

        :param event: The event that was triggered.
        :returns: None if the Effect processed the event, else the original
                  event.
        """
        return event


class Scroll(Effect):
    """
    Special effect to scroll the screen up at a required rate.  Since the Screen
    has a limited size and will not wrap, ensure that it is large enough to
    Scroll for the desired time.
    """

    def __init__(self, screen, rate, **kwargs):
        """
        :param screen: The Screen being used for the Scene.
        :param rate: How many frames to wait between scrolling the screen.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(Scroll, self).__init__(screen, **kwargs)
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
    This effect is not compatible with multi-colour rendered text.
    """

    def __init__(self, screen, renderer, y, **kwargs):
        """
        :param screen: The Screen being used for the Scene.
        :param renderer: The Renderer which is to be cycled.
        :param y: The line (y coordinate) for the start of the text.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(Cycle, self).__init__(screen, **kwargs)
        self._renderer = renderer
        self._y = y
        self._colour = 0

    def reset(self):
        pass

    def _update(self, frame_no):
        if frame_no % 2 == 0:
            return

        y = self._y
        image, _ = self._renderer.rendered_text
        for line in image:
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

    def __init__(self, screen, renderer, y, colour, bg=Screen.COLOUR_BLACK,
                 **kwargs):
        """
        :param screen: The Screen being used for the Scene.
        :param renderer: The renderer to be scrolled
        :param y: The line (y coordinate) for the start of the text.
        :param colour: The default foreground colour to use for the text.
        :param bg: The default background colour to use for the text.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(BannerText, self).__init__(screen, **kwargs)
        self._renderer = renderer
        self._y = y
        self._colour = colour
        self._bg = bg
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

        image, colours = self._renderer.rendered_text
        for (i, line) in enumerate(image):
            line += " "
            colours[i].append((self._colour, 2, self._bg))
            end_pos = min(
                len(line),
                self._text_pos + self._screen.width - self._scr_pos)
            self._screen.paint(line[self._text_pos:end_pos],
                               self._scr_pos,
                               self._y + i,
                               self._colour,
                               bg=self._bg,
                               colour_map=colours[i][self._text_pos:end_pos])

    @property
    def stop_frame(self):
        return self._start_frame + self._renderer.max_width + self._screen.width


class Print(Effect):
    """
    Special effect that simply prints the specified text (from a Renderer) at
    the required location.
    """

    def __init__(self, screen, renderer, y, x=None, colour=7, attr=0, bg=0,
                 clear=False, transparent=True, speed=4, **kwargs):
        """
        :param screen: The Screen being used for the Scene.
        :param renderer: The renderer to be printed.
        :param x: The column (x coordinate) for the start of the text.
                  If not specified, defaults to centring the text on screen.
        :param y: The line (y coordinate) for the start of the text.
        :param colour: The foreground colour to use for the text.
        :param attr: The colour attribute to use for the text.
        :param bg: The background colour to use for the text.
        :param clear: Whether to clear the text before stopping.
        :param speed: The refresh rate in frames between refreshes.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(Print, self).__init__(screen, **kwargs)
        self._renderer = renderer
        self._transparent = transparent
        self._y = y
        self._x = ((self._screen.width - renderer.max_width) // 2 if x is None
                   else x)
        self._colour = colour
        self._attr = attr
        self._bg = bg
        self._clear = clear
        self._speed = speed
        self._frame_no = 0

    def reset(self):
        pass  # Nothing required

    def _update(self, frame_no):
        self._frame_no = frame_no
        if self._clear and \
                (frame_no == self._stop_frame - 1) or (self._delete_count == 1):
            for i in range(0, self._renderer.max_height):
                self._screen.print_at(" " * self._renderer.max_width,
                                      self._x,
                                      self._y + i,
                                      bg=self._bg)
        elif frame_no % self._speed == 0:
            image, colours = self._renderer.rendered_text
            for (i, line) in enumerate(image):
                self._screen.paint(line, self._x, self._y + i, self._colour,
                                   attr=self._attr,
                                   bg=self._bg,
                                   transparent=self._transparent,
                                   colour_map=colours[i])

    @property
    def stop_frame(self):
        return self._stop_frame

    @property
    def frame_update_count(self):
        # Only demand update for next update frame.
        return self._speed - (self._frame_no % self._speed)


class Mirage(Effect):
    """
    Special effect to make bits of the specified text appear over time.  This
    text is automatically centred on the screen.
    """

    def __init__(self, screen, renderer, y, colour, **kwargs):
        """
        :param screen: The Screen being used for the Scene.
        :param renderer: The renderer to be displayed.
        :param y: The line (y coordinate) for the start of the text.
        :param colour: The colour attribute to use for the text.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(Mirage, self).__init__(screen, **kwargs)
        self._renderer = renderer
        self._y = y
        self._colour = colour

    def reset(self):
        pass

    def _update(self, frame_no):
        if frame_no % 2 == 0:
            return

        y = self._y
        image, colours = self._renderer.rendered_text
        for i, line in enumerate(image):
            if self._screen.is_visible(0, y):
                x = (self._screen.width - len(line)) // 2
                for j, c in enumerate(line):
                    if c != " " and random() > 0.85:
                        if colours[i][j][0] is not None:
                            self._screen.print_at(c, x, y,
                                                  colours[i][j][0],
                                                  colours[i][j][1])
                        else:
                            self._screen.print_at(c, x, y, self._colour)
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
            if self._screen.get_from(self._x, self._y)[0] == 32:
                break
        self._old_char = " "

    def update(self):
        """
        Draw the star.
        """
        if not self._screen.is_visible(self._x, self._y):
            self._respawn()

        cur_char, _, _, _ = self._screen.get_from(self._x, self._y)
        if cur_char not in (ord(self._old_char), 32):
            self._respawn()

        self._cycle += 1
        if self._cycle >= len(self._star_chars):
            self._cycle = 0

        new_char = self._star_chars[self._cycle]
        if new_char == self._old_char:
            return

        self._screen.print_at(new_char, self._x, self._y)
        self._old_char = new_char


class Stars(Effect):
    """
    Add random stars to the screen and make them twinkle.
    """

    def __init__(self, screen, count, **kwargs):
        """
        :param screen: The Screen being used for the Scene.
        :param count: The number of starts to create.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(Stars, self).__init__(screen, **kwargs)
        self._max = count
        self._stars = []

    def reset(self):
        self._stars = [_Star(self._screen) for _ in range(self._max)]

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
        Randomly create a new column once this one is finished.
        """
        self._y += self._rate
        self._life -= 1
        if self._life <= 0:
            self._clear = not self._clear if normal else True
            self._rate = randint(1, 2)
            if self._clear:
                self._y = 0
                self._life = self._screen.height // self._rate
            else:
                self._y = randint(0, self._screen.height // 2) - \
                    self._screen.height // 4
                self._life = \
                    randint(1, self._screen.height - self._y) // self._rate

    def update(self, reseed):
        """
        Update that trail!

        :param reseed: Whether we are in the normal reseed cycle or not.
        """
        if self._clear:
            for i in range(0, 3):
                self._screen.print_at(" ",
                                      self._x,
                                      self._screen.start_line + self._y + i)
            self._maybe_reseed(reseed)
        else:
            for i in range(0, 3):
                self._screen.print_at(chr(randint(32, 126)),
                                      self._x,
                                      self._screen.start_line + self._y + i,
                                      Screen.COLOUR_GREEN)
            for i in range(4, 6):
                self._screen.print_at(chr(randint(32, 126)),
                                      self._x,
                                      self._screen.start_line + self._y + i,
                                      Screen.COLOUR_GREEN,
                                      Screen.A_BOLD)
            self._maybe_reseed(reseed)


class Matrix(Effect):
    """
    Matrix-like falling green letters.
    """

    def __init__(self, screen, **kwargs):
        """
        :param screen: The Screen being used for the Scene.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(Matrix, self).__init__(screen, **kwargs)
        self._chars = []

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

    def __init__(self, screen, bg=0, **kwargs):
        """
        :param screen: The Screen being used for the Scene.
        :param bg: Optional background colour to use for the wipe.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(Wipe, self).__init__(screen, **kwargs)
        self._bg = bg
        self._y = None

    def reset(self):
        self._y = 0

    def _update(self, frame_no):
        if frame_no % 2 == 0:
            if self._screen.is_visible(0, self._y):
                self._screen.print_at(
                    " " * self._screen.width, 0, self._y, bg=self._bg)
            self._y += 1

    @property
    def stop_frame(self):
        return self._stop_frame


class Sprite(Effect):
    """
    An animated character capable of following a path around the screen.
    """

    def __init__(self, screen, renderer_dict, path, colour=Screen.COLOUR_WHITE,
                 clear=True, **kwargs):
        """
        :param screen: The Screen being used for the Scene.
        :param renderer_dict: A dictionary of Renderers to use for displaying
                              the Sprite.
        :param path: The Path for the Sprite to follow.
        :param colour: The colour to use to render the Sprite.
        :param clear: Whether to clear out old images or leave a trail.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(Sprite, self).__init__(screen, **kwargs)
        self._renderer_dict = renderer_dict
        self._path = path
        self._index = None
        self._colour = colour
        self._clear = clear
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
        self._old_x = None
        self._old_y = None
        self._old_direction = None
        self._path.reset()

    def last_position(self):
        """
        Returns the last position of this Sprite as a tuple
        (x, y, width, height).
        """
        return self._old_x, self._old_y, self._old_width, self._old_height

    def overlaps(self, other, use_new_pos=False):
        """
        Check whether this Sprite overlaps another.

        :param other: The other Sprite to check for an overlap.
        :param use_new_pos: Whether to use latest position (due to recent
            update).  Defaults to False.
        :returns: True if the two Sprites overlap.
        """
        (x, y) = self._path.next_pos() if use_new_pos else (self._old_x,
                                                            self._old_y)
        w = self._old_width
        h = self._old_height

        x2, y2, w2, h2 = other.last_position()

        if ((x > x2 + w2 - 1) or (x2 > x + w - 1) or
                (y > y2 + h2 - 1) or (y2 > y + h - 1)):
            return False
        else:
            return True

    def _update(self, frame_no):
        if frame_no % 2 == 0:
            # Blank out the old sprite if moved.
            if (self._clear and
                    self._old_x is not None and self._old_y is not None):
                for i in range(0, self._old_height):
                    self._screen.print_at(
                        " " * self._old_width, self._old_x, self._old_y + i, 0)

            # Don't draw a new one if we're about to stop the Sprite.
            if self._delete_count is not None and self._delete_count <= 2:
                return

            # Figure out the direction of the sprite, if enough time has
            # elapsed.
            (x, y) = self._path.next_pos()
            if self._dir_count % 3 == 0:
                direction = None
                if self._dir_x is not None:
                    dx = (x - self._dir_x) // 2
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
            x -= self._renderer_dict[direction].max_width // 2
            y -= self._renderer_dict[direction].max_height // 2

            # Update the path index for the sprite if needed.
            if self._path.is_finished():
                self._path.reset()

            # Draw the new sprite.
            # self._screen.print_at(str(x)+","+str(y)+" ", 0, 0)
            image, colours = self._renderer_dict[direction].rendered_text
            for (i, line) in enumerate(image):
                self._screen.paint(line, x, y + i, self._colour,
                                   colour_map=colours[i])

            # Remember what we need to clear up next frame.
            self._old_width = self._renderer_dict[direction].max_width
            self._old_height = self._renderer_dict[direction].max_height
            self._old_direction = direction
            self._old_x = x
            self._old_y = y

    @property
    def stop_frame(self):
        return self._stop_frame

    def process_event(self, event):
        if isinstance(self._path, DynamicPath):
            return self._path.process_event(event)
        else:
            return event


class _Flake(object):
    """
    Track a single snow flake.
    """

    _snow_chars = ".+*"
    _drift_chars = " ,;#@"

    def __init__(self, screen):
        """
        :param screen: The Screen being used for the Scene.
        """
        self._screen = screen
        self._x = 0
        self._y = 0
        self._rate = 0
        self._char = None
        self._reseed()

    def _reseed(self):
        """
        Randomly create a new snowflake once this one is finished.
        """
        self._char = choice(self._snow_chars)
        self._rate = randint(1, 3)
        self._x = randint(0, self._screen.width - 1)
        self._y = self._screen.start_line + randint(0, self._rate)

    def update(self, reseed):
        """
        Update that snowflake!

        :param reseed: Whether we are in the normal reseed cycle or not.
        """
        self._screen.print_at(" ", self._x, self._y)
        current_char = None
        for _ in range(self._rate):
            self._y += 1
            current_char, _, _, _ = self._screen.get_from(self._x, self._y)
            if current_char != 32:
                break

        if ((current_char in [ord(x) for x in self._snow_chars + " "]) and
                (self._y < self._screen.start_line + self._screen.height)):
            self._screen.print_at(self._char,
                                  self._x,
                                  self._y)
        else:
            if self._y >= self._screen.start_line + self._screen.height:
                self._y = self._screen.start_line + self._screen.height - 1

            drift_index = self._drift_chars.find(chr(current_char))
            if 0 <= drift_index < len(self._drift_chars) - 1:
                drift_char = self._drift_chars[drift_index + 1]
                self._screen.print_at(drift_char, self._x, self._y)
            else:
                self._screen.print_at(",", self._x, self._y - 1)
            if reseed:
                self._reseed()


class Snow(Effect):
    """
    Settling snow effect.
    """

    def __init__(self, screen, **kwargs):
        """
        :param screen: The Screen being used for the Scene.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(Snow, self).__init__(screen, **kwargs)
        self._chars = []

    def reset(self):
        # Make the snow start falling one flake at a time.
        self._chars = []

    def _update(self, frame_no):
        if frame_no % 3 == 0:
            if len(self._chars) < self._screen.width // 3:
                self._chars.append(_Flake(self._screen))

            for char in self._chars:
                char.update((self._stop_frame == 0) or (
                    self._stop_frame - frame_no > 100))

    @property
    def stop_frame(self):
        return self._stop_frame


class Clock(Effect):
    """
    An ASCII ticking clock (telling the correct local time).
    """

    def __init__(self, screen, x, y, r, bg=Screen.COLOUR_BLACK, **kwargs):
        """
        :param screen: The Screen being used for the Scene.
        :param x: X coordinate for the centre of the clock.
        :param y: Y coordinate for the centre of the clock.
        :param r: Radius of the clock.
        :param bg: Background colour for the clock.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(Clock, self).__init__(screen, **kwargs)
        self._x = x
        self._y = y
        self._r = r
        self._bg = bg
        self._old_time = None

    def reset(self):
        pass

    def _update(self, frame_no):
        # Helper functions to map various time elements
        def _hour_pos(t):
            return (t.tm_hour + t.tm_min / 60) * pi / 6

        def _min_pos(t):
            return t.tm_min * pi / 30

        def _sec_pos(t):
            return t.tm_sec * pi / 30

        # Clear old hands
        if self._old_time is not None:
            ot = self._old_time
            self._screen.move(self._x, self._y)
            self._screen.draw(self._x + (self._r * sin(_hour_pos(ot))),
                              self._y - (self._r * cos(_hour_pos(ot)) / 2),
                              char=" ", bg=self._bg)
            self._screen.move(self._x, self._y)
            self._screen.draw(self._x + (self._r * sin(_min_pos(ot)) * 2),
                              self._y - (self._r * cos(_min_pos(ot))),
                              char=" ", bg=self._bg)
            self._screen.move(self._x, self._y)
            self._screen.draw(self._x + (self._r * sin(_sec_pos(ot)) * 2),
                              self._y - (self._r * cos(_sec_pos(ot))),
                              char=" ", bg=self._bg)

        # Draw new ones
        new_time = datetime.datetime.now().timetuple()
        self._screen.move(self._x, self._y)
        self._screen.draw(self._x + (self._r * sin(_hour_pos(new_time))),
                          self._y - (self._r * cos(_hour_pos(new_time)) / 2),
                          colour=Screen.COLOUR_WHITE, bg=self._bg)
        self._screen.move(self._x, self._y)
        self._screen.draw(self._x + (self._r * sin(_min_pos(new_time)) * 2),
                          self._y - (self._r * cos(_min_pos(new_time))),
                          colour=Screen.COLOUR_WHITE, bg=self._bg)
        self._screen.move(self._x, self._y)
        self._screen.draw(self._x + (self._r * sin(_sec_pos(new_time)) * 2),
                          self._y - (self._r * cos(_sec_pos(new_time))),
                          colour=Screen.COLOUR_CYAN, bg=self._bg, thin=True)
        self._screen.print_at("o", self._x, self._y, Screen.COLOUR_YELLOW,
                              Screen.A_BOLD, bg=self._bg)
        self._old_time = new_time

    @property
    def stop_frame(self):
        return self._stop_frame

    @property
    def frame_update_count(self):
        # Only need to update once a second
        return 20


class Cog(Effect):
    """
    A rotating cog.
    """

    def __init__(self, screen, x, y, radius, direction=1, colour=7, **kwargs):
        """
        :param screen: The Screen being used for the Scene.
        :param x: X coordinate of the centre of the cog.
        :param y: Y coordinate of the centre of the cog.
        :param radius: The radius of the cog.
        :param direction: The direction of rotation. Positive numbers are
            anti-clockwise, negative numbers clockwise.
        :param colour: The colour of the cog.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(Cog, self).__init__(screen, **kwargs)
        self._x = x
        self._y = y
        self._radius = radius
        self._old_frame = 0
        self._rate = 2
        self._direction = direction
        self._colour = colour

    def reset(self):
        pass

    def _update(self, frame_no):
        # Rate limit the animation
        if frame_no % self._rate != 0:
            return

        # Function to plot.
        def f(p):
            return self._x + (self._radius * 2 - (6 * (p // 4 % 2))) * sin(
                (self._old_frame + p) * pi / 40)

        def g(p):
            return self._y + (self._radius - (3 * (p // 4 % 2))) * cos(
                (self._old_frame + p) * pi / 40)

        # Clear old wave.
        if self._old_frame != 0:
            self._screen.move(f(0), g(0))
            for x in range(81):
                self._screen.draw(f(x), g(x), char=" ")

        # Draw new one
        self._old_frame += self._direction
        self._screen.move(f(0), g(0))
        for x in range(81):
            self._screen.draw(f(x), g(x), colour=self._colour)

    @property
    def stop_frame(self):
        return self._stop_frame


class RandomNoise(Effect):
    """
    White noise effect - like an old analogue TV set that isn't quite tuned
    right.  If desired, a signal image (from a renderer) can be specified that
    will appear from the noise.
    """

    def __init__(self, screen, signal=None, **kwargs):
        """
        :param screen: The Screen being used for the Scene.
        :param signal: The renderer to use as the 'signal' in the white noise.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(RandomNoise, self).__init__(screen, **kwargs)
        self._signal = signal
        self._strength = 0.0
        self._step = 0.0

    def reset(self):
        self._strength = 0.0
        self._step = -0.01

    def _update(self, frame_no):
        if self._signal:
            start_x = int((self._screen.width - self._signal.max_width) // 2)
            start_y = int((self._screen.height - self._signal.max_height) // 2)
            text, colours = self._signal.rendered_text
        else:
            start_x = start_y = 0
            text, colours = "", []

        for y in range(self._screen.height):
            if self._strength < 1.0:
                offset = randint(0, int(6 - 6 * self._strength))
            else:
                offset = 0
            for x in range(self._screen.width):
                ix = x - start_x
                iy = y - start_y
                if (self._signal and random() <= self._strength and
                        x >= start_x and y >= start_y and
                        iy < len(text) and ix + offset < len(text[iy])):
                    self._screen.paint(text[iy][ix + offset],
                                       x, y,
                                       colour_map=[colours[iy][ix]])
                else:
                    if random() < 0.2:
                        self._screen.print_at(chr(randint(33, 126)), x, y)

        # Tune the signal
        self._strength += self._step
        if self._strength >= 1.25 or self._strength <= -0.5:
            self._step = -self._step

    @property
    def stop_frame(self):
        return self._stop_frame


class Julia(Effect):
    """
    Julia Set generator.  See http://en.wikipedia.org/wiki/Julia_set for more
    information on this fractal.
    """

    # Character set to use so we still get a grey scale for low-colour systems.
    _greyscale = '@@&&99##GGHHhh3322AAss;;::.. '

    # Colour palette for 256 colour xterm mode.
    _256_palette = [196, 202, 208, 214, 220, 226,
                    154, 118, 82, 46,
                    47, 48, 49, 50, 51,
                    45, 39, 33, 27, 21,
                    57, 93, 129, 201,
                    200, 199, 198, 197, 0]

    def __init__(self, screen, c=None, **kwargs):
        """
        :param screen: The Screen being used for the Scene.
        :param c: The starting value of 'c' for the Julia Set.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(Julia, self).__init__(screen, **kwargs)
        self._width = screen.width
        self._height = screen.height
        self._centre = [0.0, 0.0]
        self._size = [4.0, 4.0]
        self._min_x = self._min_y = -2.0
        self._max_x = self._max_y = 2.0
        self._c = c if c is not None else [-0.8, 0.156]
        self._scale = 0.995

    def reset(self):
        pass

    def _update(self, frame_no):
        # Draw the new image to the required block.
        c = complex(self._c[0], self._c[1])
        sx = self._centre[0] - (self._size[0] / 2.0)
        sy = self._centre[1] - (self._size[1] / 2.0)
        for y in range(self._height):
            for x in range(self._width):
                z = complex(sx + self._size[0] * (x / self._width),
                            sy + self._size[1] * (y / self._height))
                n = len(self._256_palette)
                while abs(z) < 10 and n >= 1:
                    z = z ** 2 + c
                    n -= 1
                colour = \
                    self._256_palette[
                        n - 1] if self._screen.colours >= 256 else 7
                self._screen.print_at(self._greyscale[n - 1], x, y, colour)

        # Zoom
        self._size = [i * self._scale for i in self._size]
        area = self._size[0] * self._size[1]
        if area <= 4.0 or area >= 16:
            self._scale = 1.0 / self._scale

        # Rotate
        self._c = [self._c[0] * cos(pi / 180) - self._c[1] * sin(pi / 180),
                   self._c[0] * sin(pi / 180) + self._c[1] * cos(pi / 180)]

    @property
    def stop_frame(self):
        return self._stop_frame
