import curses
from asciimatics.effects import Print, Clock
from asciimatics.renderers import FigletText, Rainbow
from asciimatics.scene import Scene
from asciimatics.screen import Screen


def demo(win):
    screen = Screen(win)

    effects = [
        Print(screen, Rainbow(screen, FigletText("256 colours")),
              y=screen.height/2 - 8),
        Print(screen, Rainbow(screen, FigletText("for xterm users")),
              y=screen.height/2 + 3),
        Clock(screen, screen.width/2, screen.height/2, screen.height/2),
    ]
    screen.play([Scene(effects, -1)])

curses.wrapper(demo)
