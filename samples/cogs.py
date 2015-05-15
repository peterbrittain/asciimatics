import curses
from asciimatics.effects import Cog, Print
from asciimatics.renderers import FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen


def demo(win):
    screen = Screen.from_curses(win)

    effects = [
        Cog(screen, 20, 10, 10),
        Cog(screen, 60, 30, 15, direction=-1),
        Print(screen, FigletText("ascii", font="smkeyboard"), x=47, y=3,
              start_frame=50),
        Print(screen, FigletText("matics", font="smkeyboard"), x=45, y=7,
              start_frame=100),
        Print(screen, FigletText("by Peter Brittain", font="term"), x=8, y=22,
              start_frame=150)
    ]
    screen.play([Scene(effects, -1)])

curses.wrapper(demo)
