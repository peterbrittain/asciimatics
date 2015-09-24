from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from builtins import object
from builtins import range
from math import pi, sin, cos, atan2
from random import uniform, random, randint
from asciimatics.effects import Effect
from asciimatics.screen import Screen


class _Particle(object):
    """
    A single particle in a Particle Effect.
    """

    def __init__(self, chars, x, y, dx, dy, colours, delta, parm=None):
        self._chars = chars
        self._x = x
        self._y = y
        self._dx = dx
        self._dy = dy
        self._colours = colours
        self._delta = delta
        self._t = 0
        self._last = None
        self._parm = parm

    def last(self):
        return self._last

    def next(self):
        self._last = self._delta(self)
        self._t += 1
        return self._last


class Particles(Effect):
    """
    A simple particle engine for
    """

    def __init__(self, screen, count, new_particle, spawn, life_time, **kwargs):
        super(Particles, self).__init__(**kwargs)
        self._screen = screen
        self._count = count
        self._new_particle = new_particle
        self._spawn = spawn
        self._life_time = life_time
        self._particles = []
        self._time_left = 0

    def reset(self):
        self._particles = []
        self._time_left = self._spawn

    def _update(self, frame_no):
        # Spawn new particles if required
        if self._time_left > 0:
            self._time_left -= 1
            for _ in range(self._count):
                self._particles.append(self._new_particle())

        # Now draw them all
        for particle in self._particles:
            # Clear our the old particle
            last = particle.last()
            if last is not None:
                self._screen.print_at(
                    " ", last[1], last[2], last[3], last[4], last[5])

            if particle._t < self._life_time:
                # Draw the new one
                char, x, y, fg, attr, bg = particle.next()
                self._screen.print_at(char, x, y, fg, attr, bg)
            else:
                self._particles.remove(particle)

    def stop_frame(self):
        return self._stop_frame


class RingFirework(Particles):
    """
    A classic firework exploding to a simple ring.
    """

    def __init__(self, screen, x, y, life_time, **kwargs):
        super(RingFirework, self).__init__(
            screen, 15, self._new_particle, 3, life_time, **kwargs)
        self._x = x
        self._y = y
        self._colour = randint(1, 7)
        self._acceleration = 1.0 - (1.0 / life_time)

    def _new_particle(self):
        direction = uniform(0, 2 * pi)
        return _Particle("*+:. ",
                         self._x,
                         self._y,
                         sin(direction) * 3 * 8 / self._life_time,
                         cos(direction) * 1.5 * 8 / self._life_time,
                         [(self._colour, Screen.A_BOLD, 0), (0, 0, 0)],
                         self._explode)

    def _explode(self, particle):
        # Simulate some gravity and slowdown in explosion
        particle._dy = particle._dy * self._acceleration + 0.03
        particle._dx = particle._dx * self._acceleration
        particle._x += particle._dx
        particle._y += particle._dy

        colour = particle._colours[
            (len(particle._colours)-1) * particle._t // self._life_time]
        return (particle._chars[
                    (len(particle._chars)-1) * particle._t // self._life_time],
                int(particle._x),
                int(particle._y),
                colour[0], colour[1], colour[2])


class SerpentFirework(Particles):
    """
    An firework where each trail changes direction.
    """

    def __init__(self, screen, x, y, life_time, **kwargs):
        super(SerpentFirework, self).__init__(
            screen, 8, self._new_particle, 2, life_time, **kwargs)
        self._x = x
        self._y = y
        self._colour = randint(1, 7)

    def _new_particle(self):
        direction = uniform(0, 2 * pi)
        acceleration = uniform(0, 2 * pi)
        return _Particle("++++- ",
                         self._x,
                         self._y,
                         cos(direction),
                         sin(direction) / 2,
                         [(self._colour, Screen.A_BOLD, 0), (0, 0, 0)],
                         self._explode,
                         parm=acceleration)

    def _explode(self, particle):
        # Change direction like a serpent firework.
        if particle._t % 3 == 0:
            particle._parm = uniform(0, 2 * pi)
        particle._dx = (particle._dx + cos(particle._parm) / 2) * 0.8
        particle._dy = (particle._dy + sin(particle._parm) / 4) * 0.8
        particle._x += particle._dx
        particle._y += particle._dy

        colour = particle._colours[
            (len(particle._colours)-1) * particle._t // self._life_time]
        return (particle._chars[
                    (len(particle._chars)-1) * particle._t // self._life_time],
                int(particle._x),
                int(particle._y),
                colour[0], colour[1], colour[2])


class StarFirework(Particles):
    """
    A classic firework exploding to a star shape.
    """

    def __init__(self, screen, x, y, life_time, **kwargs):
        super(StarFirework, self).__init__(
            screen, 10, self._new_particle, life_time, life_time, **kwargs)
        self._x = x
        self._y = y
        self._colour = randint(1, 7)
        self._acceleration = 1.0 - (1.0 / life_time)

    def _new_particle(self):
        direction = randint(0, 16) * pi / 8
        return _Particle("...++ ",
                         self._x,
                         self._y,
                         sin(direction) * 3 * 8 / self._life_time,
                         cos(direction) * 1.5 * 8 / self._life_time,
                         [(self._colour, Screen.A_BOLD, 0), (0, 0, 0)],
                         self._explode)

    def _explode(self, particle):
        # Simulate some gravity and slowdown in explosion
        particle._dy = particle._dy * self._acceleration + 0.03
        particle._dx = particle._dx * self._acceleration
        particle._x += particle._dx
        particle._y += particle._dy

        colour = particle._colours[
            (len(particle._colours)-1) * particle._t // self._life_time]
        return (particle._chars[
                    (len(particle._chars)-1) * particle._t // self._life_time],
                int(particle._x),
                int(particle._y),
                colour[0], colour[1], colour[2])

