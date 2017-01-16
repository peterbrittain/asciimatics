from __future__ import division
from asciimatics.effects import BannerText, Print, Scroll
from asciimatics.renderers import ColourImageFile, FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import sys


def demo(screen):
    scenes = []
    effects = [
        Print(screen,
              ColourImageFile(screen, "colour_globe.gif", screen.height-2,
                              uni=screen.unicode_aware,
                              dither=screen.unicode_aware),
              0,
              stop_frame=200),
        Print(screen,
              FigletText("ASCIIMATICS NEWS", font='banner3'),
              screen.height//2-3,
              colour=7, bg=7 if screen.unicode_aware else 0),
    ]
    scenes.append(Scene(effects))
    effects = [
        Print(screen,
              ColourImageFile(screen, "grumpy_cat.jpg", screen.height,
                              uni=screen.unicode_aware),
              screen.height,
              stop_frame=(40+screen.height)*3),
        Scroll(screen, 3)
    ]
    scenes.append(Scene(effects))
    effects = [
        BannerText(screen,
                   ColourImageFile(screen, "python.png", screen.height-2,
                                   uni=screen.unicode_aware, dither=screen.unicode_aware),
                   0, 0),
    ]
    scenes.append(Scene(effects))

    screen.play(scenes, stop_on_resize=True)


if __name__ == "__main__":
    while True:
        try:
            Screen.wrapper(demo)
            sys.exit(0)
        except ResizeScreenError:
            pass
