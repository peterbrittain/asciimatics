import curses
from asciimatics.effects import Print
from asciimatics.renderers import FigletText, Rainbow
from asciimatics.scene import Scene
from asciimatics.screen import Screen


def demo(win):
    screen = Screen(win)
    effects = [
        Print(screen, Rainbow(screen, FigletText("256 colours")), y=5),
        Print(screen, Rainbow(screen, FigletText("for xterm users")), y=15)
    ]
    screen.play([Scene(effects, -1)])

curses.wrapper(demo)
