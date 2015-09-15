from asciimatics.renderers import FigletText, Fire
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.effects import Print
from asciimatics.exceptions import ResizeScreenError
from pyfiglet import Figlet
import sys


def demo(screen):
    scenes = []

    text = Figlet(font="banner", width=200).renderText("ASCIIMATICS")
    width = max([len(x) for x in text.split("\n")])

    effects = [
        Print(screen,
              Fire(screen.height, 80, text, 100),
              0,
              speed=1,
              transparent=False),
        Print(screen,
              FigletText("ASCIIMATICS", "banner"),
              screen.height - 9, x=(screen.width - width) // 2 + 1,
              colour=Screen.COLOUR_BLACK,
              speed=1),
        Print(screen,
              FigletText("ASCIIMATICS", "banner"),
              screen.height - 9,
              colour=Screen.COLOUR_WHITE,
              speed=1),
    ]
    scenes.append(Scene(effects, 600))

    screen.play(scenes, stop_on_resize=True)

if __name__ == "__main__":
    while True:
        try:
            Screen.wrapper(demo)
            sys.exit(0)
        except ResizeScreenError:
            pass
