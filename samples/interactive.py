from asciimatics.exceptions import ResizeScreenError
from asciimatics.screen import Screen
from asciimatics.paths import DynamicPath
from asciimatics.sprites import Arrow
from asciimatics.scene import Scene
import sys


class Controller(DynamicPath):
    def process_key(self, key):
        if key == Screen.KEY_UP:
            self._y -= 1
            self._y = max(self._y, 2)
        elif key == Screen.KEY_DOWN:
            self._y += 1
            self._y = min(self._y, self._screen.height-2)
        elif key == Screen.KEY_LEFT:
            self._x -= 1
            self._x = max(self._x, 3)
        elif key == Screen.KEY_RIGHT:
            self._x += 1
            self._x = min(self._x, self._screen.width-3)
        else:
            return key


class InteractiveArrow(Arrow):
    def __init__(self, screen):
        """
        See :py:obj:`.Sprite` for details.
        """
        super(InteractiveArrow, self).__init__(
            screen,
            path=Controller(screen, screen.width // 2, screen.height // 2),
            colour=Screen.COLOUR_GREEN)


def demo(screen):
    scenes = []
    effects = [
        InteractiveArrow(screen),
    ]
    scenes.append(Scene(effects, -1))

    screen.play(scenes, stop_on_resize=True)


if __name__ == "__main__":
    while True:
        try:
            Screen.wrapper(demo)
            sys.exit(0)
        except ResizeScreenError:
            pass
