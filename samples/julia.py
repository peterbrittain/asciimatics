import curses
from asciimatics.effects import Julia
from asciimatics.scene import Scene
from asciimatics.screen import Screen


def demo(win):
    screen = Screen.from_curses(win)
    scenes = []
    effects = [
        Julia(screen),
    ]
    scenes.append(Scene(effects, -1))
    screen.play(scenes)

curses.wrapper(demo)
