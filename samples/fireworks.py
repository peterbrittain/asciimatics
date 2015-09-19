from asciimatics.effects import Stars, Print
from asciimatics.particles import Firework
from asciimatics.renderers import SpeechBubble
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
from random import randint
import sys


def demo(screen):
    scenes = []
    effects = [
        Stars(screen, screen.width),
        Print(screen,
              SpeechBubble("Press space to see it again"),
              y=screen.height // 2 - 1,
              start_frame=300)
    ]
    for _ in range(40):
        effects.insert(1,
                       Firework(screen,
                                randint(0, screen.width),
                                randint(0, screen.height * 3 // 4),
                                randint(5, 40),
                                start_frame=randint(0, 250)))

    scenes.append(Scene(effects, -1))
    screen.play(scenes, stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo)
        sys.exit(0)
    except ResizeScreenError:
        pass
