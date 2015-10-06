from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from abc import ABCMeta, abstractmethod
from builtins import object
from builtins import range
from math import pi, sin, cos
from random import uniform, randint
from future.utils import with_metaclass
from asciimatics.effects import Effect
from asciimatics.screen import Screen


class _Particle(object):
    """
    A single particle in a Particle Effect.
    """

    def __init__(self, chars, x, y, dx, dy, colours, delta, parm=None,
                 on_create=None, on_each=None, on_destroy=None):
        self.chars = chars
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.colours = colours
        self.time = 0

        self._delta = delta
        self._last = None
        self._parm = parm
        self._on_create = on_create
        self._on_each = on_each
        self._on_destroy = on_destroy

    def last(self):
        return self._last

    def next(self, end_time):
        # Get next particle details
        self._last = self._delta(self)
        self.time += 1

        # Trigger any configured events
        if self.time == 1 and self._on_create is not None:
            self._on_create(self)
        elif end_time == self.time and self._on_destroy is not None:
            self._on_destroy(self)
        elif self._on_each is not None:
            self._on_each(self)

        return self._last


class ParticleSystem(object):
    """
    A simple particle system to group together a set of :py:obj:`._Particle`
    objects to create a visual effect.
    """

    def __init__(self, screen, x, y, count, new_particle, spawn, life_time):
        super(ParticleSystem, self).__init__()
        self._screen = screen
        self._x = x
        self._y = y
        self._count = count
        self._new_particle = new_particle
        self._life_time = life_time
        self._particles = []
        self._time_left = spawn

    def update(self):
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

            if particle.time < self._life_time:
                # Draw the new one
                char, x, y, fg, attr, bg = particle.next(self._life_time)
                self._screen.print_at(char, x, y, fg, attr, bg)
            else:
                self._particles.remove(particle)

    def __str__(self):
        return "ParticleSystem ({} {} {})".format(
            self._count, self._life_time, self._time_left)


class ParticleEffect(with_metaclass(ABCMeta, Effect)):
    """
    An Effect that uses a :py:obj:`.ParticleSystem` to create the animation.
    """

    def __init__(self, screen, x, y, life_time, **kwargs):
        super(ParticleEffect, self).__init__(**kwargs)
        self._screen = screen
        self._x = x
        self._y = y
        self._life_time = life_time
        self._active_systems = []

    @abstractmethod
    def reset(self):
        """
        Reset the particle effect back to its initial state.
        """

    def _update(self, frame_no):
        # Take a copy in case a new system is added to the list this iteration.
        for system in self._active_systems.copy():
            if len(system._particles) > 0 or system._time_left > 0:
                system.update()
            else:
                self._active_systems.remove(system)

    def stop_frame(self):
        return self._stop_frame


class Rocket(ParticleSystem):
    """
    A rocket being launched from the ground.
    """
    def __init__(self, screen, x, y, life_time, on_destroy=None):
        super(Rocket, self).__init__(
            screen, x, screen.height - 1, 1, self._new_particle, 1, life_time)
        self._end_y = y
        self._acceleration = (self._end_y - self._y) // life_time
        self._on_destroy = on_destroy

    def _new_particle(self):
        return _Particle("|",
                         self._x,
                         self._y,
                         0,
                         self._acceleration,
                         [(Screen.COLOUR_YELLOW, Screen.A_BOLD, 0)],
                         self._move,
                         on_destroy=self._on_destroy)

    def _move(self, particle):
        particle.x += particle.dx
        particle.y += particle.dy
        if particle.y <= self._end_y:
            # Rounding errors may mean we need to end slightly early.
            particle.y = self._end_y
            particle.time = self._life_time - 1

        colour = particle.colours[0]
        return (particle.chars[0],
                int(particle.x),
                int(particle.y),
                colour[0], colour[1], colour[2])


