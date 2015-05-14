import curses
from asciimatics.effects import Cog, Print
from asciimatics.renderers import FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen


def demo(win):
    screen = Screen.from_curses(win)

    effects = [
        Cog(screen, 0, 0, 40, 20),
        Cog(screen, 30, 15, 60, 30, direction=-1),
        Print(screen, FigletText("ascii", font="smkeyboard"), x=48, y=3,
              start_frame=50),
        Print(screen, FigletText("matics", font="smkeyboard"), x=46, y=7,
              start_frame=100)
    ]
    screen.play([Scene(effects, -1)])

curses.wrapper(demo)
