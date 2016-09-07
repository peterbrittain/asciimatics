from asciimatics.renderers import Plasma, Rainbow, FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.effects import Print
from asciimatics.exceptions import ResizeScreenError
import sys


def demo(screen):
    scenes = []
    msg = FigletText("Far out!", "banner3")
    effects = [
        Print(screen,
              Plasma(screen.height, screen.width, screen.colours),
              0,
              speed=2,
              transparent=False),
        Print(screen,
              msg,
              (screen.height // 2) - 4,
              x=(screen.width - msg.max_width) // 2 + 1,
              colour=Screen.COLOUR_BLACK,
              speed=1),
        Print(screen,
              Rainbow(screen, msg),
              (screen.height // 2) - 4,
              x=(screen.width - msg.max_width) // 2,
              colour=Screen.COLOUR_MAGENTA, attr=Screen.A_BOLD,
              speed=1),
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
