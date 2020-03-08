# -*- coding: utf-8 -*-
import sys
from math import sin, cos, tan, atan2, pi, copysign, sqrt
from asciimatics.effects import Effect
from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import ResizeScreenError, StopApplication
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.widgets import PopUpDialog


HELP = """
Use the following keys:

- Cursor keys to move.
- M to toggle the mini-map
- X to quit
- 1 or 2 to change rendering mode.
"""
LEVEL_MAP = """
XXXXXXXXXXXXXXXX
X              X
X  X        X  X
X  X  X     X  X
X XXX X  XXXX  X
X XXX X XX    XX
X X XXX    XXXXX
X X XXX XXXXX  X
X X     X      X
X XXXXX   XXXXXX
X              X
XXXXXXXXXXXXXX X
""".strip().split("\n")


class GameState(object):
    """
    Persistent state for this application.
    """

    def __init__(self):
        self.player_angle = pi / 2
        self.x, self.y = 1.5, 1.5
        self.map = LEVEL_MAP
        self.mode = 1
        self.show_mini_map = True

    # TODO: Consider changing to property for this and update y.
    def safe_update_x(self, new_x):
        if 0 <= self.y < len(self.map) and 0 <= new_x < len(self.map[0]):
            if self.map[int(self.y)][int(new_x)] == "X":
                return
        self.x = new_x

    def safe_update_y(self, new_y):
        if 0 <= new_y < len(self.map) and 0 <= self.x < len(self.map[0]):
            if self.map[int(new_y)][int(self.x)] == "X":
                return
        self.y = new_y


