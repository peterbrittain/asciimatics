#!/usr/bin/env python3

from asciimatics.effects import Print

#from asciimatics.renderers import VerticalBarChart, FigletText
from asciimatics.renderers import VBarChart as VerticalBarChart
from asciimatics.renderers import FigletText

from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
from asciimatics.utilities import BoxTool
import sys
import math
import time
from random import randint

import logging
logging.basicConfig(filename="vbars.log", level=logging.DEBUG)

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
        chart1 = VerticalBarChart(11, 13, [fn, fn],
                    gradient=[(5, Screen.COLOUR_GREEN),
                              (7, Screen.COLOUR_YELLOW),
                              (9, Screen.COLOUR_RED)],
                    border=False, gap=1)

        chart2 = VerticalBarChart(11, 15,
                      [wv(1), wv(2), wv(3), wv(4), wv(5), wv(6), wv(7), wv(8), wv(9)],
                      char="*", colour=Screen.COLOUR_GREEN,
                      axes=VerticalBarChart.X_AXIS | VerticalBarChart.Y_AXIS,
                      scale=2.0, x_label='ABCDEFGHI', x_grid=1)
        chart2.border_lines.set_style(BoxTool.DOUBLE_LINE)

        # Grey-scale gradient from 10-100 fg==bg so it looks like a block
        gradual = [(10 * (i + 1), 234 + 2*i, 234 + 2*i) for i in range(11)]
        y_labels = ['' for _ in range(10)]
        y_labels[0] = '100.0'
        y_labels[-1] = '0.0'
        chart3 = VerticalBarChart(11, 20, [lambda: time.time() * 10 % 101],
                      gradient=[
                          (33, Screen.COLOUR_RED, Screen.COLOUR_RED),
                          (66, Screen.COLOUR_YELLOW, Screen.COLOUR_YELLOW),
                          (100, Screen.COLOUR_WHITE, Screen.COLOUR_WHITE),
                      ] if screen.colours < 256 else gradual,
                      char="^", scale=100.0, 
                      axes=VerticalBarChart.Y_AXIS | VerticalBarChart.Y_AXIS_RIGHT,
                      y_labels=y_labels, y_labels_rhs=y_labels)

        y_labels = ['' for _ in range(11)]
        y_labels[0] = '1.0'
        y_labels[5] = '0.5'
        y_labels[10] = '0'
        chart4 = VerticalBarChart(11, 11,
                      [wv(1), wv(2), wv(3), wv(4), wv(5), wv(7), wv(8), wv(9)],
                      colour=[c for c in range(1, 9)], bg=[c for c in range(1, 9)],
                      scale=2.0, axes=VerticalBarChart.X_AXIS, 
                      y_labels=y_labels,
                      border=False)

        effects = [
            Print(screen, chart1, x=1, y=1, transparent=False, speed=2),
            Print(screen, chart2, x=16, y=1, transparent=False, speed=2),
            Print(screen, chart3, x=33, y=1, transparent=False, speed=2),
            Print(screen, chart4, x=55, y=1, transparent=False, speed=2)
        ]

    scenes.append(Scene(effects, -1))
    screen.play(scenes, stop_on_resize=True)


while True:
    try:
        Screen.wrapper(demo)
        sys.exit(0)
    except ResizeScreenError:
        pass
