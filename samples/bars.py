from asciimatics.effects import Print
from asciimatics.renderers import BarChart
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import sys
import math
import time
from random import randint

def fn():
    return randint(0, 34)


def demo(screen):
    scenes = []
    effects = [
        Print(screen,
              BarChart(10, 40, [fn, fn],
                       char="=",
                       gradient=[(20, Screen.COLOUR_GREEN),
                                 (30, Screen.COLOUR_YELLOW),
                                 (40, Screen.COLOUR_RED)]),
              (screen.height - 10) // 2, transparent=False, speed=2)
    ]
    scenes.append(Scene(effects, 300))

    def wv(x):
        return lambda: int(27 * (1 + math.sin(math.pi * (2*time.time()+x) / 5)))

    effects = [
        Print(screen,
              BarChart(
                  12, 60,
                  [wv(1), wv(2), wv(3), wv(4), wv(5), wv(7), wv(8), wv(9)],
                  colour=[c for c in range(1,8)]),
              (screen.height - 12) // 2, transparent=False, speed=2)
    ]
    scenes.append(Scene(effects, 300))

    screen.play(scenes, stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo)
        sys.exit(0)
    except ResizeScreenError:
        pass
