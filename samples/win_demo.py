from __future__ import division
from asciimatics.effects import Print, Clock
from asciimatics.exceptions import ResizeScreenError
from asciimatics.renderers import FigletText, Rainbow
from asciimatics.scene import Scene
from asciimatics.screen import Screen
import win32console


def demo(con):
    while True:
        screen = Screen.from_windows(con)
        effects = [
            Print(screen, Rainbow(screen, FigletText("256 colours")),
                  y=screen.height//2 - 8),
            Print(screen, Rainbow(screen, FigletText("for xterm users")),
                  y=screen.height//2 + 3),
            Clock(screen, screen.width//2, screen.height//2, screen.height//2),
        ]
        try:
            screen.play([Scene(effects, -1)], stop_on_resize=True)
            return
        except ResizeScreenError:
            pass

console = win32console.PyConsoleScreenBufferType(win32console.GetStdHandle(win32console.STD_OUTPUT_HANDLE))
demo(console)
