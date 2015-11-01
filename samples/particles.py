from random import randint
from asciimatics.particles import Explosion
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import sys


def demo(screen):
    scenes = []
    effects = []
    for i in range(20):
        effects.append(
            Explosion(screen,
                      randint(3, screen.width - 4),
                      randint(1, screen.height - 2),
                      randint(20, 30),
                      start_frame=randint(0, 250)))
    scenes.append(Scene(effects, -1))

    screen.play(scenes, stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo)
        sys.exit(0)
    except ResizeScreenError:
        pass
