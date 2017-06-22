from math import sqrt

from asciimatics.renderers import Kaleidoscope, FigletText, Rainbow, RotatedDuplicate, \
    StaticRenderer
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.effects import Print
from asciimatics.exceptions import ResizeScreenError
import sys


def demo(screen):
    scenes = []
    cell1 = Rainbow(screen,
                    RotatedDuplicate(screen.width // 2,
                                     max(screen.width // 2, screen.height),
                                     FigletText("ASCII" if screen.width < 80 else "ASCII rules",
                                                font="banner",
                                                width=screen.width // 2)))
    cell2 = ""
    size = int(sqrt(screen.height ** 2 + screen.width ** 2 // 4))
    for _ in range(size):
        for x in range(size):
            c = x * screen.colours // size
            cell2 += "${%d,2,%d}:" % (c, c)
        cell2 += "\n"
    for i in range(8):
        scenes.append(
                Scene([Print(screen,
                             Kaleidoscope(screen.height, screen.width, cell1, i),
                             0,
                             speed=1,
                             transparent=False),
                       Print(screen,
                             FigletText(str(i)), screen.height - 6, x=screen.width - 8, speed=1)],
                      duration=360))
        scenes.append(
                Scene([Print(screen,
                             Kaleidoscope(screen.height, screen.width, StaticRenderer([cell2]), i),
                             0,
                             speed=1,
                             transparent=False)],
                      duration=360))
    screen.play(scenes, stop_on_resize=True)

if __name__ == "__main__":
    while True:
        try:
            Screen.wrapper(demo)
            sys.exit(0)
        except ResizeScreenError:
            pass
