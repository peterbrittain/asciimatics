#!/usr/bin/env python3

from random import choice
from asciimatics.renderers import Plasma, Rainbow, FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.effects import Print
from asciimatics.exceptions import ResizeScreenError
import sys


class PlasmaScene(Scene):

    # Random cheesy comments
    _comments = [
        "Far out!",
        "Groovy",
        "Heavy",
        "Right on!",
        "Cool",
        "Dude!"
    ]

    def __init__(self, screen):
        self._screen = screen
        effects = [
            Print(screen,
                  Plasma(screen.height, screen.width, screen.colours),
                  0,
                  speed=1,
                  transparent=False),
        ]
        super(PlasmaScene, self).__init__(effects, 200, clear=False)

    def _add_cheesy_comment(self):
        msg = FigletText(choice(self._comments), "banner3")
        self._effects.append(
            Print(self._screen,
                  msg,
                  (self._screen.height // 2) - 4,
                  x=(self._screen.width - msg.max_width) // 2 + 1,
                  colour=Screen.COLOUR_BLACK,
                  stop_frame=80,
                  speed=1))
        self._effects.append(
            Print(self._screen,
                  Rainbow(self._screen, msg),
                  (self._screen.height // 2) - 4,
                  x=(self._screen.width - msg.max_width) // 2,
                  colour=Screen.COLOUR_BLACK,
                  stop_frame=80,
                  speed=1))

    def reset(self, old_scene=None, screen=None):
        super(PlasmaScene, self).reset(old_scene, screen)

        # Make sure that we only have the initial Effect and add a new cheesy
        # comment.
        self._effects = [self._effects[0]]
        self._add_cheesy_comment()


def demo(screen):
    screen.play([PlasmaScene(screen)], stop_on_resize=True)


if __name__ == "__main__":
    while True:
        try:
            Screen.wrapper(demo)
            sys.exit(0)
        except ResizeScreenError:
            pass
