from random import randint
from asciimatics.effects import Print
from asciimatics.particles import Explosion, StarFirework, DropScreen, Rain, \
    ShootScreen
from asciimatics.renderers import SpeechBubble, FigletText, Rainbow
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import sys


def demo(screen):
    scenes = []

    # First scene: title page
    effects = [
        Print(screen,
              Rainbow(screen, FigletText("ASCIIMATICS", font="big")),
              y=screen.height // 4 - 5),
        Print(screen,
              FigletText("Particle System"),
              screen.height // 2 - 3),
        Print(screen,
              FigletText("Effects Demo"),
              screen.height * 3 // 4 - 3),
        Print(screen,
              SpeechBubble("Press SPACE to continue..."),
              screen.height - 3,
              transparent=False,
              start_frame=70)
    ]
    scenes.append(Scene(effects, -1))

    # Next scene: just dissolve the title.
    effects = [
        ShootScreen(screen, screen.width // 2, screen.height // 2, 100),
    ]
    scenes.append(Scene(effects, 40, clear=False))

    # Next scene: sub-heading.
    effects = [
        DropScreen(screen, 100),
        Print(screen,
              Rainbow(screen, FigletText("Explosions", font="doom")),
              y=screen.height // 2 - 5,
              stop_frame=30),
        DropScreen(screen, 100, start_frame=30)
    ]
    scenes.append(Scene(effects, 80))

    # Next scene: explosions
    effects = []
    for i in range(20):
        effects.append(
            Explosion(screen,
                      randint(3, screen.width - 4),
                      randint(1, screen.height - 2),
                      randint(20, 30),
                      start_frame=randint(0, 250)))
    effects.append(Print(screen,
                         SpeechBubble("Press SPACE to continue..."),
                         screen.height - 6,
                         speed=1,
                         transparent=False,
                         start_frame=100))
    scenes.append(Scene(effects, -1))

    # Next scene: sub-heading.
    effects = [
        Print(screen,
              Rainbow(screen, FigletText("Rain", font="doom")),
              y=screen.height // 2 - 5,
              stop_frame=30),
        DropScreen(screen, 100, start_frame=30)
    ]
    scenes.append(Scene(effects, 80))

    # Next scene: rain storm.
    effects = [
        Rain(screen, 200),
        Print(screen,
              SpeechBubble("Press SPACE to continue..."),
              screen.height - 6,
              speed=1,
              transparent=False,
              start_frame=100)
    ]
    scenes.append(Scene(effects, -1))

    # Next scene: sub-heading.
    effects = [
        Print(screen,
              Rainbow(screen, FigletText("Fireworks", font="doom")),
              y=screen.height // 2 - 5,
              stop_frame=30),
        DropScreen(screen, 100, start_frame=30)
    ]
    scenes.append(Scene(effects, 80))

    # Next scene: fireworks
    effects = []
    for i in range(20):
        effects.append(
            StarFirework(screen,
                         randint(3, screen.width - 4),
                         randint(1, screen.height - 2),
                         randint(20, 30),
                         start_frame=randint(0, 250)))
    effects.append(Print(screen,
                         SpeechBubble("Press SPACE to continue..."),
                         screen.height - 6,
                         speed=1,
                         transparent=False,
                         start_frame=100))
    scenes.append(Scene(effects, -1))

    screen.play(scenes, stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo)
        sys.exit(0)
    except ResizeScreenError:
        pass
