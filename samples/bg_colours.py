#!/usr/bin/env python3

from __future__ import division
from asciimatics.effects import Wipe, Print
from asciimatics.renderers import FigletText, SpeechBubble
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import sys


def demo(screen):
    scenes = []

    for bg, name in [
            (Screen.COLOUR_RED, "RED"),
            (Screen.COLOUR_YELLOW, "YELLOW"),
            (Screen.COLOUR_GREEN, "GREEN"),
            (Screen.COLOUR_CYAN, "CYAN"),
            (Screen.COLOUR_BLUE, "BLUE"),
            (Screen.COLOUR_MAGENTA, "MAGENTA"),
            (Screen.COLOUR_WHITE, "WHITE")]:
        effects = [
            Wipe(screen, bg=bg, stop_frame=screen.height * 2 + 30),
            Print(screen, FigletText(name, "epic"), screen.height // 2 - 4,
                  colour=7 - bg,
                  bg=bg,
                  start_frame=screen.height * 2),
            Print(screen,
                  SpeechBubble("Testing background colours - press X to exit"),
                  screen.height-5,
                  speed=1, transparent=False)
        ]
        scenes.append(Scene(effects, 0, clear=False))

    screen.play(scenes, stop_on_resize=True)


if __name__ == "__main__":
    while True:
        try:
            Screen.wrapper(demo)
            sys.exit(0)
        except ResizeScreenError:
            pass
