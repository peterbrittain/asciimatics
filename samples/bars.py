#!/usr/bin/env python3

from asciimatics.effects import Print
from asciimatics.renderers import BarChart, FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
from asciimatics.utilities import BorderLines
import sys
import math
import time
from random import randint


def fn():
    return randint(0, 40)


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
        chart1 = BarChart(10, 40, [fn, fn], char="=", 
                    gradient=[(20, Screen.COLOUR_GREEN),
                              (30, Screen.COLOUR_YELLOW),
                              (40, Screen.COLOUR_RED)],
                    keys=['a', 'b'])
        chart1.border_lines.set_type(BorderLines.DOUBLE_LINE)

        chart2 = BarChart(13, 60,
                      [wv(1), wv(2), wv(3), wv(4), wv(5), wv(7), wv(8), wv(9)],
                      colour=Screen.COLOUR_GREEN,
                      axes=BarChart.BOTH,
                      scale=2.0)
        chart2.border_lines.set_type(BorderLines.ASCII_LINE)

        effects = [
            Print(screen, chart1, x=13, y=1, transparent=False, speed=2),
            Print(screen, chart2, x=68, y=1, transparent=False, speed=2),
            Print(screen,
                  BarChart(
                      7, 60, [lambda: time.time() * 10 % 101],
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
                      char=">",
                      scale=100.0,
                      labels=True,
                      axes=BarChart.X_AXIS),
                  x=68, y=16, transparent=False, speed=2),
            Print(screen,
                  BarChart(
                      10, 60,
                      [wv(1), wv(2), wv(3), wv(4), wv(5), wv(7), wv(8), wv(9)],
                      colour=[c for c in range(1, 8)],
                      bg=[c for c in range(1, 8)],
                      scale=2.0,
                      axes=BarChart.X_AXIS,
                      intervals=0.5,
                      labels=True,
                      border=False),
                  x=3, y=13, transparent=False, speed=2)
        ]

    scenes.append(Scene(effects, -1))
    screen.play(scenes, stop_on_resize=True)


while True:
    try:
        Screen.wrapper(demo)
        sys.exit(0)
    except ResizeScreenError:
        pass
