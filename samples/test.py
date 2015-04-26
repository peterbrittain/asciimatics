import curses
from asciimatics.effects import Cycle, Stars
from asciimatics.renderers import FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen


def demo(win):
    screen = Screen(win)
    effects = [
        Cycle(
            screen,
            FigletText("ASCIIMATICS", font='big'),
            screen.height / 2 - 8),
        Cycle(
            screen,
            FigletText("ROCKS!", font='big'),
            screen.height / 2 + 3),
        Stars(screen, 200)
    ]
    screen.play([Scene(effects, 500)])

curses.wrapper(demo)
