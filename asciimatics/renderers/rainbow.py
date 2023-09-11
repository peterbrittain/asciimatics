"""
This module implements a rainbow effect renderer.
"""
from asciimatics.renderers.base import StaticRenderer


class Rainbow(StaticRenderer):
    """
    Chained renderer to add rainbow colours to output of another renderer.
    The embedded rendered must not use multi-colour mode (i.e. ${c,a}
    mark-ups) as these will be converted to explicit text by this renderer.
    """

    # Colour palette when limited to 16 colours (8 dim and 8 bright).
    _16_palette = [1, 1, 3, 3, 2, 2, 6, 6, 4, 4, 5, 5]

    # Colour palette for 256 colour xterm mode.
    _256_palette = [196, 202, 208, 214, 220, 226,
                    154, 118, 82, 46,
                    47, 48, 49, 50, 51,
                    45, 39, 33, 27, 21,
                    57, 93, 129, 201,
                    200, 199, 198, 197]

    def __init__(self, screen, renderer):
        """
        :param screen: The screen object for this renderer.
        :param renderer: The renderer to wrap.
        """
        super().__init__()
        palette = self._256_palette if screen.colours > 16 else self._16_palette
        for image in renderer.images:
            new_image = ""
            for y, line in enumerate(image):
                for x, c in enumerate(line):
                    colour = (x + y) % len(palette)
                    new_image += '${%d,1}%s' % (palette[colour], c)
                if y < len(image) - 1:
                    new_image += "\n"
            self._images.append(new_image)
