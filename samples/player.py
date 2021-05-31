#!/usr/bin/env python3
import sys
import logging
from asciimatics.effects import Print
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.renderers import AnsiArtPlayer, AsciinemaPlayer, SpeechBubble
from asciimatics.exceptions import ResizeScreenError

logging.basicConfig(filename="debug.log", level=logging.DEBUG)


def demo(screen, scene):
    with AsciinemaPlayer("test.rec", max_delay=0.1) as player, \
            AnsiArtPlayer("fruit.ans", strip=True) as player2:
        screen.play(
            [
                Scene(
                    [
                        Print(screen, player, 0, speed=1, transparent=False),
                        Print(screen,
                              SpeechBubble("Press space to see ansi art"),
                              y=screen.height - 3, speed=0, transparent=False)
                    ], -1),
                Scene(
                    [
                        Print(screen, player2, 0, speed=1, transparent=False),
                        Print(screen,
                              SpeechBubble("Press space to see asciinema"),
                              y=screen.height - 3, speed=0, transparent=False)
                    ], -1)
            ],
            stop_on_resize=True, start_scene=scene, allow_int=True)


last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
