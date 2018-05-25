from __future__ import division
from asciimatics.effects import Cog, Print
from asciimatics.renderers import FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import sys


def demo(screen):
    # Typical terminals are 80x24 on UNIX and 80x25 on Windows
    if screen.width != 80 or screen.height not in (24, 25):
        effects = [
            Print(screen, FigletText("Resize to 80x24"),
                  y=screen.height//2-3),
        ]
    else:
        effects = [
            Cog(screen, 20, 10, 10),
            Cog(screen, 60, 30, 15, direction=-1),
            Print(screen, FigletText("ascii", font="smkeyboard"),
                  attr=Screen.A_BOLD, x=47, y=3, start_frame=50),
            Print(screen, FigletText("matics", font="smkeyboard"),
                  attr=Screen.A_BOLD, x=45, y=7, start_frame=100),
            Print(screen, FigletText("by Peter Brittain", font="term"),
                  x=8, y=22, start_frame=150)
        ]
    screen.play([Scene(effects, -1)], stop_on_resize=True)


while True:
    try:
        Screen.wrapper(demo)
        sys.exit(0)
    except ResizeScreenError:
        pass
