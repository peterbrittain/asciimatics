"""
This module provides common code for all Renderers.
"""

from abc import ABCMeta, abstractmethod
import re

from wcwidth.wcwidth import wcswidth

from asciimatics.screen import Screen, TemporaryCanvas
from asciimatics.constants import COLOUR_REGEX

#: Attribute conversion table for the ${c,a} form of attributes for
#: :py:obj:`~.Screen.paint`.
ATTRIBUTES = {
    "1": Screen.A_BOLD,
    "2": Screen.A_NORMAL,
    "3": Screen.A_REVERSE,
    "4": Screen.A_UNDERLINE,
}


class Renderer(metaclass=ABCMeta):
    """
    A Renderer is simply a class that will return one or more text renderings
    for display by an Effect.

    In the simple case, this can be a single string that contains some
    unchanging content - e.g. a simple text message.

    It can also represent a sequence of strings that can be played one after
    the other to make a simple animation sequence - e.g. a rotating globe.
    """

    @property
    @abstractmethod
    def max_width(self):
        """
        :return: The max width of the rendered text (across all images if an animated renderer).
        """

    @property
    @abstractmethod
    def rendered_text(self):
        """
        :return: The next image and colour map in the sequence as a tuple.
        """

    @property
    @abstractmethod
    def images(self):
        """
        :return: An iterator of all the images in the Renderer.
        """

    @property
    @abstractmethod
    def max_height(self):
        """
        :return: The max height of the rendered text (across all images if an animated renderer).
        """

    def __repr__(self):
        """
        :returns: a plain string representation of the next rendered image.
        """
        return "\n".join(self.rendered_text[0])


class StaticRenderer(Renderer):
    """
    A StaticRenderer is a Renderer that can create all possible images in
    advance.  After construction the images will not change, but can by cycled
    for animation purposes.

    This class will also convert text like ${c,a,b} into colour c, attribute a
    and background b for any subsequent text in the line, thus allowing
    multi-coloured text.  The attribute and background are optional.
    """

    # Regular expression for use to find colour sequences in multi-colour text.
    # It should match ${n}, ${m,n} or ${m,n,o}
    _colour_sequence = re.compile(COLOUR_REGEX)

    def __init__(self, images=None, animation=None):
        """
        :param images: An optional set of ascii images to be rendered.
        :param animation: A function to pick the image (from images) to be
                          rendered for any given frame.
        """
        super().__init__()
        self._images = images if images is not None else []
        self._index = 0
        self._max_width = 0
        self._max_height = 0
        self._animation = animation
        self._colour_map = None
        self._plain_images = []

    def _convert_images(self):
        """
        Convert any images into a more Screen-friendly format.
        """
        self._plain_images = []
        self._colour_map = []
        for image in self._images:
            colour_map = []
            new_image = []
            for line in image.split("\n"):
                new_line = ""
                attributes = (None, None, None)
                colours = []
                while len(line) > 0:
                    match = self._colour_sequence.match(line)
                    if match is None:
                        new_line += line[0]
                        colours.append(attributes)
                        line = line[1:]
                    else:
                        # The regexp either matches:
                        # - 2,3,4 for ${c,a,b}
                        # - 5,6 for ${c,a}
                        # - 7 for ${c}.
                        if match.group(2) is not None:
                            attributes = (int(match.group(2)),
                                          ATTRIBUTES[match.group(3)],
                                          int(match.group(4)))
                        elif match.group(5) is not None:
                            attributes = (int(match.group(5)),
                                          ATTRIBUTES[match.group(6)],
                                          None)
                        else:
                            attributes = (int(match.group(7)), 0, None)
                        line = match.group(8)
                new_image.append(new_line)
                colour_map.append(colours)
            self._plain_images.append(new_image)
            self._colour_map.append(colour_map)

    @property
    def images(self):
        """
        :return: An iterator of all the images in the Renderer.
        """
        if len(self._plain_images) <= 0:
            self._convert_images()

        return iter(self._plain_images)

    @property
    def rendered_text(self):
        """
        :return: The next image and colour map in the sequence as a tuple.
        """
        if len(self._plain_images) <= 0:
            self._convert_images()

        if self._animation is None:
            index = self._index
            self._index += 1
            if self._index >= len(self._plain_images):
                self._index = 0
        else:
            index = self._animation()
        return (self._plain_images[index],
                self._colour_map[index])

    @property
    def max_height(self):
        """
        :return: The max height of the rendered text (across all images if an animated renderer).
        """
        if len(self._plain_images) <= 0:
            self._convert_images()

        if self._max_height == 0:
            for image in self._plain_images:
                self._max_height = max(len(image), self._max_height)
        return self._max_height

    @property
    def max_width(self):
        """
        :return: The max width of the rendered text (across all images if an animated renderer).
        """
        if len(self._plain_images) <= 0:
            self._convert_images()

        if self._max_width == 0:
            for image in self._plain_images:
                new_max = max(wcswidth(x) for x in image)
                self._max_width = max(new_max, self._max_width)
        return self._max_width


class DynamicRenderer(Renderer, metaclass=ABCMeta):
    """
    A DynamicRenderer is a Renderer that creates each image as requested.  It
    has a defined maximum size on construction.
    """

    def __init__(self, height, width, clear=True):
        """
        :param height: The max height of the rendered image.
        :param width: The max width of the rendered image.
        """
        super().__init__()
        self._must_clear = clear
        self._canvas = TemporaryCanvas(height, width)

    def _clear(self):
        """
        Clear the current image.
        """
        # self._canvas.clear_buffer(Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)
        self._canvas.clear_buffer(None, 0, 0)

    def _write(self, text, x, y, colour=Screen.COLOUR_WHITE,
               attr=Screen.A_NORMAL, bg=Screen.COLOUR_BLACK):
        """
        Write some text to the specified location in the current image.

        :param text: The text to be added.
        :param x: The X coordinate in the image.
        :param y: The Y coordinate in the image.
        :param colour: The colour of the text to add.
        :param attr: The attribute of the image.
        :param bg: The background colour of the text to add.

        This is only kept for back compatibility.  Direct access to the canvas methods is
        preferred.
        """
        self._canvas.print_at(text, x, y, colour, attr, bg)

    @property
    def _plain_image(self):
        return self._canvas.plain_image

    @property
    def _colour_map(self):
        return self._canvas.colour_map

    @abstractmethod
    def _render_now(self):
        """
        Common method to render the latest image.

        :returns: A tuple of the plain image and the colour map as per
        :py:meth:`.rendered_text`.
        """

    @abstractmethod
    def _render_all(self):
        """
        Generate all output.

        If this renderer cannot reasonably return everything, it will just return the next frame (as
        per _render_now() inside an iterable object.

        :returns: an iterable of image/colour map tuples.
        """

    @property
    def images(self):
        # Attempt to get all images.  Note that many are genuinely dynamic and so will only return one.
        return [x[0] for x in self._render_all()]

    @property
    def rendered_text(self):
        if self._must_clear:
            self._clear()
        return self._render_now()

    @property
    def max_height(self):
        return self._canvas.height

    @property
    def max_width(self):
        return self._canvas.width
