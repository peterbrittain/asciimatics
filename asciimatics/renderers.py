# coding=utf-8
from pyfiglet import Figlet, DEFAULT_FONT
from PIL import Image
import re
import curses


#: Attribute conversion table for the ${c,a} form of attributes for
#: :py:obj:`.paint`.
ATTRIBUTES = {
    "1": curses.A_BOLD,
    "2": curses.A_NORMAL,
    "3": curses.A_REVERSE,
    "4": curses.A_UNDERLINE,
}


class Renderer(object):
    """
    A Renderer is simply a class that will return one or more text renderings
    for display by an Effect.

    In the simple case, this can be a single string that contains some
    unchanging content - e.g. a simple text message.

    It can also represent a sequence of strings that can be played one after
    the other to make a simple animation sequence - e.g. a rotating globe.

    This class will convert text like ${c,a} into colour c, attribute a for any
    subseqent text in the line, thus allowing multi-coloured text.  The
    attribute is optional.
    """

    # Regular expression for use to find colour sequences in multi-colour text.
    # It should match ${n} or ${m,n}
    _colour_esc_code = r"^\$\{((\d+),(\d+)|(\d+))\}(.*)"
    _colour_sequence = re.compile(_colour_esc_code)

    def __init__(self, images=None, animation=None):
        """
        :param images: An optional set of ascii images to be rendered.
        :param animation: A function to pick the image (from images) to be
                          rendered for any given frame.
        """
        self._images = images if images is not None else []
        self._index = 0
        self._max_width = 0
        self._max_height = 0
        self._animation = animation
        self._colour_map = None
        self._plain_images = None

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
                attrs = (None, None)
                colours = []
                while len(line) > 0:
                    match = self._colour_sequence.match(line)
                    if match is None:
                        new_line += line[0]
                        colours.append(attrs)
                        line = line[1:]
                    else:
                        # The regexp either matches ${c,a} for group 2,3 or
                        # ${c} for group 4.
                        if match.group(3) is None:
                            attrs = (int(match.group(4)), 0)
                        else:
                            attrs = (int(match.group(2)),
                                     ATTRIBUTES[match.group(3)])
                        line = match.group(5)
                new_image.append(new_line)
                colour_map.append(colours)
            self._plain_images.append(new_image)
            self._colour_map.append(colour_map)

    @property
    def rendered_text(self):
        """
        :return: The next image and colour map in the sequence as a tuple.
        """
        if self._plain_images is None:
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
    def max_width(self):
        """
        :return: The max width of the rendered text (across all images if an
            animated renderer.
        """
        if self._plain_images is None:
            self._convert_images()

        if self._max_width == 0:
            for image in self._plain_images:
                new_max = max([len(x) for x in image])
                self._max_width = max(new_max, self._max_width)
        return self._max_width

    @property
    def max_height(self):
        """
        :return: The max height of the rendered text (across all images if an
            animated renderer.
        """
        if self._plain_images is None:
            self._convert_images()

        if self._max_height == 0:
            for image in self._plain_images:
                self._max_height = max(len(image), self._max_height)
        return self._max_height


class FigletText(Renderer):
    """
    Simple renderer to convert a text string to a Figlet equivalent string.
    """

    def __init__(self, text, font=DEFAULT_FONT):
        """
        :param text: The text string to convert with Figlet.
        :param font: The Figlet font to use (optional).
        """
        super(FigletText, self).__init__()
        self._images = [Figlet(font=font, width=200).renderText(text)]


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
                        ascii_image += "${%d}" % (232 + col * 23/256)
                        ascii_image += self._greyscale[
                            (int(col) * len(self._greyscale)) / 256]
            self._images.append(ascii_image)


class ColourImageFile(Renderer):
    """
    Renderer to convert animage file (as supported by the Python Imaging
    Library) into an block image of available colours.
    """

    def __init__(self, screen, filename, height=30):
        """
        :param screen: The screen to use when displaying the image.
        :param filename: The name of the file to render.
        :param height: The height of the text rendered image.
        """
        super(ColourImageFile, self).__init__()
        image = Image.open(filename)

        # Find any PNG or GIF background colour.
        background = None
        if 'background' in image.info:
            background = image.info['background']
        elif 'transparency' in image.info:
            background = image.info['transparency']

        # Convert each frame in the image.
        for frame in _ImageSequence(image):
            ascii_image = ""
            frame = frame.resize(
                (int(frame.size[0] * height * 2.0 / frame.size[1]), height),
                Image.BICUBIC)
            tmp_img = Image.new("P", (1, 1))
            tmp_img.putpalette(screen._256_palette)

            # Avoid dithering - this requires a little hack to get directly
            # at the underlying library in PIL.
            new_frame = frame.convert('RGB')
            tmp_img.load()
            new_frame.load()
            new_frame = new_frame._new(new_frame.im.convert("P", 0, tmp_img.im))

            # Blank out any transparent sections of the image for complex
            # images with alpha blending.
            if background is None and frame.mode == 'RGBA':
                mask = Image.eval(frame.split()[-1], lambda a: 255 if a <= 64
                                  else 0)
                new_frame.paste(16, mask)

            # Convert the resulting image to coloured ASCII codes.
            for py in range(0, new_frame.size[1]):
                ascii_image += "\n"
                for px in range(0, new_frame.size[0]):
                    real_col = frame.getpixel((px, py))
                    col = new_frame.getpixel((px, py))
                    if real_col == background or col == 16:
                        ascii_image += " "
                    else:
                        ascii_image += "${%d}#" % col
            self._images.append(ascii_image)


class SpeechBubble(Renderer):
    """
    Renders supplied text into a speech bubble.
    """

    def __init__(self, text, tail=None):
        """
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
        :param width: The desired width of the box.
        :param height: The desired height of the box.
        """
        super(Box, self).__init__()
        box = "+" + "-" * (width-2) + "+\n"
        for line in range(height-2):
            box += "|" + " " * (width-2) + "|\n"
        box += "+" + "-" * (width-2) + "+\n"
        self._images = [box]


class Rainbow(Renderer):
    """
    Chained renderer to add rainbow colours to output of another renderer.
    """

    # Colour palette when limited to 16 colours (8 dim and 8 bright).
    _16_palette = [1, 3, 2, 6, 4, 5]

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
        super(Rainbow, self).__init__()
        palette = self._256_palette if screen.colours > 16 else self._16_palette
        for image in renderer._images:
            new_image = ""
            x = y = 0
            for c in image:
                colour = (x + y) % len(palette)
                new_image += '${%d,1}%s' % (palette[colour], c)
                if c == '\n':
                    x = 0
                    y += 1
                else:
                    x += 1
            self._images.append(new_image)
