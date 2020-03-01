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
XXXXXXXXXXXXXXXX
""".strip().split("\n")
BLOCK_SIZE = 8
FOV = pi / 3


def demo(screen, scene):
    # Basic state
    player_angle = pi / 2
    x, y = 1.5, 1.5
    view_distance = 4

    while True:
        # Draw the background - simple split of floor and ceiling.
        screen.clear_buffer(0, 0, 7, 0, 0, screen.width, screen.height // 2)
        screen.clear_buffer(0, 0, 0, 0, screen.height // 2, screen.width, screen.height - screen.height // 2)

        # Now do the ray casting across the visible canvas.
        # Compensate for aspect ratio by treating 2 cells as a single pixel.
        for sx in range(0, screen.width, 2):
            # Calculate the ray for this vertical slice.
            angle = FOV * sx / screen.width - (FOV / 2) + player_angle
            ray_x = cos(angle)
            ray_y = sin(angle)

            # Find current square in map
            next_x_step = 1 / tan(angle)
            next_y_step = int(copysign(1, ray_y))
            map_y = int(y + (next_y_step + 1) // 2)
            map_x = x + next_x_step * (map_y - y)
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
            next_y_step = tan(angle)
            map2_x = int(x + (next_x_step + 1) // 2)
            map2_y = y + next_y_step * (map2_x - x)
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
                    colour = 9
                    c = abs(map_x - int(map_x))
                else:
                    wall = int(BLOCK_SIZE * view_distance / dist2)
                    colour = 1
                    c = abs(map2_y - int(map2_y))
                for sy in range(wall):
                    screen.print_at("##", sx, (screen.height - wall) // 2 + sy, colour, bg=colour)
                if c < 0.02:
                    for sy in range(wall):
                        screen.print_at("|", sx, (screen.height - wall) // 2 + sy, 0, bg=0)

        screen.print_at("{} {} {} {}".format(x, y, cos(player_angle), sin(player_angle)), 0, 0)
        screen.print_at("{} {} {} {}".format(map_x, map_y, map2_x, map2_y), 0, 1)
        screen.print_at("{} {} {}".format(hit, hit2, tan(angle)), 0, 2)
        screen.refresh()

        # Allow movement
        c = screen.get_key()
        if c == ord("q"):
            break
        elif c == ord("z"):
            player_angle -= pi / 10
        elif c == ord("x"):
            player_angle += pi / 10
        elif c == ord("k"):
            x += cos(player_angle)
            y += sin(player_angle)
        elif c == ord("m"):
            x -= cos(player_angle)
            y -= sin(player_angle)
        screen.wait_for_input(0.05)

if __name__ == "__main__":
    last_scene = None
    while True:
        try:
            Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
            sys.exit(0)
        except ResizeScreenError as e:
            last_scene = e.scene
