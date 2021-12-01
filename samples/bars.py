#!/usr/bin/env python3

from asciimatics.constants import SINGLE_LINE, DOUBLE_LINE, ASCII_LINE
from asciimatics.effects import Print
from asciimatics.exceptions import ResizeScreenError
from asciimatics.renderers import BarChart, VBarChart, FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.utilities import BoxTool
import sys
import math
import time
from random import randint


def fn():
    return randint(0, 10)

def fn2():
    return randint(0, 6)


def wv(x):
    return lambda: 1 + math.sin(math.pi * (2*time.time()+x) / 5)


def demo(screen):
    scenes = []
    if screen.width != 132 or screen.height != 24:
        effects = [
            Print(screen, FigletText("Resize to 132x24"),
                  y=screen.height//2-3),
        ]
    else:
        # Horizontal Charts
        hchart1 = BarChart(9, 22, [fn, fn], char="═",
                           gradient=[(7, Screen.COLOUR_GREEN),
                                     (9, Screen.COLOUR_YELLOW),
                                     (10, Screen.COLOUR_RED)],
                            keys=["one", "two"], gap=1,
                  )
        hchart2 = BarChart(10, 25, [wv(1), wv(3), wv(5), wv(7), wv(9)],
                      colour=Screen.COLOUR_GREEN, axes=BarChart.BOTH, scale=2.0)
        hchart2.border_style = ASCII_LINE
        hchart2.axes_style = ASCII_LINE
        hchart3 = BarChart(10, 40, [wv(1), wv(2), wv(3), wv(4), wv(5), wv(7), wv(8), wv(9)],
                      colour=[c for c in range(1, 8)], bg=[c for c in range(1, 8)],
                      scale=2.0, axes=BarChart.X_AXIS, intervals=0.5, labels=True, border=False)
        hchart4 = BarChart(7, 30, [lambda: time.time() * 10 % 101],
                      gradient=[
                          (33, Screen.COLOUR_RED, Screen.COLOUR_RED),
                          (66, Screen.COLOUR_YELLOW, Screen.COLOUR_YELLOW),
                          (100, Screen.COLOUR_WHITE, Screen.COLOUR_WHITE),
                      ] if screen.colours < 256 else [
                          (10, 234, 234), (20, 236, 236), (30, 238, 238),
                          (40, 240, 240), (50, 242, 242), (60, 244, 244),
                          (70, 246, 246), (80, 248, 248), (90, 250, 250),
                          (100, 252, 252)
                      ],
                      char=">", scale=100.0, labels=True, axes=BarChart.X_AXIS)
        hchart4.border_style = SINGLE_LINE

        # Vertical Charts
        vchart1 = VBarChart(12, 21, [fn2, fn2], char="═",
                           gradient=[(3, Screen.COLOUR_GREEN),
                                     (4, Screen.COLOUR_YELLOW),
                                     (5, Screen.COLOUR_RED)],
                            keys=["one", "two"],
                  )
        vchart2 = VBarChart(12, 17, [wv(1), wv(3), wv(5), wv(7), wv(9)],
                      colour=Screen.COLOUR_GREEN, axes=BarChart.BOTH, scale=2.0, gap=0)
        vchart2.border_style = ASCII_LINE
        vchart2.axes_style = ASCII_LINE
        vchart3 = VBarChart(12, 39, [wv(1), wv(2), wv(3), wv(4), wv(5), wv(7), wv(8), wv(9)],
                      colour=[c for c in range(1, 8)], bg=[c for c in range(1, 8)], gap=0,
                      scale=2.0, axes=BarChart.Y_AXIS, intervals=0.5, labels=True, border=False)
        vchart4 = VBarChart(12, 16, [lambda: time.time() * 10 % 101],
                      gradient=[
                          (33, Screen.COLOUR_RED, Screen.COLOUR_RED),
                          (66, Screen.COLOUR_YELLOW, Screen.COLOUR_YELLOW),
                          (100, Screen.COLOUR_WHITE, Screen.COLOUR_WHITE),
                      ] if screen.colours < 256 else [
                          (10, 234, 234), (20, 236, 236), (30, 238, 238),
                          (40, 240, 240), (50, 242, 242), (60, 244, 244),
                          (70, 246, 246), (80, 248, 248), (90, 250, 250),
                          (100, 252, 252)
                      ],
                      char=">", scale=100.0, labels=True, axes=VBarChart.Y_AXIS)
        vchart4.border_style = SINGLE_LINE

        effects = [
            Print(screen, hchart1, x=1, y=1, transparent=False, speed=2),
            Print(screen, hchart2, x=25, y=1, transparent=False, speed=2),
            Print(screen, hchart3, x=52, y=1, transparent=False, speed=2),
            Print(screen, hchart4, x=96, y=2, transparent=False, speed=2),

            Print(screen, vchart1, x=2, y=12, transparent=False, speed=2),
            Print(screen, vchart2, x=29, y=12, transparent=False, speed=2),
            Print(screen, vchart3, x=52, y=12, transparent=False, speed=2),
            Print(screen, vchart4, x=103, y=12, transparent=False, speed=2),
        ]

    scenes.append(Scene(effects, -1))
    screen.play(scenes, stop_on_resize=True)


while True:
    try:
        Screen.wrapper(demo)
        sys.exit(0)
    except ResizeScreenError:
        pass
