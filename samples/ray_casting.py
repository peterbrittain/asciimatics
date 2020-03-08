# -*- coding: utf-8 -*-
import sys
from math import sin, cos, tan, atan2, pi, copysign, sqrt
from asciimatics.effects import Effect
from asciimatics.event import KeyboardEvent
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.exceptions import ResizeScreenError, StopApplication


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

    def __init__(self):
        self.player_angle = pi / 2
        self.x, self.y = 1.5, 1.5
        self.map = LEVEL_MAP
        self.mode = 1


class MiniMap(Effect):
    def __init__(self, screen, game_state):
        super(MiniMap, self).__init__(screen)
        self._state = game_state

    def _update(self, _):
        # Draw the map segment
        for mx in range(5):
            for my in range(5):
                px = int(self._state.x) + mx - 2
                py = int(self._state.y) + my - 2
                text = self._state.map[py][px] * 2 if 0 <= py < len(self._state.map) and 0 <= px < len(self._state.map[0]) else "  "
                self._screen.print_at(text, self._screen.width - 12 + 2*mx, self._screen.height - 6 + my, 1, 0)

        # Draw the player
        # TODO: Fix this repetition
        if self._state.player_angle < pi / 4 or self._state.player_angle > 7 * pi / 4:
            self._screen.print_at(">>", self._screen.width - 8, self._screen.height - 4, 2, 0)
        elif self._state.player_angle < 3 * pi / 4:
            self._screen.print_at("vv", self._screen.width - 8, self._screen.height - 4, 2, 0)
        elif self._state.player_angle < 5 * pi / 4:
            self._screen.print_at("<<", self._screen.width - 8, self._screen.height - 4, 2, 0)
        else:
            self._screen.print_at("^^", self._screen.width - 8, self._screen.height - 4, 2, 0)

    @property
    def stop_frame(self):
        # No specific end point for this Effect.  Carry on running forever.
        return 0

    def reset(self):
        # Nothing special to do.  Just need this to satisfy the ABC.
        pass


class RayCaster(Effect):

    # Textures to get less intense with distance.
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

            # Now draw the wall segment
            if hit or hit2:
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
    def __init__(self, screen, game_state):
        self._screen = screen
        self._state = game_state
        effects = [
            RayCaster(screen, self._state),
            MiniMap(screen, self._state)
        ]
        super(DemoScene, self).__init__(effects, -1)

    def _safe_update_x(self, old_x, old_y, new_x):
        if 0 <= old_y < len(self._state.map) and 0 <= new_x < len(self._state.map[0]):
            if self._state.map[int(old_y)][int(new_x)] == "X":
                return old_x
        return new_x

    def _safe_update_y(self, old_x, old_y, new_y):
        if 0 <= new_y < len(self._state.map) and 0 <= old_x < len(self._state.map[0]):
            if self._state.map[int(new_y)][int(old_x)] == "X":
                return old_y
        return new_y

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            c = event.key_code
            if c == ord("q"):
                raise StopApplication("User exit")
            elif c in (ord("z"), Screen.KEY_LEFT):
                self._state.player_angle -= pi / 45
                if self._state.player_angle < 0:
                    self._state.player_angle += 2 * pi
            elif c in (ord("x"), Screen.KEY_RIGHT):
                self._state.player_angle += pi / 45
                if self._state.player_angle > 2 * pi:
                    self._state.player_angle -= 2 * pi
            elif c in (ord("k"), Screen.KEY_UP):
                self._state.x = self._safe_update_x(self._state.x, self._state.y, self._state.x + cos(self._state.player_angle) / 5)
                self._state.y = self._safe_update_y(self._state.x, self._state.y, self._state.y + sin(self._state.player_angle) / 5)
            elif c in (ord("m"), Screen.KEY_DOWN):
                self._state.x = self._safe_update_x(self._state.x, self._state.y, self._state.x - cos(self._state.player_angle) / 5)
                self._state.y = self._safe_update_y(self._state.x, self._state.y, self._state.y - sin(self._state.player_angle) / 5)
            elif c in (ord("1"), ord("2")):
                self._state.mode = c - ord("0")
            else:
                return super(DemoScene, self).process_event(self, event)
        else:
            return super(DemoScene, self).process_event(self, event)


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
