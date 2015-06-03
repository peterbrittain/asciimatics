from __future__ import division
from asciimatics.effects import Print, Clock
from asciimatics.renderers import FigletText, Rainbow
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import sys

def demo(screen):
    effects = [
        Print(screen, Rainbow(screen, FigletText("256 colours")),
              y=screen.height//2 - 8),
        Print(screen, Rainbow(screen, FigletText("for xterm users")),
              y=screen.height//2 + 3),
        Clock(screen, screen.width//2, screen.height//2, screen.height//2),
    ]
    screen.play([Scene(effects, -1)], stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo)
        sys.exit(0)
    except ResizeScreenError:
        pass
