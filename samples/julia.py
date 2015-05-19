import curses
from asciimatics.effects import Julia
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError


def demo(win):
    screen = Screen.from_curses(win)
    finished = False
    while not finished:
        scenes = []
        effects = [
            Julia(screen),
        ]
        scenes.append(Scene(effects, -1))
        try:
            screen.play(scenes, stop_on_resize=True)
            finished = True
        except ResizeScreenError:
            screen = Screen.from_curses(win)

curses.wrapper(demo)
