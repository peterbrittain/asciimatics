"""
This module provides `Sprites` to create animation effects with Paths.  For more details see
http://asciimatics.readthedocs.io/en/latest/animation.html
"""
from asciimatics.effects import Sprite
from asciimatics.renderers import StaticRenderer
import random

# Images for Sam-ple sprite.
from asciimatics.screen import Screen

sam_default = [
    """
    ______
  .`      `.
 /   -  -   \\
|     __     |
|            |
 \\          /
  '.______.'
""",
    """
    ______
  .`      `.
 /   o  o   \\
|     __     |
|            |
 \\          /
  '.______.'
"""
]
sam_left = """
    ______
  .`      `.
 / o        \\
|            |
|--          |
 \\          /
  '.______.'
"""
sam_right = """
    ______
  .`      `.
 /        o \\
|            |
|          --|
 \\          /
  '.______.'
"""
sam_down = """
    ______
  .`      `.
 /          \\
|            |
|    ^  ^    |
 \\   __     /
  '.______.'
"""
sam_up = """
    ______
  .`  __  `.
 /   v  v   \\
|            |
|            |
 \\          /
  '.______.'
"""

# Images for an arrow Sprite.
left_arrow = """
 /____
/
\\ ____
 \\
"""
up_arrow = """
  /\\
 /  \\
/|  |\\
 |  |
 """
right_arrow = """
____\\
     \\
____ /
    /
"""
down_arrow = """
 |  |
\\|  |/
 \\  /
  \\/
 """
default_arrow = [
    """
  /\\
 /  \\
/|><|\\
 |  |
 """,
    """
  /\\
 /  \\
/|oo|\\
 |  |
 """,
]


# Simple static function to swap between 2 images to make a sprite blink.
def _blink():
    if random.random() > 0.9:
        return 0
    else:
        return 1


class Sam(Sprite):
    """
    Sam Paul sprite - an simple sample animated character.
    """

    def __init__(self, screen, path, start_frame=0, stop_frame=0):
        """
        See :py:obj:`.Sprite` for details.
        """
        super().__init__(
            screen,
            renderer_dict={
                "default": StaticRenderer(images=sam_default, animation=_blink),
                "left": StaticRenderer(images=[sam_left]),
                "right": StaticRenderer(images=[sam_right]),
                "down": StaticRenderer(images=[sam_down]),
                "up": StaticRenderer(images=[sam_up]),
            },
            path=path,
            start_frame=start_frame,
            stop_frame=stop_frame)


class Arrow(Sprite):
    """
    Sample arrow sprite - points where it is going.
    """

    def __init__(self, screen, path, colour=Screen.COLOUR_WHITE, start_frame=0,
                 stop_frame=0):
        """
        See :py:obj:`.Sprite` for details.
        """
        super().__init__(
            screen,
            renderer_dict={
                "default": StaticRenderer(images=default_arrow,
                                          animation=_blink),
                "left": StaticRenderer(images=[left_arrow]),
                "right": StaticRenderer(images=[right_arrow]),
                "down": StaticRenderer(images=[down_arrow]),
                "up": StaticRenderer(images=[up_arrow]),
            },
            path=path,
            colour=colour,
            start_frame=start_frame,
            stop_frame=stop_frame)


class Plot(Sprite):
    """
    Sample Sprite that simply plots an "X" for each step in the path.  Useful
    for plotting a path to the screen.
    """

    def __init__(self, screen, path, colour=Screen.COLOUR_WHITE, start_frame=0,
                 stop_frame=0):
        """
        See :py:obj:`.Sprite` for details.
        """
        super().__init__(
            screen,
            renderer_dict={
                "default": StaticRenderer(images=["X"])
            },
            path=path,
            colour=colour,
            clear=False,
            start_frame=start_frame,
            stop_frame=stop_frame)
