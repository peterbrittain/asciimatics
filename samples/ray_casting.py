#!/usr/bin/env python3

# -*- coding: utf-8 -*-
import sys
from math import sin, cos, pi, copysign, floor
from asciimatics.effects import Effect
from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import ResizeScreenError, StopApplication
from asciimatics.renderers import ColourImageFile
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.widgets import PopUpDialog


HELP = """
Use the following keys:

- Cursor keys to move.
- M to toggle the mini-map
- X to quit
- 1 to 4 to change rendering mode.

Can you find grumpy cat?
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
IMAGE_HEIGHT = 64


class Image(object):
    """
    Class to handle image stripe rendering.
    """

    def __init__(self, image):
        self._image = image

    def next_frame(self):
        self._frame = self._image.rendered_text

    def draw_stripe(self, screen, height, x, image_x):
        # Clip required dimensions.
        y_start, y_end = 0, height
        if height > screen.height:
            y_start = (height - screen.height) // 2
            y_end = y_start + screen.height + 1

        # Draw the stripe for the required region.
        for sy in range(y_start, y_end):
            try:
                y = int((screen.height - height) / 2) + sy
                image_y = int(sy * IMAGE_HEIGHT / height)
                char = self._frame[0][image_y][image_x]
                # Unicode images use . for background only pixels; ascii ones use space.
                if char not in (" ", "."):
                    fg, attr, bg = self._frame[1][image_y][image_x]
                    attr = 0 if attr is None else attr
                    bg = 0 if bg is None else bg
                    screen.fast_poke(char, x, y, fg, attr, bg)
            except IndexError:
                pass


class Sprite(object):
    """
    Dynamically sized sprite.
    """

    def __init__(self, state, x, y, images):
        self._state = state
        self.x, self.y = x, y
        self._images = images

    def next_frame(self):
        for image in self._images:
            image.next_frame()

    def draw_stripe(self, height, x, image_x):
        # Resize offset in image for the expected height of this stripe.
        self._images[self._state.mode % 2].draw_stripe(
            self._state.screen, height, x, int(image_x * IMAGE_HEIGHT / height))


class GameState(object):
    """
    Persistent state for this application.
    """

    def __init__(self):
        self.player_angle = pi / 2
        self.x, self.y = 1.5, 1.5
        self.map = LEVEL_MAP
        self.mode = 0
        self.show_mini_map = True
        self.images = {}
        self.sprites = []
        self.screen = None

    def load_image(self, screen, filename):
        self.images[filename] = [None, None]
        self.images[filename][0] = Image(ColourImageFile(screen, filename, IMAGE_HEIGHT, uni=False))
        self.images[filename][1] = Image(ColourImageFile(screen, filename, IMAGE_HEIGHT, uni=True))

    def update_screen(self, screen):
        # Save off active screen.
        self.screen = screen

        # Images only need initializing once - they don't actually use the screen after construction.
        if len(self.images) <= 0:
            self.load_image(screen, "grumpy_cat.jpg")
            self.load_image(screen, "colour_globe.gif")
            self.load_image(screen, "wall.png")

        # Demo uses static sprites, so can reset every time now we have images loaded.
        self.sprites = [
            Sprite(self, 3.5, 6.5, self.images["grumpy_cat.jpg"]),
            Sprite(self, 14.5, 11.5, self.images["colour_globe.gif"]),
            Sprite(self, 0, 0, self.images["wall.png"])
        ]

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

    def __init__(self, screen, game_state):
        super(RayCaster, self).__init__(screen)
        # Controls for rendering.
        #
        # Ideally we'd just use a field of vision (FOV) to represent the screen aspect ratio.  However, this
        # looks wrong for very wide screens.  So, limit to 4:1 aspect ratio, then calculate FOV.
        self.width = min(screen.height * 4, screen.width)
        self.FOV = self.width / screen.height / 4

        # Remember game state for later.
        self._state = game_state

        # Set up raycasting sizes and colours
        self._block_size = screen.height // 3
        if screen.colours >= 256:
            self._colours = [x for x in zip(range(255, 232, -1), [0] * 24, range(255, 232, -1))]
        else:
            self._colours = [(Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_WHITE) for _ in range(6)]
            self._colours.extend([(Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_WHITE) for _ in range(9)])
            self._colours.extend([(Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK) for _ in range(9)])
            self._colours.append((Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_BLACK))

    def _update(self, _):
        # First draw the background - which is theoretically the floor and ceiling.
        self._screen.clear_buffer(Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_BLACK)

        # Now do the ray casting across the visible canvas.
        # Compensate for aspect ratio by treating 2 cells as a single pixel.
        x_offset = (self._screen.width - self.width ) // 2
        last_side = None
        z_buffer = [999999 for _ in range(self.width + 1)]
        camera_x = cos(self._state.player_angle + pi / 2) * self.FOV
        camera_y = sin(self._state.player_angle + pi / 2) * self.FOV
        for sx in range(0, self.width, 2 - self._state.mode // 2):
            # Calculate the ray for this vertical slice.
            camera_segment = 2 * sx / self.width - 1
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
                z_buffer[sx], z_buffer[sx + 1] = dist, dist

                # Are we drawing block colours or ray traced walls?
                if self._state.mode < 2:
                    # Simple block colours - get height and text attributes
                    wall = min(self._screen.height, int(self._screen.height / dist))
                    colour, attr, bg = self._colours[min(len(self._colours) - 1, int(3 * dist))]
                    text = self._TEXTURES[min(len(self._TEXTURES) - 1, int(2 * dist))]

                    # Now draw the wall segment
                    for sy in range(wall):
                        self._screen.print_at(
                            text * 2, x_offset + sx, (self._screen.height - wall) // 2 + sy,
                            colour, attr, bg=0 if self._state.mode == 0 else bg)
                else:
                    # Ray casting - get wall texture
                    image = self._state.images["wall.png"][self._state.mode % 2]

                    # Get texture height and stripe offset bearing in mind pixels are 1x2 aspect ratio.
                    wall = int(self._screen.height / dist)
                    if hit_side:
                        wall_x = self._state.x + dist * ray_x;
                    else:
                        wall_x = self._state.y + dist * ray_y;
                    wall_x -= int(wall_x);
                    texture_x = int(wall_x * IMAGE_HEIGHT * 2);
                    if (not hit_side) and ray_x > 0:
                        texture_x = IMAGE_HEIGHT * 2 - texture_x - 1;
                    if hit_side and ray_y < 0:
                        texture_x = IMAGE_HEIGHT * 2 - texture_x - 1;

                    # Now draw it
                    image.next_frame()
                    image.draw_stripe(self._screen, wall, x_offset + sx, texture_x)

                # Draw a line when we change surfaces to help make it easier to see the 3d effect
                if hit_side != last_side:
                    last_side = hit_side
                    for sy in range(wall):
                        self._screen.print_at("|", x_offset + sx, (self._screen.height - wall) // 2 + sy, 0, bg=0)

        # Now draw sprites
        ray_x = cos(self._state.player_angle)
        ray_y = sin(self._state.player_angle)
        for sprite in self._state.sprites:
            # Translate sprite position to relative to camera
            sprite_x = sprite.x - self._state.x
            sprite_y = sprite.y - self._state.y
            inv_det = 1.0 / (camera_x * ray_y - ray_x * camera_y)
            transform_x = inv_det * (ray_y * sprite_x - ray_x * sprite_y);
            transform_y = inv_det * (-camera_y * sprite_x + camera_x * sprite_y)

            # Sprite location on camera plane.
            sprite_screen_x = int((self.width / 2) * (1 + transform_x / transform_y));

            # Calculate height (and width) of the sprite on screen
            sprite_height = abs(int(self._screen.height / (transform_y)))

            # Don't bother if behind the viewing plane (or too big to render).
            if transform_y > 0:
                # Update for animation
                sprite.next_frame()

                # Loop through every vertical stripe of the sprite on screen
                start = max(0, sprite_screen_x - sprite_height)
                end = min(self.width, sprite_screen_x + sprite_height)
                for stripe in range(start, end):
                    if stripe > 0 and stripe < self.width and transform_y < z_buffer[stripe]:
                        texture_x = int(stripe - (-sprite_height + sprite_screen_x) * sprite_height / sprite_height)
                        sprite.draw_stripe(sprite_height, x_offset + stripe, texture_x)

    @property
    def frame_update_count(self):
        # Animation required - every other frame should be OK for demo.
        return 1

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
        # Standard setup for every screen.
        self._screen = screen
        self._state = game_state
        self._mini_map = MiniMap(screen, self._state, self._screen.height // 4)
        effects = [
            RayCaster(screen, self._state)
        ]
        super(GameController, self).__init__(effects, -1)

        # Add minimap if required.
        if self._state.show_mini_map:
            self.add_effect(self._mini_map)

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
            elif c in (ord("1"), ord("2"), ord("3"), ord("4")):
                self._state.mode = c - ord("1")
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
    game_state.update_screen(screen)
    screen.play([GameController(screen, game_state)], stop_on_resize=True, allow_int=True)


if __name__ == "__main__":
    game_state = GameState()
    while True:
        try:
            Screen.wrapper(demo, catch_interrupt=False, arguments=[game_state])
            sys.exit(0)
        except ResizeScreenError:
            pass
