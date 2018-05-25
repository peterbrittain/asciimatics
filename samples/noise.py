from asciimatics.effects import RandomNoise
from asciimatics.renderers import FigletText, Rainbow
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import sys


def demo(screen):
    effects = [
        RandomNoise(screen,
                    signal=Rainbow(screen,
                                   FigletText("ASCIIMATICS")))
    ]
    screen.play([Scene(effects, -1)], stop_on_resize=True)


while True:
    try:
        Screen.wrapper(demo)
        sys.exit(0)
    except ResizeScreenError:
        pass
