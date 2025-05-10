"""
This module implements a typewriter renderer.
"""
from asciimatics.renderers.base import DynamicRenderer


class Typewriter(DynamicRenderer):
    """
    Renderer to create a typewriter effect based on a specified source.
    """

    def __init__(self, source):
        """
        :param source: Source renderer to by typed.
        """
        super().__init__(source.max_height, source.max_width)
        self._source = source
        self._count = 0

    def reset(self):
        self._count = 0

    def _render_all(self):
        while self._count < sum(len(x) for x in self._source.rendered_text[0]):
            yield self._render_now()

    def _render_now(self):
        # Now build the rendered text from the source and current limit.
        self._count += 1
        count = 0
        text, colour_map = self._source.rendered_text
        for y, row in enumerate(text):
            for x, char in enumerate(row):
                count += 1
                if count > self._count:
                    break
                self._write(char,
                            x, y,
                            colour_map[y][x][0],
                            colour_map[y][x][1],
                            colour_map[y][x][2])

        return self._plain_image, self._colour_map
