"""
This module implements renderers that show measuring scales to the screen.
"""
from asciimatics.renderers.base import StaticRenderer


class Scale(StaticRenderer):
    """
    This renders a linear scale, useful for debugging positions of your
    creations. Every 5 spaces gets a tick mark, every 10 a number.
    """

    def __init__(self, width):
        """
        :param width: The width of the scale
        """
        super().__init__()

        contents = []
        for x in range(1, width + 1):
            if x % 10 == 0 and x > 0:
                contents.append(str(x)[-2])
            elif x % 5 == 0:
                contents.append('+')
            else:
                contents.append('-')

        text = ''.join(contents)

        self._images = [text]


class VScale(StaticRenderer):
    """
    This renders a vertical linear scale, useful for debugging positions of your
    creations. Writes lowest significant digit of a count running vertically.
    """

    def __init__(self, height):
        """
        :param width: The width of the scale
        """
        super().__init__()

        contents = [str(i)[-1] for i in range(1, height + 1)]
        text = '\n'.join(contents)

        self._images = [text]