class MiniMap(Effect):
    """
    Class to draw a small map based on the one stored in the GameState.
    """

    # Translation from angle to map directions.
    _DIRECTIONS = [
        (0, pi / 4, ">>"),
        (pi / 4, 3 * pi / 4, "vv"),
        (3 * pi / 4, 5 * pi / 4, "<<"),
        (5 * pi / 4, 7 * pi / 4, "^^")
    ]

    def __init__(self, screen, game_state, size=5):
        super(MiniMap, self).__init__(screen)
        self._state = game_state
        self._size = size
        self._x = self._screen.width - 2 * (self._size + 1)
        self._y = self._screen.height - (self._size + 1)

    def _update(self, _):
        # Draw the miniature map.
        for mx in range(self._size):
            for my in range(self._size):
                px = int(self._state.x) + mx - self._size // 2
                py = int(self._state.y) + my - self._size // 2
                text = self._state.map[py][px] * 2 if 0 <= py < len(self._state.map) and 0 <= px < len(self._state.map[0]) else "  "
                self._screen.print_at(text, self._x + 2 * mx, self._y + my, Screen.COLOUR_RED)

        # Draw the player
        text = ">>"
        for a, b, direction in self._DIRECTIONS:
            if a < self._state.player_angle <= b:
                text = direction
                break
        self._screen.print_at(text, self._x + self._size // 2 * 2, self._y + self._size // 2, Screen.COLOUR_GREEN)

    @property
    def stop_frame(self):
        # No specific end point for this Effect.  Carry on running forever.
        return 0

    def reset(self):
        # Nothing special to do.  Just need this to satisfy the ABC.
        pass


class RayCaster(Effect):
    """
    Raycaster effect - will draw a 3D rendition of the map stored in the GameState.
    """

    # Textures to emulate h distance.
    _TEXTURES = "@&#$AHhwai;:. "

    # Controls for rendering - where to project screen and field of vision for that projection
    VIEW_DISTANCE = 4
    FOV = pi / 3

    def __init__(self, screen, game_state):
        super(RayCaster, self).__init__(screen)
        # Basic state
        self._state = game_state
        self._block_size = screen.height // 3
        if screen.colours >= 256:
            self._colours = [x for x in zip(range(255, 232, -1), [0] * 24, range(255, 232, -1))]
        else:
            self._colours = [
                (7, Screen.A_BOLD, 0),
                (7, Screen.A_BOLD, 0),
                (7, Screen.A_BOLD, 0),
                (7, Screen.A_BOLD, 0),
                (7, Screen.A_BOLD, 0),
                (7, Screen.A_BOLD, 0),
                (7, Screen.A_NORMAL, 0),
                (7, Screen.A_NORMAL, 0),
                (7, Screen.A_NORMAL, 0),
                (7, Screen.A_NORMAL, 0),
                (7, Screen.A_NORMAL, 0),
                (7, Screen.A_NORMAL, 0),
                (7, Screen.A_NORMAL, 0),
                (7, Screen.A_NORMAL, 0),
                (7, Screen.A_NORMAL, 0),
                (0, Screen.A_BOLD, 0),
                (0, Screen.A_BOLD, 0),
                (0, Screen.A_BOLD, 0),
                (0, Screen.A_BOLD, 0),
                (0, Screen.A_BOLD, 0),
                (0, Screen.A_BOLD, 0),
                (0, Screen.A_BOLD, 0),
                (0, Screen.A_BOLD, 0),
                (0, Screen.A_BOLD, 0),
                (0, 0, 0)]

    def _update(self, _):
        # First Draw the background - simple split of floor and ceiling.
        # TODO: Use some form of distance for shading?
        self._screen.clear_buffer(0, 0, 0, 0, 0, self._screen.width, self._screen.height // 2)
        self._screen.clear_buffer(0, 0, 0, 0, self._screen.height // 2, self._screen.width, self._screen.height - self._screen.height // 2)

        # TODO: Revisit this algorithm.  Look at the combined version from other tutorial
        # Now do the ray casting across the visible canvas.
        # Compensate for aspect ratio by treating 2 cells as a single pixel.
        last_x, last_y, last_side = -1, -1, None
        for sx in range(0, self._screen.width, 2):
            # Calculate the ray for this vertical slice.
            angle = self.FOV * sx / self._screen.width - (self.FOV / 2) + self._state.player_angle
            ray_x = cos(angle)
            ray_y = sin(angle)

            # Find current square in map
            next_y_step = int(copysign(1, ray_y))
            try:
                next_x_step = next_y_step / tan(angle)
            except ZeroDivisionError:
                next_x_step = 9999999
            map_y = int(self._state.y + (next_y_step + 1) // 2)
            map_x = self._state.x + next_x_step * abs(map_y - self._state.y)
            hit = False
            while True:
                try:
                    if self._state.map[map_y + (next_y_step - 1) // 2][int(map_x)] == "X":
                        hit = True
                        break
                    map_x += next_x_step
                    map_y += next_y_step
                except IndexError:
                    break

            next_x_step = int(copysign(1, ray_x))
            next_y_step = next_x_step * tan(angle)
            map2_x = int(self._state.x + (next_x_step + 1) // 2)
            map2_y = self._state.y + next_y_step * abs(map2_x - self._state.x)
            hit2 = False
            while True:
                try:
                    if self._state.map[int(map2_y)][map2_x + (next_x_step - 1) // 2] == "X":
                        hit2 = True
                        break
                    map2_x += next_x_step
                    map2_y += next_y_step
                except IndexError:
                    break

            if hit or hit2:
                # Figure out textures and colours to use based on the distance to the wall.
                dist = sqrt((map_x - self._state.x) ** 2 + (map_y - self._state.y) ** 2) * cos(self.FOV * sx / self._screen.width - (self.FOV / 2))
                dist2 = sqrt((map2_x - self._state.x) ** 2 + (map2_y - self._state.y) ** 2) * cos(self.FOV * sx / self._screen.width - (self.FOV / 2))
                if hit and dist < dist2:
                    wall = int(self._block_size * self.VIEW_DISTANCE / dist)
                    colour, attr, bg = self._colours[min(len(self._colours) - 1, int(3 * dist))]
                    text = self._TEXTURES[min(len(self._TEXTURES) - 1, int(2 * dist))]
                    new_x, new_y, new_side = int(map_x), int(map_y), False
                else:
                    wall = int(self._block_size * self.VIEW_DISTANCE / dist2)
                    colour, attr, bg = self._colours[min(len(self._colours) - 1, int(3 * dist2))]
                    text = self._TEXTURES[min(len(self._TEXTURES) - 1, int(2 * dist2))]
                    new_x, new_y, new_side = int(map2_x), int(map2_y), True
                wall = min(self._screen.height, wall)

                # Now draw the wall segment
                for sy in range(wall):
                    self._screen.print_at(text * 2, sx, (self._screen.height - wall) // 2 + sy, colour, attr, bg=0 if self._state.mode == 1 else bg)

                # Draw a line when we change surfaces to help make it easier to see the 3d effect
                if new_side != last_side:
                    last_x, last_y, last_side = new_x, new_y, new_side
                    for sy in range(wall):
                        self._screen.print_at("|", sx, (self._screen.height - wall) // 2 + sy, 0, bg=0)

    @property
    def stop_frame(self):
        # No specific end point for this Effect.  Carry on running forever.
        return 0

    def reset(self):
        # Nothing special to do.  Just need this to satisfy the ABC.
        pass


class DemoScene(Scene):
    """
    Scene to control the combined Effects for the demo.

    This class handles the user input, updating the game state as required and will redraw everything on
    each frame update.
    """

    def __init__(self, screen, game_state):
        self._screen = screen
        self._state = game_state
        self._mini_map = MiniMap(screen, self._state, self._screen.height // 4)
        effects = [
            RayCaster(screen, self._state),
            self._mini_map
        ]
        super(DemoScene, self).__init__(effects, -1)

    def process_event(self, event):
        # Allow standard event processing first
        if super(DemoScene, self).process_event(event) is None:
            return

        # If that didn't handle it, check for a key that this demo understands.
        if isinstance(event, KeyboardEvent):
            c = event.key_code
            if c in (ord("x"), ord("X")):
                raise StopApplication("User exit")
            elif c in (ord("a"), Screen.KEY_LEFT):
                # TODO: Consider moving to game state property
                self._state.player_angle -= pi / 45
                if self._state.player_angle < 0:
                    self._state.player_angle += 2 * pi
            elif c in (ord("d"), Screen.KEY_RIGHT):
                self._state.player_angle += pi / 45
                if self._state.player_angle > 2 * pi:
                    self._state.player_angle -= 2 * pi
            elif c in (ord("w"), Screen.KEY_UP):
                self._state.safe_update_x(self._state.x + cos(self._state.player_angle) / 5)
                self._state.safe_update_y(self._state.y + sin(self._state.player_angle) / 5)
            elif c in (ord("s"), Screen.KEY_DOWN):
                self._state.safe_update_x(self._state.x - cos(self._state.player_angle) / 5)
                self._state.safe_update_y(self._state.y - sin(self._state.player_angle) / 5)
            elif c in (ord("1"), ord("2")):
                self._state.mode = c - ord("0")
            elif c in (ord("m"), ord("M")):
                self._state.show_mini_map = not self._state.show_mini_map
                if self._state.show_mini_map:
                    self.add_effect(self._mini_map)
                else:
                    self.remove_effect(self._mini_map)
            elif c in (ord("h"), ord("H")):
                self.add_effect(PopUpDialog(self._screen, HELP, ["OK"]))
            else:
                # Not a recognised key - pass on to other handlers.
                return event
        else:
            # Ignore other types of events.
            return event


def demo(screen, game_state):
    screen.play([DemoScene(screen, game_state)], stop_on_resize=True)


if __name__ == "__main__":
    game_state = GameState()
    while True:
        try:
            Screen.wrapper(demo, catch_interrupt=False, arguments=[game_state])
            sys.exit(0)
        except ResizeScreenError as e:
            pass
