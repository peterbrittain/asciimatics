from random import choice
from asciimatics.renderers import Kaleidoscope
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.effects import Print
from asciimatics.exceptions import ResizeScreenError
import sys


def demo(screen):
    effects = [
        Print(screen,
              Kaleidoscope(screen.height, screen.width, screen.colours, 8),
              0,
              speed=1,
              transparent=False),
    ]
    screen.play([Scene(effects)], stop_on_resize=True)

if __name__ == "__main__":
    while True:
        try:
            Screen.wrapper(demo)
            sys.exit(0)
        except ResizeScreenError:
            pass
