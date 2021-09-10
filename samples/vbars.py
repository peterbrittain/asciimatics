#!/usr/bin/env python3

from asciimatics.effects import Print
from asciimatics.renderers import VerticalBarChart, FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
from asciimatics.utilities import BorderLines
import sys
import math
import time
from random import randint


def fn():
    return randint(0, 10)


def wv(x):
    return lambda: 1 + math.sin(math.pi * (2*time.time()+x) / 5)


def demo(screen):
    scenes = []
    if screen.width != 80 or screen.height != 30:
        effects = [
            Print(screen, FigletText("Resize to 80x30"),
                  y=screen.height//2-3),
        ]
    else:
        chart1 = VerticalBarChart(11, 30, [fn, fn],
                    gradient=[(5, Screen.COLOUR_GREEN),
                              (7, Screen.COLOUR_YELLOW),
                              (9, Screen.COLOUR_RED)],
                    border=False, gap=1)

        chart2 = VerticalBarChart(11, 16,
                      [wv(1), wv(2), wv(3), wv(4), wv(5), wv(6), wv(7), wv(8)],
                      char="*", colour=Screen.COLOUR_GREEN,
                      axes=VerticalBarChart.BOTH,
                      scale=2.0, keys=[chr(x) for x in range(65, 73)])
        chart2.border_lines.set_type(BorderLines.DOUBLE_LINE)

        # Grey-scale gradient from 10-100 fg==bg so it looks like a block
        gradual = [(10 * (i + 1), 234 + 2*i, 234 + 2*i) for i in range(11)]
        chart3 = VerticalBarChart(15, 70, [lambda: time.time() * 10 % 101],
                      gradient=[
                          (33, Screen.COLOUR_RED, Screen.COLOUR_RED),
                          (66, Screen.COLOUR_YELLOW, Screen.COLOUR_YELLOW),
                          (100, Screen.COLOUR_WHITE, Screen.COLOUR_WHITE),
                      ] if screen.colours < 256 else gradual,
                      char="^", scale=100.0, labels=True, 
                      axes=VerticalBarChart.Y_AXIS)

#        chart4 = VerticalBarChart(10, 60,
#                      [wv(1), wv(2), wv(3), wv(4), wv(5), wv(7), wv(8), wv(9)],
#                      colour=[c for c in range(1, 8)],
#                      bg=[c for c in range(1, 8)],
#                      scale=2.0, axes=BarChart.X_AXIS, intervals=0.5,
#                      labels=True, border=False)

        effects = [
            Print(screen, chart1, x=1, y=1, transparent=False, speed=2),
            Print(screen, chart2, x=40, y=1, transparent=False, speed=2),
            Print(screen, chart3, x=10, y=13, transparent=False, speed=2),
#            Print(screen, chart4, x=3, y=13, transparent=False, speed=2)
        ]

    scenes.append(Scene(effects, -1))
    screen.play(scenes, stop_on_resize=True)


while True:
    try:
        Screen.wrapper(demo)
        sys.exit(0)
    except ResizeScreenError:
        pass
