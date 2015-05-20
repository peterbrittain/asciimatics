from __future__ import division
import curses
from asciimatics.effects import Cog, Print
from asciimatics.renderers import FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError


def demo(win):
    screen = Screen.from_curses(win)
    finished = False
    while not finished:
        if screen.width != 80 or screen.height != 24:
            effects = [
                Print(screen, FigletText("Resize to 80x24"),
                      y=screen.height//2-3),
            ]
        else:
            effects = [
                Cog(screen, 20, 10, 10),
                Cog(screen, 60, 30, 15, direction=-1),
                Print(screen, FigletText("ascii", font="smkeyboard"),
                      x=47, y=3, start_frame=50),
                Print(screen, FigletText("matics", font="smkeyboard"),
                      x=45, y=7, start_frame=100),
                Print(screen, FigletText("by Peter Brittain", font="term"),
                      x=8, y=22, start_frame=150)
            ]
        try:
            screen.play([Scene(effects, -1)], stop_on_resize=True)
            finished = True
        except ResizeScreenError:
            screen = Screen.from_curses(win)

curses.wrapper(demo)
