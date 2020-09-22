#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import sys
from math import sin, cos, pi, copysign, floor
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

    @property
    def map_x(self):
        return int(floor(self.x))

    @property
    def map_y(self):
        return int(floor(self.y))

    def safe_update_x(self, new_x):
        new_x += self.x
        if 0 <= self.y < len(self.map) and 0 <= new_x < len(self.map[0]):
            if self.map[self.map_y][int(floor(new_x))] == "X":
                return
        self.x = new_x

    def safe_update_y(self, new_y):
        new_y += self.y
        if 0 <= new_y < len(self.map) and 0 <= self.x < len(self.map[0]):
            if self.map[int(floor(new_y))][self.map_x] == "X":
                return
        self.y = new_y

    def safe_update_angle(self, new_angle):
        self.player_angle += new_angle
        if self.player_angle < 0:
            self.player_angle += 2 * pi
        if self.player_angle > 2 * pi:
            self.player_angle -= 2 * pi


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
                px = self._state.map_x + mx - self._size // 2
                py = self._state.map_y + my - self._size // 2
                if (0 <= py < len(self._state.map) and
                        0 <= px < len(self._state.map[0]) and self._state.map[py][px] != " "):
                    colour = Screen.COLOUR_RED
                else:
                    colour = Screen.COLOUR_BLACK
                self._screen.print_at("  ", self._x + 2 * mx, self._y + my, colour, bg=colour)

        # Draw the player
        text = ">>"
        for a, b, direction in self._DIRECTIONS:
            if a < self._state.player_angle <= b:
                text = direction
                break
        self._screen.print_at(
            text, self._x + self._size // 2 * 2, self._y + self._size // 2, Screen.COLOUR_GREEN)

    @property
    def frame_update_count(self):
        # No animation required.
        return 0

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

    This class follows the logic from https://lodev.org/cgtutor/raycasting.html.
    """

    # Textures to emulate h distance.
    _TEXTURES = "@&#$AHhwai;:. "

    # Controls for rendering - this is the relative size of the camera plane to the viewing vector.
    FOV = 0.66

    def __init__(self, screen, game_state):
        super(RayCaster, self).__init__(screen)
        self._state = game_state
        self._block_size = screen.height // 3
        if screen.colours >= 256:
            self._colours = [x for x in zip(range(255, 232, -1), [0] * 24, range(255, 232, -1))]
        else:
            self._colours = [(Screen.COLOUR_WHITE, Screen.A_BOLD, 0) for _ in range(6)]
            self._colours.extend([(Screen.COLOUR_WHITE, Screen.A_NORMAL, 0) for _ in range(9)])
            self._colours.extend([(Screen.COLOUR_BLACK, Screen.A_BOLD, 0) for _ in range(9)])
            self._colours.append((Screen.COLOUR_BLACK, Screen.A_NORMAL, 0))

    def _update(self, _):
        # First draw the background - which is theoretically the floor and ceiling.
        self._screen.clear_buffer(Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_BLACK)

        # Now do the ray casting across the visible canvas.
        # Compensate for aspect ratio by treating 2 cells as a single pixel.
        last_side = None
        for sx in range(0, self._screen.width, 2):
            # Calculate the ray for this vertical slice.
            camera_x = cos(self._state.player_angle + pi / 2) * self.FOV
            camera_y = sin(self._state.player_angle + pi / 2) * self.FOV
            camera_segment = 2 * sx / self._screen.width - 1
            ray_x = cos(self._state.player_angle) + camera_x * camera_segment
            ray_y = sin(self._state.player_angle) + camera_y * camera_segment

            # Representation of the ray within our map
            map_x = self._state.map_x
            map_y = self._state.map_y
            hit = False
            hit_side = False

            # Logical length along the ray from one x or y-side to next x or y-side
            try:
                ratio_to_x = abs(1 / ray_x)
            except ZeroDivisionError:
                ratio_to_x = 999999
            try:
                ratio_to_y = abs(1 / ray_y)
            except ZeroDivisionError:
                ratio_to_y = 999999

            # Calculate block step direction and initial partial step to the next side (on same
            # logical scale as the previous ratios).
            step_x = int(copysign(1, ray_x))
            step_y = int(copysign(1, ray_y))
            side_x = (self._state.x - map_x) if ray_x < 0 else (map_x + 1.0 - self._state.x)
            side_x *= ratio_to_x
            side_y = (self._state.y - map_y) if ray_y < 0 else (map_y + 1.0 - self._state.y)
            side_y *= ratio_to_y

            # Give up if we'll never intersect the map
            while (((step_x < 0 and map_x >= 0) or (step_x > 0 and map_x < len(self._state.map[0]))) and
                   ((step_y < 0 and map_y >= 0) or (step_y > 0 and map_y < len(self._state.map)))):
                # Move along the ray to the next nearest side (measured in distance along the ray).
                if side_x < side_y:
                    side_x += ratio_to_x
                    map_x += step_x
                    hit_side = False
                else:
                    side_y += ratio_to_y
                    map_y += step_y
                    hit_side = True

                # Check whether the ray has now hit a wall.
                if 0 <= map_x < len(self._state.map[0]) and 0 <= map_y < len(self._state.map):
                    if self._state.map[map_y][map_x] == "X":
                        hit = True
                        break

            # Draw wall if needed.
            if hit:
                # Figure out textures and colours to use based on the distance to the wall.
                if hit_side:
                    dist = (map_y - self._state.y + (1 - step_y) / 2) / ray_y
                else:
                    dist = (map_x - self._state.x + (1 - step_x) / 2) / ray_x
                wall = min(self._screen.height, int(self._screen.height / dist))
                colour, attr, bg = self._colours[min(len(self._colours) - 1, int(3 * dist))]
                text = self._TEXTURES[min(len(self._TEXTURES) - 1, int(2 * dist))]

                # Now draw the wall segment
                for sy in range(wall):
                    self._screen.print_at(
                        text * 2, sx, (self._screen.height - wall) // 2 + sy,
                        colour, attr, bg=0 if self._state.mode == 1 else bg)

                # Draw a line when we change surfaces to help make it easier to see the 3d effect
                if hit_side != last_side:
                    last_side = hit_side
                    for sy in range(wall):
                        self._screen.print_at("|", sx, (self._screen.height - wall) // 2 + sy, 0, bg=0)

    @property
    def frame_update_count(self):
        # No animation required.
        return 0

    @property
    def stop_frame(self):
        # No specific end point for this Effect.  Carry on running forever.
        return 0

    def reset(self):
        # Nothing special to do.  Just need this to satisfy the ABC.
        pass


class GameController(Scene):
    """
    Scene to control the combined Effects for the demo.

    This class handles the user input, updating the game state and updating required Effects as needed.
    Drawing of the Scene is then handled in the usual way.
    """

    def __init__(self, screen, game_state):
        self._screen = screen
        self._state = game_state
        self._mini_map = MiniMap(screen, self._state, self._screen.height // 4)
        effects = [
            RayCaster(screen, self._state),
            self._mini_map
        ]
        super(GameController, self).__init__(effects, -1)

    def process_event(self, event):
        # Allow standard event processing first
        if super(GameController, self).process_event(event) is None:
            return

        # If that didn't handle it, check for a key that this demo understands.
        if isinstance(event, KeyboardEvent):
            c = event.key_code
            if c in (ord("x"), ord("X")):
                raise StopApplication("User exit")
            elif c in (ord("a"), Screen.KEY_LEFT):
                self._state.safe_update_angle(-pi / 45)
            elif c in (ord("d"), Screen.KEY_RIGHT):
                self._state.safe_update_angle(pi / 45)
            elif c in (ord("w"), Screen.KEY_UP):
                self._state.safe_update_x(cos(self._state.player_angle) / 5)
                self._state.safe_update_y(sin(self._state.player_angle) / 5)
            elif c in (ord("s"), Screen.KEY_DOWN):
                self._state.safe_update_x(-cos(self._state.player_angle) / 5)
                self._state.safe_update_y(-sin(self._state.player_angle) / 5)
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
    screen.play([GameController(screen, game_state)], stop_on_resize=True)


if __name__ == "__main__":
    game_state = GameState()
    while True:
        try:
            Screen.wrapper(demo, catch_interrupt=False, arguments=[game_state])
            sys.exit(0)
        except ResizeScreenError:
            pass
