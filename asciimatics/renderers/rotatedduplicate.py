"""
This module implements a renderer that renders another renderer but rotated.
"""

from asciimatics.renderers.base import StaticRenderer


class RotatedDuplicate(StaticRenderer):
    """
    Chained renderer to add a rotated version of the original renderer underneath and centre the
    whole thing within within the specified dimensions.
    """

    def __init__(self, width, height, renderer):
        """
        :param width: The maximum width of the rendered text.
        :param height: The maximum height of the rendered text.
        :param renderer: The renderer to wrap.
        """
        super().__init__()
        for image in renderer.images:
            mx = (width - max(len(x) for x in image)) // 2
            my = height // 2 - len(image)
            tab = (" " * mx if mx > 0 else "") + "\n" + (" " * mx if mx > 0 else "")
            new_image = []
            new_image.extend(["" for _ in range(max(0, my))])
            new_image.extend(image)
            new_image.extend([x[::-1] for x in reversed(image)])
            new_image.extend(["" for _ in range(max(0, my))])
            if mx < 0:
                new_image = [x[-mx:mx] for x in new_image]
            if my < 0:
                new_image = new_image[-my:my]
            self._images.append(tab.join(new_image))
