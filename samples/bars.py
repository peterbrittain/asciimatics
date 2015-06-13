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
    return randint(0, 40)


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
        return lambda: 1 + math.sin(math.pi * (2*time.time()+x) / 5)

    effects = [
        Print(screen,
              BarChart(
                  13, 60,
                  [wv(1), wv(2), wv(3), wv(4), wv(5), wv(7), wv(8), wv(9)],
                  colour=Screen.COLOUR_GREEN,
                  axes=BarChart.BOTH,
                  scale=2.0),
              (screen.height - 13) // 2, transparent=False, speed=2)
    ]
    scenes.append(Scene(effects, 300))

    effects = [
        Print(screen,
              BarChart(
                  7, 60, [lambda: time.time() * 10 % 101],
                  gradient=[(10, 234), (20, 236), (30, 238), (40, 240),
                            (50, 242), (60, 244), (70, 246), (80, 248),
                            (90, 250), (100, 252)],
                  char=">",
                  scale=100.0,
                  labels=True,
                  axes=BarChart.X_AXIS),
              (screen.height - 7) // 2, transparent=False, speed=2)
    ]
    scenes.append(Scene(effects, 300))

    effects = [
        Print(screen,
              BarChart(
                  10, 60,
                  [wv(1), wv(2), wv(3), wv(4), wv(5), wv(7), wv(8), wv(9)],
                  colour=[c for c in range(1,8)],
                  scale=2.0,
                  axes=BarChart.X_AXIS,
                  intervals=0.25,
                  labels=True,
                  border=False),
              (screen.height - 10) // 2, transparent=False, speed=2)
    ]
    scenes.append(Scene(effects, 300))

    screen.play(scenes, stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo)
        sys.exit(0)
    except ResizeScreenError:
        pass
