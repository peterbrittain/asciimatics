from asciimatics.renderers import BarChart
from asciimatics.screen import Screen
import sys
import math
import time
from random import randint


def fn():
    return randint(0, 40)


def wv(x):
    return lambda: 1 + math.sin(math.pi * (2*time.time()+x) / 5)


def demo():
    chart = BarChart(10, 40, [fn, fn],
                     char="=",
                     gradient=[(20, Screen.COLOUR_GREEN),
                               (30, Screen.COLOUR_YELLOW),
                               (40, Screen.COLOUR_RED)])
    print(chart)
    chart = BarChart(13, 60,
                     [wv(1), wv(2), wv(3), wv(4), wv(5), wv(7), wv(8), wv(9)],
                     colour=Screen.COLOUR_GREEN,
                     axes=BarChart.BOTH,
                     scale=2.0)
    print(chart)
    chart = BarChart(7, 60, [lambda: time.time() * 10 % 101],
                     gradient=[(10, 234), (20, 236), (30, 238), (40, 240),
                               (50, 242), (60, 244), (70, 246), (80, 248),
                               (90, 250), (100, 252)],
                     char=">",
                     scale=100.0,
                     labels=True,
                     axes=BarChart.X_AXIS)
    print(chart)
    chart = BarChart(10, 60,
                     [wv(1), wv(2), wv(3), wv(4), wv(5), wv(7), wv(8), wv(9)],
                     colour=[c for c in range(1, 8)],
                     scale=2.0,
                     axes=BarChart.X_AXIS,
                     intervals=0.5,
                     labels=True,
                     border=False)
    print(chart)

demo()
sys.exit(0)
