# -*- coding: utf-8 -*-
import sys
from math import sin, cos, tan, atan2, pi, copysign, sqrt
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication, InvalidFields


MAP = """
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
BLOCK_SIZE = 8
FOV = pi / 2
COLOURS = range(255, 232, -1)
TEXTURES = "@&#$AHhwai;:. "


def demo(screen, scene):
    # Basic state
    player_angle = pi / 2
    x, y = 1.5, 1.5
    view_distance = 4

    while True:
        # Draw the background - simple split of floor and ceiling.
        screen.clear_buffer(0, 0, 0, 0, 0, screen.width, screen.height // 2)
        screen.clear_buffer(0, 0, 0, 0, screen.height // 2, screen.width, screen.height - screen.height // 2)

        # Now do the ray casting across the visible canvas.
        # Compensate for aspect ratio by treating 2 cells as a single pixel.
        last_x, last_y, last_side = -1, -1, None
        for sx in range(0, screen.width, 2):
            # Calculate the ray for this vertical slice.
            angle = FOV * sx / screen.width - (FOV / 2) + player_angle
            ray_x = cos(angle)
            ray_y = sin(angle)

            # Find current square in map
            next_y_step = int(copysign(1, ray_y))
            try:
                next_x_step = next_y_step / tan(angle)
            except ZeroDivisionError:
                next_x_step = 9999999
            map_y = int(y + (next_y_step + 1) // 2)
            map_x = x + next_x_step * abs(map_y - y)
            hit = False
            while True:
                try:
                    if MAP[map_y + (next_y_step - 1) // 2][int(map_x)] == "X":
                        hit = True
                        break
                    map_x += next_x_step
                    map_y += next_y_step
                except IndexError:
                    break

            next_x_step = int(copysign(1, ray_x))
            next_y_step = next_x_step * tan(angle)
            map2_x = int(x + (next_x_step + 1) // 2)
            map2_y = y + next_y_step * abs(map2_x - x)
            hit2 = False
            while True:
                try:
                    if MAP[int(map2_y)][map2_x + (next_x_step - 1) // 2] == "X":
                        hit2 = True
                        break
                    map2_x += next_x_step
                    map2_y += next_y_step
                except IndexError:
                    break

            if hit or hit2:
                dist = sqrt((map_x - x) ** 2 + (map_y - y) ** 2) * cos(FOV * sx / screen.width - (FOV / 2))
                dist2 = sqrt((map2_x - x) ** 2 + (map2_y - y) ** 2) * cos(FOV * sx / screen.width - (FOV / 2))
                if hit and dist < dist2:
                    wall = int(BLOCK_SIZE * view_distance / dist)
                    colour = COLOURS[min(len(COLOURS) - 1, int(3 * dist))]
                    text = TEXTURES[min(len(TEXTURES) - 1, int(2 * dist))]
                    new_x, new_y, new_side = int(map_x), int(map_y), False
                else:
                    wall = int(BLOCK_SIZE * view_distance / dist2)
                    colour = COLOURS[min(len(COLOURS) - 1, int(3 * dist2))]
                    text = TEXTURES[min(len(TEXTURES) - 1, int(2 * dist2))]
                    new_x, new_y, new_side = int(map2_x), int(map2_y), True
                wall = min(screen.height, wall)
                for sy in range(wall):
                    screen.print_at(text * 2, sx, (screen.height - wall) // 2 + sy, colour)
                if (new_x, new_y, new_side) != (last_x, last_y, last_side):
                    last_x, last_y, last_side = new_x, new_y, new_side
                    for sy in range(wall):
                        screen.print_at("|", sx, (screen.height - wall) // 2 + sy, 0, bg=0)


        #Add a minimap
        for mx in range(5):
            for my in range(5):
                px = int(x) + mx - 2
                py = int(y) + my - 2
                text = MAP[py][px] * 2 if 0 <= py < len(MAP) and 0 <= px < len(MAP[0]) else "  "
                screen.print_at(text, screen.width - 12 + 2*mx, screen.height - 6 + my, 1, 0)
        if player_angle < pi / 4 or player_angle > 7 * pi / 4:
            screen.print_at(">>", screen.width - 8, screen.height - 4, 2, 0)
        elif player_angle < 3 * pi / 4:
            screen.print_at("vv", screen.width - 8, screen.height - 4, 2, 0)
        elif player_angle < 5 * pi / 4:
            screen.print_at("<<", screen.width - 8, screen.height - 4, 2, 0)
        else:
            screen.print_at("^^", screen.width - 8, screen.height - 4, 2, 0)

        screen.refresh()

        # Allow movement
        def _safe_update_x(old_x, old_y, new_x):
            if 0 <= old_y < len(MAP) and 0 <= new_x < len(MAP[0]):
                if MAP[int(old_y)][int(new_x)] == "X":
                    return old_x
            return new_x

        def _safe_update_y(old_x, old_y, new_y):
            if 0 <= new_y < len(MAP) and 0 <= old_x < len(MAP[0]):
                if MAP[int(new_y)][int(old_x)] == "X":
                    return old_y
            return new_y

        c = screen.get_key()
        if c == ord("q"):
            break
        elif c in (ord("z"), Screen.KEY_LEFT):
            player_angle -= pi / 45
            if player_angle < 0:
                player_angle += 2 * pi
        elif c in (ord("x"), Screen.KEY_RIGHT):
            player_angle += pi / 45
            if player_angle > 2 * pi:
                player_angle -= 2 * pi
        elif c in (ord("k"), Screen.KEY_UP):
            x = _safe_update_x(x, y, x + cos(player_angle) / 5)
            y = _safe_update_y(x, y, y + sin(player_angle) / 5)
        elif c in (ord("m"), Screen.KEY_DOWN):
            x = _safe_update_x(x, y, x - cos(player_angle) / 5)
            y = _safe_update_y(x, y, y - sin(player_angle) / 5)
        screen.wait_for_input(0.05)

if __name__ == "__main__":
    last_scene = None
    while True:
        try:
            Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
            sys.exit(0)
        except ResizeScreenError as e:
            last_scene = e.scene
