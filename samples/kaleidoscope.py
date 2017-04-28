from asciimatics.renderers import Kaleidoscope, FigletText, Rainbow, RotatedDuplicate
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.effects import Print
from asciimatics.exceptions import ResizeScreenError
import sys


def demo(screen):
    scenes = []
    for i in range(8):
        scenes.append(
                Scene([Print(screen,
                             Kaleidoscope(screen.height,
                                          screen.width,
                                          Rainbow(screen,
                                                  RotatedDuplicate(screen,
                                                                   FigletText("ASCII rules",
                                                                              font="banner",
                                                                              width=screen.width//2))),
                                          i),
                             0,
                             speed=1,
                             transparent=False),
                       Print(screen,
                             FigletText(str(i)), screen.height - 6, x=screen.width - 8, speed=1)],
                      duration=360))
    screen.play(scenes, stop_on_resize=True)

if __name__ == "__main__":
    while True:
        try:
            Screen.wrapper(demo)
            sys.exit(0)
        except ResizeScreenError:
            pass
