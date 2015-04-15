# coding=utf-8
from pyfiglet import Figlet, DEFAULT_FONT
from PIL import Image


class Renderer(object):
    """
    A Renderer is simply a class that will return one or more text renderings
    for display by an Effect.

    In the simple case, this can be a single string that contains some
    unchanging content - e.g. a simple text message.

    It can also represent a sequence of strings that can be played one after
    the other to make a simple animation sequence - e.g. a rotating globe.
    """

    def __init__(self, images=None, animation=None):
        """
        Constructor.
        """
        self._images = images if images is not None else []
        self._index = 0
        self._max_width = 0
        self._max_height = 0
        self._animation = animation

    @property
    def rendered_text(self):
        """
        :return: The next image in the sequence.
        """
        if self._animation is None:
            result = self._images[self._index]
            self._index += 1
            if self._index >= len(self._images):
                self._index = 0
        else:
            result = self._images[self._animation()]
        return result

    @property
    def max_width(self):
        """
        :return: The max width of the rendered text (across all images if an
            animated renderer.
        """
        if self._max_width == 0:
            for image in self._images:
                new_max = max([len(x) for x in image.split("\n")])
                self._max_width = max(new_max, self._max_width)
        return self._max_width

    @property
    def max_height(self):
        """
        :return: The max height of the rendered text (across all images if an
            animated renderer.
        """
        if self._max_height == 0:
            for image in self._images:
                self._max_height = max(len(image.split("\n")), self._max_height)
        return self._max_height


class FigletText(Renderer):
    """
    Simple renderer to convert a text string to a Figlet equivalent string.
    """

    def __init__(self, text, font=DEFAULT_FONT):
        """
        Constructor.

        :param text: The text string to convert with Figlet.
        :param font: The Figlet font to use.
        """
        super(FigletText, self).__init__()
        self._images = [Figlet(font=font).renderText(text)]


class _ImageSequence(object):
    """
    Simple class to make an interator for a PIL Image object.
    """

    def __init__(self, im):
        self.im = im

    def __getitem__(self, ix):
        try:
            if ix:
                self.im.seek(ix)
            return self.im
        except EOFError:
            raise IndexError


class ImageFile(Renderer):
    """
    Renderer to convert animage file (as supported by the Python Imaging
    Library) into an ascii greyscale text image.
    """

    # The ASCII grey scale from darkest to lightest.
    _greyscale = ' .:;rsA23hHG#9&@'

    def __init__(self, filename, height=30):
        """
        Constructor.

        :param filename: The name of the file to render.
        :param height: The height of the text rendered image.
        """
        super(ImageFile, self).__init__()
        image = Image.open(filename)
        background = image.info['background'] if 'background' in image.info \
            else None
        for frame in _ImageSequence(image):
            ascii_image = ""
            frame = frame.resize(
                (int(frame.size[0] * height * 2.0 / frame.size[1]), height),
                Image.BICUBIC)
            grey_frame = frame.convert('L')
            for py in range(0, grey_frame.size[1]):
                ascii_image += "\n"
                for px in range(0, grey_frame.size[0]):
                    real_col = frame.getpixel((px, py))
                    col = grey_frame.getpixel((px, py))
                    if real_col == background:
                        ascii_image += " "
                    else:
                        ascii_image += self._greyscale[
                            (int(col) * len(self._greyscale)) / 256]
            self._images.append(ascii_image)


class SpeechBubble(Renderer):
    """
    Renders supplied text into a speech bubble.
    """

    def __init__(self, text, tail=None):
        """
        Constructor.

        :param text: The text to be put into a speech bubble.
        :param tail: Where to put the bubble callout tail, specifying "L" or
                     "R" for left or right tails.  Can be None for no tail.
        """
        super(SpeechBubble, self).__init__()
        max_len = max([len(x) for x in text.split("\n")])
        bubble = ".-" + "-" * max_len + "-.\n"
        for line in text.split("\n"):
            bubble += "| " + line + " |\n"
            bubble += "`-" + "-" * max_len + "-`\n"
        if tail == "L":
            bubble += "  )/  \n"
            bubble += "-\"`\n"
        elif tail == "R":
            bubble += (" " * max_len) + "\\(  \n"
            bubble += (" " * max_len) + " `\"-\n"
        self._images = [bubble]


class Box(Renderer):
    """
    Renders a simple box using ASCII characters.  This does not render in
    extended box drawing characters as that requires direct use of the curses
    API to draw non-ASCII characters (which is not supported by Effects that
    take Renderer parameters).
    """

    def __init__(self, width, height):
        """
        Constructor.

        :param width: The desired width of the box.
        :param height: The desired height of the box.
        """
        super(Box, self).__init__()
        box = "+" + "-" * (width-2) + "+\n"
        for line in range(height-2):
            box += "|" + " " * (width-2) + "|\n"
        box += "+" + "-" * (width-2) + "+\n"
        self._images = [box]