class RingExplosion(ParticleSystem):
    """
    A classic firework exploding to a simple ring.
    """

    def __init__(self, screen, x, y, life_time):
        super(RingExplosion, self).__init__(
            screen, x, y, 15, self._new_particle, 3, life_time)
        self._colour = randint(1, 7)
        self._acceleration = 1.0 - (1.0 / life_time)

    def _new_particle(self):
        direction = uniform(0, 2 * pi)
        return _Particle("**::. ",
                         self._x,
                         self._y,
                         sin(direction) * 3 * 8 / self._life_time,
                         cos(direction) * 1.5 * 8 / self._life_time,
                         [(self._colour, Screen.A_BOLD, 0), (0, 0, 0)],
                         self._explode)

    def _explode(self, particle):
        # Simulate some gravity and slowdown in explosion
        particle.dy = particle.dy * self._acceleration + 0.03
        particle.dx *= self._acceleration
        particle.x += particle.dx
        particle.y += particle.dy

        colour = particle.colours[
            (len(particle.colours)-1) * particle.time // self._life_time]
        return (particle.chars[
                (len(particle.chars)-1) * particle.time // self._life_time],
                int(particle.x),
                int(particle.y),
                colour[0], colour[1], colour[2])


class SerpentExplosion(ParticleSystem):
    """
    A firework where each trail changes direction.
    """

    def __init__(self, screen, x, y, life_time):
        super(SerpentExplosion, self).__init__(
            screen, x, y, 8, self._new_particle, 2, life_time)
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
        if particle.time % 3 == 0:
            particle._parm = uniform(0, 2 * pi)
        particle.dx = (particle.dx + cos(particle._parm) / 2) * 0.8
        particle.dy = (particle.dy + sin(particle._parm) / 4) * 0.8
        particle.x += particle.dx
        particle.y += particle.dy

        colour = particle.colours[
            (len(particle.colours)-1) * particle.time // self._life_time]
        return (particle.chars[
                (len(particle.chars)-1) * particle.time // self._life_time],
                int(particle.x),
                int(particle.y),
                colour[0], colour[1], colour[2])


class StarExplosion(ParticleSystem):
    """
    A classic firework exploding to a Peony shape with trails.
    """

    def __init__(self, screen, x, y, life_time, on_each):
        super(StarExplosion, self).__init__(
            screen, x, y, 15, self._new_particle, 2, life_time)
        self._colour = randint(1, 7)
        self._acceleration = 1.0 - (1.0 / life_time)
        self._on_each = on_each

    def _new_particle(self):
        direction = randint(0, 16) * pi / 8
        return _Particle("+",
                         self._x,
                         self._y,
                         sin(direction) * 3 * 8 / self._life_time,
                         cos(direction) * 1.5 * 8 / self._life_time,
                         [(self._colour, Screen.A_BOLD, 0), (0, 0, 0)],
                         self._explode,
                         on_each=self._on_each)

    def _explode(self, particle):
        # Simulate some gravity and slowdown in explosion
        particle.dy = particle.dy * self._acceleration + 0.03
        particle.dx *= self._acceleration
        particle.x += particle.dx
        particle.y += particle.dy

        colour = particle.colours[
            (len(particle.colours)-1) * particle.time // self._life_time]
        return (particle.chars[
                (len(particle.chars)-1) * particle.time // self._life_time],
                int(particle.x),
                int(particle.y),
                colour[0], colour[1], colour[2])


class StarTrail(ParticleSystem):
    """
    A trail for a StarExplosion.
    """

    def __init__(self, screen, x, y, life_time, colour):
        super(StarTrail, self).__init__(
            screen, x, y, 1, self._new_particle, 1, life_time)
        self._colour = colour

    def _new_particle(self):
        return _Particle("+... ",
                         self._x,
                         self._y,
                         0,
                         0,
                         [(self._colour, Screen.A_BOLD, 0), (0, 0, 0)],
                         self._twinkle)

    def _twinkle(self, particle):
        # Simulate some gravity
        particle.dy += 0.03
        particle.y += particle.dy

        colour = particle.colours[
            (len(particle.colours)-1) * particle.time // self._life_time]
        return (particle.chars[
                (len(particle.chars)-1) * particle.time // self._life_time],
                int(particle.x),
                int(particle.y),
                colour[0], colour[1], colour[2])


class StarFirework(ParticleEffect):
    """
    Classic rocket with star explosion.
    """

    def __init__(self, screen, x, y, life_time, **kwargs):
        super(StarFirework, self).__init__(screen, x, y, life_time, **kwargs)

    def reset(self):
        self._active_systems = [
            Rocket(self._screen, self._x, self._y, 10, on_destroy=self._next)]

    def _next(self, parent):
        self._active_systems.append(
            StarExplosion(self._screen, parent.x, parent.y, self._life_time - 10, on_each=self._trail))

    def _trail(self, parent):
        if randint(0, len(self._active_systems)) < 30:
            self._active_systems.insert(0,
                StarTrail(self._screen, parent.x, parent.y, 7, parent.colours[0][0]))

class RingFirework(ParticleEffect):
    """
    Classic rocket with ring explosion.
    """

    def __init__(self, screen, x, y, life_time, **kwargs):
        super(RingFirework, self).__init__(screen, x, y, life_time, **kwargs)

    def reset(self):
        self._active_systems = [
            Rocket(self._screen, self._x, self._y, 10, on_destroy=self._next)]

    def _next(self, parent):
        self._active_systems.append(
            RingExplosion(self._screen, parent.x, parent.y, self._life_time - 10))


class SerpentFirework(ParticleEffect):
    """
    A firework where each trail changes direction.
    """

    def __init__(self, screen, x, y, life_time, **kwargs):
        super(SerpentFirework, self).__init__(screen, x, y, life_time, **kwargs)

    def reset(self):
        self._active_systems = [
            Rocket(self._screen, self._x, self._y, 10, on_destroy=self._next)]

    def _next(self, parent):
        self._active_systems.append(
            SerpentExplosion(self._screen, parent.x, parent.y, self._life_time - 10))
