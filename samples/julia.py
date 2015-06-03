from asciimatics.effects import Julia
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import sys


def demo(screen):
    scenes = []
    effects = [
        Julia(screen),
    ]
    scenes.append(Scene(effects, -1))
    screen.play(scenes, stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo)
        sys.exit(0)
    except ResizeScreenError:
        pass
