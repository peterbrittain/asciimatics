from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from abc import ABCMeta, abstractmethod
from builtins import object
from builtins import range
from copy import copy
from math import pi, sin, cos, atan
from random import uniform, randint
from future.utils import with_metaclass
from asciimatics.effects import Effect
from asciimatics.screen import Screen


class Particle(object):
    """
    A single particle in a Particle Effect.
    """

    def __init__(self, chars, x, y, dx, dy, colours, life_time, move,
                 next_colour=None, next_char=None, parm=None,
                 on_create=None, on_each=None, on_destroy=None):
        """
        :param chars: String of characters to use for the particle.
        :param x: The initial horizontal position of the particle.
        :param y: The initial vertical position of the particle.
        :param dx: The initial horizontal velocity of the particle.
        :param dy: The initial vertical velocity of the particle.
        :param colours: A list of colour tuples to use for the particle.
        :param life_time: The life time of the particle.
        :param move: A function which returns the next location of the particle.
        :param next_colour: An optional function to return the next colour for
            the particle.  Defaults to a linear progression of `chars`.
        :param next_char: An optional function to return the next character for
            the particle.  Defaults to a linear progression of `colours`.
        :param parm: An optional parameter for use within any of the
        :param on_create: An optional function to spawn new particles when this
            particle first is created.
        :param on_each: An optional function to spawn new particles for every
            frame of this particle (other than creation/destruction).
        :param on_destroy: An optional function to spawn new particles when this
            particle is destroyed.
        """
        self.chars = chars
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.colours = colours
        self.time = 0
        self.life_time = life_time

        self._move = move
        self._next_colour = (
            self._default_next_colour if next_colour is None else next_colour)
        self._next_char = (
            self._default_next_char if next_char is None else next_char)
        self._last = None
        self._parm = parm
        self._on_create = on_create
        self._on_each = on_each
        self._on_destroy = on_destroy

    @staticmethod
    def _default_next_char(particle):
        """
        Default next character implementation - linear progression through
        each character.
        """
        return particle.chars[
            (len(particle.chars)-1) * particle.time // particle.life_time]

    @staticmethod
    def _default_next_colour(particle):
        """
        Default next colour implementation - linear progression through
        each colour tuple.
        """
        return particle.colours[
            (len(particle.colours) - 1) * particle.time // particle.life_time]

    def last(self):
        """
        The last attributes returned for this particle - typically used for
        clearing out the particle on the next frame.  See :py:meth:`.next` for
        details of the returned results.
        """
        return self._last

    def next(self):
        """
        The set of attributes for this particle for the next frame to be
        rendered.

        :returns: A tuple of (character, x, y, fg, attribute, bg)
        """
        # Get next particle details
        x, y = self._move(self)
        colour = self._next_colour(self)
        char = self._next_char(self)
        self._last = char, x, y, colour[0], colour[1], colour[2]
        self.time += 1

        # Trigger any configured events
        if self.time == 1 and self._on_create is not None:
            self._on_create(self)
        elif self.life_time == self.time and self._on_destroy is not None:
            self._on_destroy(self)
        elif self._on_each is not None:
            self._on_each(self)

        return self._last


class ParticleSystem(object):
    """
    A simple particle system to group together a set of :py:obj:`._Particle`
    objects to create a visual effect.  After initialization, the particle
    system will be called once per frame to be displayed to te screen.
    """

    def __init__(self, screen, x, y, count, new_particle, spawn, life_time,
                 blend=False):
        """
        :param screen: The screen to which the particle system will be rendered.
        :param x: The x location of origin of the particle system.
        :param y: The y location of origin of the particle system.
        :param count: The count of new particles to spawn on each frame.
        :param new_particle: The function to call to spawn a new particle.
        :param spawn: The number of frames for which to spawn particles.
        :param life_time: The life time of the whole particle system.
        :param blend: Whether to blend particles or not.  Defaults to False.
        """
        super(ParticleSystem, self).__init__()
        self._screen = screen
        self._x = x
        self._y = y
        self._count = count
        self._new_particle = new_particle
        self._life_time = life_time
        self.particles = []
        self.time_left = spawn
        self._blend = blend

    def update(self):
        """
        The function to draw a new frame for the particle system.
        """
        # Spawn new particles if required
        if self.time_left > 0:
            self.time_left -= 1
            for _ in range(self._count):
                self.particles.append(self._new_particle())

        # Now draw them all
        for particle in self.particles:
            # Clear our the old particle
            last = particle.last()
            if last is not None:
                char, x, y, fg, attr, bg = last
                screen_data = self._screen.get_from(x, y)
                if self._blend and screen_data:
                    char2, fg2, attr2, bg2 = screen_data
                    index = 0
                    for i, colours in enumerate(particle.colours):
                        if (fg2, attr2, bg2) == colours:
                            index = i
                            break
                    index -= 1
                    fg, attr, bg = particle.colours[max(index, 0)]
                self._screen.print_at(" ", x, y, fg, attr, bg)

            if particle.time < particle.life_time:
                # Draw the new one
                char, x, y, fg, attr, bg = particle.next()
                screen_data = self._screen.get_from(x, y)
                if self._blend and screen_data:
                    char2, fg2, attr2, bg2 = screen_data
                    index = -1
                    for i, colours in enumerate(particle.colours):
                        if (fg2, attr2, bg2) == colours:
                            index = i
                            break
                    index += 1
                    fg, attr, bg = \
                        particle.colours[min(index, len(particle.colours) - 1)]
                self._screen.print_at(char, x, y, fg, attr, bg)
            else:
                self.particles.remove(particle)


class ParticleEffect(with_metaclass(ABCMeta, Effect)):
    """
    An Effect that uses a :py:obj:`.ParticleSystem` to create the animation.
    """

    def __init__(self, screen, x, y, life_time, **kwargs):
        """
        :param screen: The Screen being used for the Scene.
        :param x: The column (x coordinate) for the origin of the effect.
        :param y: The line (y coordinate) for the origin of the effect.
        :param life_time: The life time of the effect.

        Also see the common keyword arguments in :py:obj:`.Effect`.
        """
        super(ParticleEffect, self).__init__(**kwargs)
        self._screen = screen
        self._x = x
        self._y = y
        self._life_time = life_time
        self._active_systems = []
        self.reset()

    @abstractmethod
    def reset(self):
        """
        Reset the particle effect back to its initial state.  This must be
        implemented by the child classes.
        """

    def _update(self, frame_no):
        # Take a copy in case a new system is added to the list this iteration.
        for system in copy(self._active_systems):
            if len(system.particles) > 0 or system.time_left > 0:
                system.update()
            else:
                self._active_systems.remove(system)

    @property
    def stop_frame(self):
        return self._stop_frame


class Rocket(ParticleSystem):
    """
    A rocket being launched from the ground.
    """
    def __init__(self, screen, x, y, life_time, on_destroy=None):
        """
        :param screen: The Screen being used for this particle system.
        :param x: The column (x coordinate) for the origin of the rocket.
        :param y: The line (y coordinate) for the origin of the rocket.
        :param life_time: The life time of the rocket.
        :param on_destroy: The function to call when the rocket explodes.
        """
        super(Rocket, self).__init__(
            screen, x, screen.height - 1, 1, self._new_particle, 1, life_time)
        self._end_y = y
        self._acceleration = (self._end_y - self._y) // life_time
        self._on_destroy = on_destroy

    def _new_particle(self):
        return Particle("|",
                        self._x,
                        self._y,
                        0,
                        self._acceleration,
                        [(Screen.COLOUR_YELLOW, Screen.A_BOLD, 0)],
                        self._life_time,
                        self._move,
                        on_destroy=self._on_destroy)

    def _move(self, particle):
        particle.x += particle.dx
        particle.y += particle.dy
        if particle.y <= self._end_y:
            # Rounding errors may mean we need to end slightly early.
            particle.y = self._end_y
            particle.time = self._life_time - 1

        return int(particle.x), int(particle.y)


class RingExplosion(ParticleSystem):
    """
    A classic firework explosion in a simple ring.
    """

    def __init__(self, screen, x, y, life_time):
        """
        :param screen: The Screen being used for this particle system.
        :param x: The column (x coordinate) for the origin of this explosion.
        :param y: The line (y coordinate) for the origin of this explosion.
        :param life_time: The life time of this explosion.
        """
        super(RingExplosion, self).__init__(
            screen, x, y, 30, self._new_particle, 1, life_time)
        self._colour = randint(1, 7)
        self._acceleration = 1.0 - (1.0 / life_time)

    def _new_particle(self):
        direction = uniform(0, 2 * pi)
        return Particle("***:. ",
                        self._x,
                        self._y,
                        sin(direction) * 3 * 8 / self._life_time,
                        cos(direction) * 1.5 * 8 / self._life_time,
                        [(self._colour, Screen.A_BOLD, 0),
                         (self._colour, 0, 0),
                         (0, 0, 0)],
                        self._life_time,
                        self._explode)

    def _explode(self, particle):
        # Simulate some gravity and slowdown in explosion
        particle.dy = particle.dy * self._acceleration + 0.03
        particle.dx *= self._acceleration
        particle.x += particle.dx
        particle.y += particle.dy

        return int(particle.x), int(particle.y)


class SerpentExplosion(ParticleSystem):
    """
    A firework explosion where each trail changes direction.
    """

    def __init__(self, screen, x, y, life_time):
        """
        :param screen: The Screen being used for this particle system.
        :param x: The column (x coordinate) for the origin of this explosion.
        :param y: The line (y coordinate) for the origin of this explosion.
        :param life_time: The life time of this explosion.
        """
        super(SerpentExplosion, self).__init__(
            screen, x, y, 8, self._new_particle, 2, life_time)
        self._colour = randint(1, 7)

    def _new_particle(self):
        direction = uniform(0, 2 * pi)
        acceleration = uniform(0, 2 * pi)
        return Particle("++++- ",
                        self._x,
                        self._y,
                        cos(direction),
                        sin(direction) / 2,
                        [(self._colour, Screen.A_BOLD, 0), (0, 0, 0)],
                        self._life_time,
                        self._explode,
                        parm=acceleration)

    @staticmethod
    def _explode(particle):
        # Change direction like a serpent firework.
        if particle.time % 3 == 0:
            particle._parm = uniform(0, 2 * pi)
        particle.dx = (particle.dx + cos(particle._parm) / 2) * 0.8
        particle.dy = (particle.dy + sin(particle._parm) / 4) * 0.8
        particle.x += particle.dx
        particle.y += particle.dy

        return int(particle.x), int(particle.y)


class StarExplosion(ParticleSystem):
    """
    A classic firework explosion to a Peony shape with trails.
    """

    def __init__(self, screen, x, y, life_time, points, on_each):
        """
        :param screen: The Screen being used for this particle system.
        :param x: The column (x coordinate) for the origin of this explosion.
        :param y: The line (y coordinate) for the origin of this explosion.
        :param life_time: The life time of this explosion.
        :param points: Number of points the explosion should have.
        :param on_each: The function to call to spawn a trail.
        """
        super(StarExplosion, self).__init__(
            screen, x, y, points, self._new_particle, 1, life_time)
        self._colour = randint(1, 7)
        self._acceleration = 1.0 - (1.0 / life_time)
        self._on_each = on_each
        self._points = points
        self._point_count = 0

    def _new_particle(self):
        direction = self._point_count * 2 * pi / self._points
        self._point_count += 1
        return Particle("+",
                        self._x,
                        self._y,
                        sin(direction) * 3 * 8 / self._life_time,
                        cos(direction) * 1.5 * 8 / self._life_time,
                        [(self._colour, Screen.A_BOLD, 0), (0, 0, 0)],
                        self._life_time,
                        self._explode,
                        on_each=self._on_each)

    def _explode(self, particle):
        # Simulate some gravity and slowdown in explosion
        particle.dy = particle.dy * self._acceleration + 0.03
        particle.dx *= self._acceleration
        particle.x += particle.dx
        particle.y += particle.dy

        return int(particle.x), int(particle.y)


class StarTrail(ParticleSystem):
    """
    A trail for a :py:obj:`.StarExplosion`.
    """

    def __init__(self, screen, x, y, life_time, colour):
        """
        :param screen: The Screen being used for this particle system.
        :param x: The column (x coordinate) for the origin of this trail.
        :param y: The line (y coordinate) for the origin of this trail.
        :param life_time: The life time of this trail.
        :param colour: The colour of this trail.
        """
        super(StarTrail, self).__init__(
            screen, x, y, 1, self._new_particle, 1, life_time)
        self._colour = colour

    def _new_particle(self):
        return Particle("+:,. ",
                        self._x,
                        self._y,
                        0,
                        0,
                        [(self._colour, Screen.A_BOLD, 0),
                         (self._colour, 0, 0),
                         (0, 0, 0)],
                        self._life_time,
                        self._twinkle)

    @staticmethod
    def _twinkle(particle):
        # Simulate some gravity
        particle.dy += 0.03
        particle.y += particle.dy

        return int(particle.x), int(particle.y)


class PalmExplosion(ParticleSystem):
    """
    A classic firework explosion into a palm shape.
    """

    def __init__(self, screen, x, y, life_time, on_each=None):
        """
        :param screen: The Screen being used for this particle system.
        :param x: The column (x coordinate) for the origin of this explosion.
        :param y: The line (y coordinate) for the origin of this explosion.
        :param life_time: The life time of this explosion.
        :param on_each: The function to call to spawn a trail.
        """
        super(PalmExplosion, self).__init__(
            screen, x, y, 6, self._new_particle, 2, life_time)
        self._colour = randint(1, 7)
        self._on_each = on_each
        self._arc_start = uniform(pi / 6, pi / 3)
        self._arc_end = self._arc_start + uniform(pi / 6, pi / 2)

    def _new_particle(self):
        direction = uniform(self._arc_start, self._arc_end)
        return Particle("* ",
                        self._x,
                        self._y,
                        cos(direction) * 1.5,
                        -sin(direction),
                        [(self._colour, Screen.A_BOLD, 0),
                         (0, 0, 0)],
                        self._life_time,
                        self._explode,
                        on_each=self._on_each)

    @staticmethod
    def _explode(particle):
        # Simulate some gravity
        particle.dy += 0.2
        particle.x += particle.dx
        particle.y += particle.dy

        return int(particle.x), int(particle.y)


class ExplosionFlames(ParticleSystem):
    """
    An explosion of flame and smoke.
    """

    def __init__(self, screen, x, y, life_time):
        """
        :param screen: The Screen being used for this particle system.
        :param x: The column (x coordinate) for the origin of this explosion.
        :param y: The line (y coordinate) for the origin of this explosion.
        :param life_time: The life time of this explosion.
        """
        super(ExplosionFlames, self).__init__(
            screen, x, y, 30, self._new_particle, life_time - 10, life_time,
            blend=True)

    def _new_particle(self):
        direction = uniform(0, 2 * pi)
        d = self._life_time - 10
        r = uniform(0, sin(pi * (d - self.time_left) / (d * 2))) * 3.0
        return Particle("#",
                        self._x + sin(direction) * r * 2.0,
                        self._y + cos(direction) * r,
                        sin(direction) / 2.0,
                        cos(direction) / 4.0,
                        [
                            (Screen.COLOUR_BLACK, 0, 0),
                            (Screen.COLOUR_RED, 0, 0),
                            (Screen.COLOUR_RED, Screen.A_BOLD, 0),
                            (Screen.COLOUR_YELLOW, Screen.A_BOLD, 0),
                            (Screen.COLOUR_WHITE, Screen.A_BOLD, 0),
                        ],
                        10,
                        self._burn,
                        next_colour=self._colour)

    @staticmethod
    def _burn(particle):
        particle.x += particle.dx
        particle.y += particle.dy
        return int(particle.x), int(particle.y)

    @staticmethod
    def _colour(particle):
        return particle.colours[0]


class StarFirework(ParticleEffect):
    """
    Classic rocket with star explosion.
    """

    def __init__(self, screen, x, y, life_time, **kwargs):
        """
        See :py:obj:`.ParticleEffect` for details of the parameters.
        """
        super(StarFirework, self).__init__(screen, x, y, life_time, **kwargs)

    def reset(self):
        self._active_systems = []
        self._active_systems.append(
            Rocket(self._screen, self._x, self._y, 10, on_destroy=self._next))

    def _next(self, parent):
        self._active_systems.append(
            StarExplosion(
                self._screen, parent.x, parent.y, self._life_time - 10,
                randint(6, 20), on_each=self._trail))

    def _trail(self, parent):
        if len(self._active_systems) < 150 and randint(0, 100) < 50:
            self._active_systems.insert(
                0, StarTrail(self._screen,
                             parent.x,
                             parent.y,
                             10,
                             parent.colours[0][0]))


class RingFirework(ParticleEffect):
    """
    Classic rocket with ring explosion.
    """

    def __init__(self, screen, x, y, life_time, **kwargs):
        """
        See :py:obj:`.ParticleEffect` for details of the parameters.
        """
        super(RingFirework, self).__init__(screen, x, y, life_time, **kwargs)

    def reset(self):
        self._active_systems = []
        self._active_systems.append(
            Rocket(self._screen, self._x, self._y, 10, on_destroy=self._next))

    def _next(self, parent):
        self._active_systems.append(RingExplosion(
            self._screen, parent.x, parent.y, self._life_time - 10))


class SerpentFirework(ParticleEffect):
    """
    A firework where each trail changes direction.
    """

    def __init__(self, screen, x, y, life_time, **kwargs):
        """
        See :py:obj:`.ParticleEffect` for details of the parameters.
        """
        super(SerpentFirework, self).__init__(screen, x, y, life_time, **kwargs)

    def reset(self):
        self._active_systems = []
        self._active_systems.append(
            Rocket(self._screen, self._x, self._y, 10, on_destroy=self._next))

    def _next(self, parent):
        self._active_systems.append(SerpentExplosion(
            self._screen, parent.x, parent.y, self._life_time - 10))


class PalmFirework(ParticleEffect):
    """
    Classic palm shaped firework.
    """

    def __init__(self, screen, x, y, life_time, **kwargs):
        """
        See :py:obj:`.ParticleEffect` for details of the parameters.
        """
        super(PalmFirework, self).__init__(screen, x, y, life_time, **kwargs)

    def reset(self):
        self._active_systems = []
        self._active_systems.append(
            Rocket(self._screen, self._x, self._y, 10, on_destroy=self._next))

    def _next(self, parent):
        self._active_systems.append(PalmExplosion(
            self._screen, parent.x, parent.y, self._life_time - 10,
            on_each=self._trail))

    def _trail(self, parent):
        if len(self._active_systems) < 100 and randint(0, 100) < 80:
            self._active_systems.insert(
                0, StarTrail(self._screen,
                             parent.x,
                             parent.y,
                             10,
                             parent.colours[0][0]))


class Explosion(ParticleEffect):
    """
    An explosion effect.
    """

    def __init__(self, screen, x, y, life_time, **kwargs):
        """
        See :py:obj:`.ParticleEffect` for details of the parameters.
        """
        super(Explosion, self).__init__(screen, x, y, life_time, **kwargs)

    def reset(self):
        self._active_systems = []
        self._active_systems.append(
            ExplosionFlames(self._screen, self._x, self._y, self._life_time))
