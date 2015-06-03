from __future__ import division
from builtins import range
import copy
import math
from asciimatics.effects import Cycle, Print, Stars
from asciimatics.renderers import SpeechBubble, FigletText, Box
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.sprites import Arrow, Plot, Sam
from asciimatics.paths import Path
from asciimatics.exceptions import ResizeScreenError
import sys


def _speak(screen, text, pos, start):
    return Print(
        screen,
        SpeechBubble(text, "L"),
        x=pos[0] + 4, y=pos[1] - 4,
        colour=Screen.COLOUR_CYAN,
        clear=True,
        start_frame=start,
        stop_frame=start+50)


def demo(screen):
    scenes = []
    centre = (screen.width // 2, screen.height // 2)
    podium = (8, 5)

    # Scene 1.
    path = Path()
    path.jump_to(-20, centre[1])
    path.move_straight_to(centre[0], centre[1], 10)
    path.wait(30)
    path.move_straight_to(podium[0], podium[1], 10)
    path.wait(100)

    effects = [
        Arrow(screen, path, colour=Screen.COLOUR_GREEN),
        _speak(screen, "WELCOME TO ASCIIMATICS", centre, 30),
        _speak(screen, "My name is Aristotle Arrow.", podium, 110),
        _speak(screen,
               "I'm here to help you learn ASCIImatics.", podium, 180),
    ]
    scenes.append(Scene(effects))

    # Scene 2.
    path = Path()
    path.jump_to(podium[0], podium[1])

    effects = [
        Arrow(screen, path, colour=Screen.COLOUR_GREEN),
        _speak(screen, "Let's start with the Screen...", podium, 10),
        _speak(screen, "This is your Screen object.", podium, 80),
        Print(screen, Box(screen.width, screen.height), 0, 0, start_frame=90),
        _speak(screen, "It lets you play a Scene like this one I'm in.",
               podium, 150),
        _speak(screen, "A Scene contains one or more Effects.", podium, 220),
        _speak(screen, "Like me - I'm a Sprite!", podium, 290),
        _speak(screen, "Or these Stars.", podium, 360),
        _speak(screen, "As you can see, the Screen handles them both at once.",
               podium, 430),
        _speak(screen, "It can handle as many Effects as you like.",
               podium, 500),
        _speak(screen, "Please press <SPACE> now.", podium, 570),
        Stars(screen, (screen.width + screen.height) // 2, 360)
    ]
    scenes.append(Scene(effects, -1))

    # Scene 3.
    path = Path()
    path.jump_to(podium[0], podium[1])

    effects = [
        Arrow(screen, path, colour=Screen.COLOUR_GREEN),
        _speak(screen, "This is a new Scene.", podium, 10),
        _speak(screen, "The Screen stops all Effects and clears itself between "
                       "Scenes.",
               podium, 70),
        _speak(screen, "That's why you can't see the Stars now.", podium, 130),
        _speak(screen, "(Though you can override that if you need to.)", podium,
               200),
        _speak(screen, "Please press <SPACE> now.", podium, 270),
    ]
    scenes.append(Scene(effects, -1))

    # Scene 4.
    path = Path()
    path.jump_to(podium[0], podium[1])

    effects = [
        Arrow(screen, path, colour=Screen.COLOUR_GREEN),
        _speak(screen, "So, how do you design your animation?", podium, 10),
        _speak(screen, "1) Decide on your cinematic flow of Scenes.", podium,
               80),
        _speak(screen, "2) Create the Effects in each Scene.", podium, 150),
        _speak(screen, "3) Pass the Scenes to the Screen to play.", podium,
               220),
        _speak(screen, "It really is that easy!", podium, 290),
        _speak(screen, "Just look at this sample code.", podium, 360),
        _speak(screen, "Please press <SPACE> now.", podium, 430),
    ]
    scenes.append(Scene(effects, -1))

    # Scene 5.
    path = Path()
    path.jump_to(podium[0], podium[1])

    effects = [
        Arrow(screen, path, colour=Screen.COLOUR_GREEN),
        _speak(screen, "There are various effects you can use.  For "
                       "example...",
               podium, 10),
        Cycle(screen,
              FigletText("Colour cycling"),
              centre[1] - 5,
              start_frame=100),
        Cycle(screen,
              FigletText("using Figlet"),
              centre[1] + 1,
              start_frame=100),
        _speak(screen, "Look in the effects module for more...",
               podium, 290),
        _speak(screen, "Please press <SPACE> now.", podium, 360),
    ]
    scenes.append(Scene(effects, -1))

    # Scene 6.
    path = Path()
    path.jump_to(podium[0], podium[1])
    curve_path = []
    for i in range(0, 11):
        curve_path.append(
            (centre[0] + (screen.width / 4 * math.sin(i * math.pi / 5)),
             centre[1] - (screen.height / 4 * math.cos(i * math.pi / 5))))
    path2 = Path()
    path2.jump_to(centre[0], centre[1] - screen.height // 4),
    path2.move_round_to(curve_path, 60)

    effects = [
        Arrow(screen, path, colour=Screen.COLOUR_GREEN),
        _speak(screen, "Sprites (like me) are also an Effect.", podium, 10),
        _speak(screen, "We take a pre-defined Path to follow.", podium, 80),
        _speak(screen, "Like this one...", podium, 150),
        Plot(screen, path2, colour=Screen.COLOUR_BLUE, start_frame=160,
             stop_frame=300),
        _speak(screen, "My friend Sam will now follow it...", podium, 320),
        Sam(screen, copy.copy(path2), start_frame=380),
        _speak(screen, "Please press <SPACE> now.", podium, 420),
    ]
    scenes.append(Scene(effects, -1))

    # Scene 7.
    path = Path()
    path.jump_to(podium[0], podium[1])
    path.wait(60)
    path.move_straight_to(-5, podium[1], 20)
    path.wait(300)

    effects = [
        Arrow(screen, path, colour=Screen.COLOUR_GREEN),
        _speak(screen, "Goodbye!", podium, 10),
        Cycle(screen,
              FigletText("THE END!"),
              centre[1] - 4,
              start_frame=100),
        Print(screen, SpeechBubble("Press X to exit"), centre[1] + 6,
              start_frame=150)
    ]
    scenes.append(Scene(effects, 500))

    screen.play(scenes, stop_on_resize=True)


if __name__ == "__main__":
    while True:
        try:
            Screen.wrapper(demo)
            sys.exit(0)
        except ResizeScreenError:
            pass
