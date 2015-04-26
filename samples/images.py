from asciimatics.effects import BannerText, Print, Scroll
from asciimatics.renderers import ImageFile, ColourImageFile
from asciimatics.scene import Scene
from asciimatics.screen import Screen
import curses


def demo(win):
    screen = Screen(win)

    scenes = []
    effects = [
        Print(screen, ColourImageFile(screen, "colour_globe.gif",
                                      screen.height-2), 0,
              stop_frame=200),
    ]
    scenes.append(Scene(effects))
    effects = [
        Print(screen, ColourImageFile(screen, "grumpy_cat.jpg", 40),
              screen.height,
              stop_frame=(40+screen.height)*3),
        Scroll(screen, 3)
    ]
    scenes.append(Scene(effects))
    effects = [
        BannerText(screen, ColourImageFile(screen, "python.png",
                                           screen.height-2), 0, 0),
    ]
    scenes.append(Scene(effects))

    screen.play(scenes)


if __name__ == "__main__":
    curses.wrapper(demo)

