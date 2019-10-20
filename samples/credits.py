from __future__ import division
from pyfiglet import Figlet

from asciimatics.effects import Scroll, Mirage, Wipe, Cycle, Matrix, \
    BannerText, Stars, Print
from asciimatics.particles import DropScreen
from asciimatics.renderers import FigletText, SpeechBubble, Rainbow, Fire
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import sys


def _credits(screen):
    scenes = []

    text = Figlet(font="banner", width=200).renderText("ASCIIMATICS")
    width = max([len(x) for x in text.split("\n")])

    effects = [
        Print(screen,
              Fire(screen.height, 80, text, 0.4, 40, screen.colours),
              0,
              speed=1,
              transparent=False),
        Print(screen,
              FigletText("ASCIIMATICS", "banner"),
              screen.height - 9, x=(screen.width - width) // 2 + 1,
              colour=Screen.COLOUR_BLACK,
              bg=Screen.COLOUR_BLACK,
              speed=1),
        Print(screen,
              FigletText("ASCIIMATICS", "banner"),
              screen.height - 9,
              colour=Screen.COLOUR_WHITE,
              bg=Screen.COLOUR_WHITE,
              speed=1),
    ]
    scenes.append(Scene(effects, 100))

    effects = [
        Matrix(screen, stop_frame=200),
        Mirage(
            screen,
            FigletText("Asciimatics"),
            screen.height // 2 - 3,
            Screen.COLOUR_GREEN,
            start_frame=100,
            stop_frame=200),
        Wipe(screen, start_frame=150),
        Cycle(
            screen,
            FigletText("Asciimatics"),
            screen.height // 2 - 3,
            start_frame=200)
    ]
    scenes.append(Scene(effects, 250, clear=False))

    effects = [
        BannerText(
            screen,
            Rainbow(screen, FigletText(
                "Reliving the 80s in glorious ASCII text...", font='slant')),
            screen.height // 2 - 3,
            Screen.COLOUR_GREEN)
    ]
    scenes.append(Scene(effects))

    effects = [
        Scroll(screen, 3),
        Mirage(
            screen,
            FigletText("Conceived and"),
            screen.height,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("written by:"),
            screen.height + 8,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("Peter Brittain"),
            screen.height + 16,
            Screen.COLOUR_GREEN)
    ]
    scenes.append(Scene(effects, (screen.height + 24) * 3))

    effects = [
        Scroll(screen, 3),
        Mirage(
            screen,
            FigletText("With help from:"),
            screen.height,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("Cory Benfield"),
            screen.height + 8,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("Bryce Guinta"),
            screen.height + 16,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("Aman Orazaev"),
            screen.height + 24,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("Daniel Kerr"),
            screen.height + 32,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("Dylan Janeke"),
            screen.height + 40,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("ianadeem"),
            screen.height + 48,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("Scott Mudge"),
            screen.height + 56,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("Luke Murphy"),
            screen.height + 64,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("mronkain"),
            screen.height + 72,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("Dougal Sutherland"),
            screen.height + 80,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("Kirtan Sakariya"),
            screen.height + 88,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("Jesse Lieberg"),
            screen.height + 96,
            Screen.COLOUR_GREEN),
        Mirage(
            screen,
            FigletText("Erik Doffagne"),
            screen.height + 104,
            Screen.COLOUR_GREEN)
    ]
    scenes.append(Scene(effects, (screen.height + 104) * 3))

    effects = [
        Cycle(
            screen,
            FigletText("ASCIIMATICS", font='big'),
            screen.height // 2 - 8,
            stop_frame=100),
        Cycle(
            screen,
            FigletText("ROCKS!", font='big'),
            screen.height // 2 + 3,
            stop_frame=100),
        Stars(screen, (screen.width + screen.height) // 2, stop_frame=100),
        DropScreen(screen, 100, start_frame=100)
    ]
    scenes.append(Scene(effects, 200))

    effects = [
        Print(screen,
              SpeechBubble("Press 'X' to exit."), screen.height // 2 - 1, attr=Screen.A_BOLD)
    ]
    scenes.append(Scene(effects, -1))

    screen.play(scenes, stop_on_resize=True)


if __name__ == "__main__":
    while True:
        try:
            Screen.wrapper(_credits)
            sys.exit(0)
        except ResizeScreenError:
            pass
