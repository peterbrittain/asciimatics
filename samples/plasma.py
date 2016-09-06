from asciimatics.renderers import Plasma
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.effects import Print
from asciimatics.exceptions import ResizeScreenError
import sys


def demo(screen):
    scenes = []

    effects = [
        Print(screen,
              Plasma(screen.height, screen.width, screen.colours),
              0,
              speed=1,
              transparent=False),
    ]
    scenes.append(Scene(effects, -1))

    screen.play(scenes, stop_on_resize=True)

if __name__ == "__main__":
    while True:
        try:
            Screen.wrapper(demo)
            sys.exit(0)
        except ResizeScreenError:
            pass
