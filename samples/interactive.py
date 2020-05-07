#!/usr/bin/env python3

from asciimatics.effects import Sprite, Print
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.exceptions import ResizeScreenError
from asciimatics.renderers import StaticRenderer, SpeechBubble, FigletText
from asciimatics.screen import Screen
from asciimatics.paths import DynamicPath
from asciimatics.sprites import Arrow
from asciimatics.scene import Scene
import sys

# Sprites used for the demo
arrow = None
cross_hairs = None


class KeyboardController(DynamicPath):
    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            key = event.key_code
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
                return event
        else:
            return event


class MouseController(DynamicPath):
    def __init__(self, sprite, scene, x, y):
        super(MouseController, self).__init__(scene, x, y)
        self._sprite = sprite

    def process_event(self, event):
        if isinstance(event, MouseEvent):
            self._x = event.x
            self._y = event.y
            if event.buttons & MouseEvent.DOUBLE_CLICK != 0:
                # Try to whack the other sprites when mouse is clicked
                self._sprite.whack("KERPOW!")
            elif event.buttons & MouseEvent.LEFT_CLICK != 0:
                # Try to whack the other sprites when mouse is clicked
                self._sprite.whack("BANG!")
            elif event.buttons & MouseEvent.RIGHT_CLICK != 0:
                # Try to whack the other sprites when mouse is clicked
                self._sprite.whack("CRASH!")
        else:
            return event


class TrackingPath(DynamicPath):
    def __init__(self, scene, path):
        super(TrackingPath, self).__init__(scene, 0, 0)
        self._path = path

    def process_event(self, event):
        return event

    def next_pos(self):
        x, y = self._path.next_pos()
        return x + 8, y - 2


class Speak(Sprite):
    def __init__(self, screen, scene, path, text, **kwargs):
        """
        See :py:obj:`.Sprite` for details.
        """
        super(Speak, self).__init__(
            screen,
            renderer_dict={
                "default": SpeechBubble(text, "L")
            },
            path=TrackingPath(scene, path),
            colour=Screen.COLOUR_CYAN,
            **kwargs)


class InteractiveArrow(Arrow):
    def __init__(self, screen):
        """
        See :py:obj:`.Sprite` for details.
        """
        super(InteractiveArrow, self).__init__(
            screen,
            path=KeyboardController(
                screen, screen.width // 2, screen.height // 2),
            colour=Screen.COLOUR_GREEN)

    def say(self, text):
        self._scene.add_effect(
            Speak(self._screen, self._scene, self._path, text, delete_count=50))


class CrossHairs(Sprite):
    def __init__(self, screen):
        """
        See :py:obj:`.Sprite` for details.
        """
        super(CrossHairs, self).__init__(
            screen,
            renderer_dict={
                "default": StaticRenderer(images=["X"])
            },
            path=MouseController(
                self, screen, screen.width // 2, screen.height // 2),
            colour=Screen.COLOUR_RED)

    def whack(self, sound):
        x, y = self._path.next_pos()
        if self.overlaps(arrow, use_new_pos=True):
            arrow.say("OUCH!")
        else:
            self._scene.add_effect(Print(
                self._screen,
                SpeechBubble(sound), y, x, clear=True, delete_count=50))


def demo(screen):
    global arrow, cross_hairs
    arrow = InteractiveArrow(screen)
    cross_hairs = CrossHairs(screen)

    scenes = []
    effects = [
        Print(screen, FigletText("Hit the arrow with the mouse!", "digital"),
              y=screen.height//3-3),
        Print(screen, FigletText("Press space when you're ready.", "digital"),
              y=2 * screen.height//3-3),
    ]
    scenes.append(Scene(effects, -1))

    effects = [
        arrow,
        cross_hairs
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
