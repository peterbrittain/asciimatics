import curses
from asciimatics.effects import RandomNoise, Mirage
from asciimatics.renderers import FigletText, Rainbow
from asciimatics.scene import Scene
from asciimatics.screen import Screen


def demo(win):
    screen = Screen(win)

    effects = [
        RandomNoise(screen,
                    signal=Rainbow(screen,
                                   FigletText("ASCIIMATICS")))
    ]
    screen.play([Scene(effects, -1)])

curses.wrapper(demo)
