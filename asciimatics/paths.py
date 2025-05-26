"""
This module provides `Paths` to create animation effects with Sprites.  For more details see
http://asciimatics.readthedocs.io/en/latest/animation.html
"""

from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, List, Tuple, Optional
if TYPE_CHECKING:
    from asciimatics.event import Event
    from asciimatics.screen import Screen


def _spline(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """
    Catmull-Rom cubic spline to interpolate 4 given points.

    :param t: Time index through the spline (must be 0-1).
    :param p0: The previous point in the curve (for continuity).
    :param p1: The first point to interpolate.
    :param p2: The second point to interpolate.
    :param p3: The last point to interpolate.
    """
    return (t * ((2 - t) * t - 1) * p0 + (t * t * (3 * t - 5) + 2) * p1 + t * ((4 - 3 * t) * t + 1) * p2 +
            (t - 1) * t * t * p3) / 2


class _AbstractPath(metaclass=ABCMeta):
    """
    Class to represent the motion of a Sprite.

    The Screen will reset() the Path before iterating through each position
    using next_pos() and checking whether it has reached the end using
    is_finished().
    """

    def __init__(self):
        """
        To define a Path, use the methods to jump to a location, wait or move
        between points.
        """
        self._steps = []
        self._index = 0
        self._rec_x = 0
        self._rec_y = 0

    @abstractmethod
    def reset(self):
        """
        Reset the Path for use next time.
        """

    @abstractmethod
    def next_pos(self) -> Tuple[int, int]:
        """
        :return: The next position tuple (x, y) for the Sprite on this path.
        """

    @abstractmethod
    def is_finished(self) -> bool:
        """
        :return: Whether this path has got to the end.
        """


class Path(_AbstractPath):
    """
    Class to record and play back the motion of a Sprite.

    The Screen will reset() the Path before iterating through each position
    using next_pos() and checking whether it has reached the end using
    is_finished().
    """

    def __init__(self):
        """
        To define a Path, use the methods to jump to a location, wait or move
        between points.
        """
        super().__init__()
        self._steps: list[tuple[int, int]] = []
        self._rec_x = 0
        self._rec_y = 0
        self.reset()

    def reset(self):
        """
        Reset the Path for use next time.
        """
        self._index = 0

    def next_pos(self) -> Tuple[int, int]:
        """
        :return: The next position tuple (x, y) for the Sprite on this path.
        """
        if self._index <= len(self._steps):
            result = self._steps[self._index]
            self._index += 1
        else:
            result = self._steps[-1]
        return result

    def is_finished(self) -> bool:
        """
        :return: Whether this path has got to the end.
        """
        return self._index >= len(self._steps)

    def _add_step(self, pos: Tuple[int, int]):
        """
        Add a step to the end of the current recorded path.

        :param pos: The position tuple (x, y) to add to the list.
        """
        self._steps.append(pos)
        self._rec_x = pos[0]
        self._rec_y = pos[1]

    def wait(self, delay: int):
        """
        Wait at the current location for the specified number of iterations.

        :param delay: The time to wait (in animation frames).
        """
        for _ in range(0, delay):
            self._add_step((self._rec_x, self._rec_y))

    def jump_to(self, x: int, y: int):
        """
        Jump straight to the newly specified location - i.e. teleport there and
        don't create a path to get there.

        :param x:  X coord for the end position.
        :param y: Y coord for the end position.
        """
        self._add_step((x, y))

    def move_straight_to(self, x: int, y: int, steps: int):
        """
        Move straight to the newly specified location - i.e. create a straight
        line Path from the current location to the specified point.

        :param x:  X coord for the end position.
        :param y: Y coord for the end position.
        :param steps: How many steps to take for the move.
        """
        start_x = self._rec_x
        start_y = self._rec_y
        for i in range(1, steps + 1):
            self._add_step((int(start_x + (x - start_x) / float(steps) * i),
                            int(start_y + (y - start_y) / float(steps) * i)))

    def move_round_to(self, points: List[Tuple[int, int]], steps: int):
        """
        Follow a path pre-defined by a set of at least 4 points.  This Path will
        interpolate the points into a curve and follow that curve.

        :param points: The list of points that defines the path.
        :param steps: The number of steps to take to follow the path.
        """
        # Spline interpolation needs a before and after point for the curve.
        # Duplicate the first and last points to handle this.  We also need
        # to move from the current position to the first specified point.
        points.insert(0, (self._rec_x, self._rec_y))
        points.insert(0, (self._rec_x, self._rec_y))
        points.append(points[-1])

        # Convert the points into an interpolated set of more detailed points.
        steps_per_spline = steps // (len(points) - 3)
        for j in range(1, len(points) - 2):
            for t in range(1, steps_per_spline + 1):
                y = _spline(
                    float(t) / steps_per_spline,
                    float(points[j - 1][1]),
                    float(points[j][1]),
                    float(points[j + 1][1]),
                    float(points[j + 2][1]))
                x = int(points[j][0] + ((points[j + 1][0] - points[j][0]) * float(t) / steps_per_spline))
                self._add_step((x, int(y)))


class DynamicPath(_AbstractPath, metaclass=ABCMeta):
    """
    Class to create a dynamic path that reacts to events

    The Screen will reset() the Path before iterating through each position
    using next_pos() and checking whether it has reached the end using
    is_finished().
    """

    def __init__(self, screen: Screen, x: int, y: int):
        """
        To implement a DynamicPath, override the :py:meth:`.process_event()`
        method to react to any user input.
        """
        super().__init__()
        self._screen = screen
        self._x = self._start_x = x
        self._y = self._start_y = y
        self.reset()

    def reset(self):
        """
        Reset the Path for use next time.
        """
        self._x = self._start_x
        self._y = self._start_y

    def next_pos(self) -> Tuple[int, int]:
        """
        :return: The next position tuple (x, y) for the Sprite on this path.
        """
        return self._x, self._y

    def is_finished(self) -> bool:
        """
        :return: Whether this path has got to the end.
        """
        return False

    @abstractmethod
    def process_event(self, event: Event) -> Optional[Event]:
        """
        Process any mouse event.

        :param event: The event that was triggered.
        :returns: None if the Effect processed the event, else the original
                  event.
        """
