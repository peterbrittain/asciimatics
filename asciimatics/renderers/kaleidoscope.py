"""
This module implements a kaeldioscope effect renderer.
"""

from math import sin, cos, pi, atan2

from asciimatics.renderers.base import DynamicRenderer


class Kaleidoscope(DynamicRenderer):
    """
    Renderer to create a 2-mirror kaleidoscope effect.

    This is a chained renderer (i.e. it acts upon the output of another Renderer which is
    passed to it on construction).  The other Renderer is used as the cell that is rotated over
    time to create the animation.

    You can specify the desired rotational symmetry of the kaleidoscope (which determines the
    angle between the mirrors).  If you chose values of less than 2, you are effectively removing
    one or both mirrors, thus either getting the original cell or a simple mirrored image of the
    cell.

    Since this renderer rotates the background cell, it needs operate on square pixels, which
    means each character in the cell is drawn as 2 next to each other on the screen.  In other
    words the cell needs to be half the width of the desired output (when measured in text
    characters).
    """

    def __init__(self, height, width, cell, symmetry):
        """
        :param height: Height of the box to contain the kaleidoscope.
        :param width: Width of the box to contain the kaleidoscope.
        :param cell: A Renderer to use as the backing cell for the kaleidoscope.
        :param symmetry: The desired rotational symmetry.  Must be a non-negative integer.
        """
        super().__init__(height, width)
        self._symmetry = symmetry
        self._rotation = 0
        self._cell = cell

    def _render_now(self):
        # Rotate a point (x, y) through an angle theta.
        def _rotate(x, y, theta):
            return x * cos(theta) - y * sin(theta), x * sin(theta) + y * cos(theta)

        # Reflect a point (x, y) in a line at angle theta
        def _reflect(x, y, theta):
            return x * cos(2 * theta) + y * sin(2 * theta), x * sin(2 * theta) - y * cos(2 * theta)

        # Get the base cell now - so we can pick out characters as needed.
        text, colour_map = self._cell.rendered_text

        # Integer maths will result in gaps between characters if you rotate from the starting
        # point to desired end-point.  We therefore look for the reverse mapping from the final
        # character and trace-back instead.
        for dx in range(self._canvas.width // 2):
            for dy in range(self._canvas.height):
                # Figure out which segment of the circle we're in, so we know what affine
                # transformations to apply.
                ox = dx - self._canvas.width / 4
                oy = dy - self._canvas.height / 2
                segment = round(atan2(oy, ox) * self._symmetry / pi)
                if segment % 2 == 0:
                    # Just a rotation required for even segments.
                    x1, y1 = _rotate(
                        ox, oy, 0 if self._symmetry == 0 else -segment * pi / self._symmetry)
                else:
                    # Odd segments require a rotation and then a reflection.
                    x1, y1 = _rotate(ox, oy, (1 - segment) * pi / self._symmetry)
                    x1, y1 = _reflect(x1, y1, pi / self._symmetry / 2)

                # Now rotate once more to simulate the rotation of the background cell too.
                x1, y1 = _rotate(x1, y1, self._rotation)

                # Re-normalize back to the box coordinates and draw the character that we found
                # from the reverse mapping.
                x2 = int(x1 + self._cell.max_width / 2)
                y2 = int(y1 + self._cell.max_height / 2)
                if (0 <= y2 < len(text)) and (0 <= x2 < len(text[y2])):
                    self._write(text[y2][x2] + text[y2][x2],
                                dx * 2,
                                dy,
                                colour_map[y2][x2][0],
                                colour_map[y2][x2][1],
                                colour_map[y2][x2][2])

        # Now rotate the background cell for the next frame.
        self._rotation += pi / 180

        return self._plain_image, self._colour_map
