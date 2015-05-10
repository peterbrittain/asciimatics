import curses
from asciimatics.effects import RandomNoise
from asciimatics.renderers import FigletText, Rainbow
from asciimatics.scene import Scene
from asciimatics.screen import Screen


def demo(win):
    screen = Screen.from_curses(win)

    effects = [
        RandomNoise(screen,
                    signal=Rainbow(screen,
                                   FigletText("ASCIIMATICS")))
    ]
    screen.play([Scene(effects, -1)])

curses.wrapper(demo)
