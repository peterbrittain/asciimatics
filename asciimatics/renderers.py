# -*- coding: utf-8 -*-
"""
This module provides `Renderers` to create complex animation effects.  For more details see
http://asciimatics.readthedocs.io/en/latest/rendering.html
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from builtins import object
from builtins import range
import copy
from random import randint, random
from future.utils import with_metaclass
from abc import ABCMeta, abstractproperty, abstractmethod
from math import sin, cos, pi, sqrt, atan2
from pyfiglet import Figlet, DEFAULT_FONT
from PIL import Image
import re
import json

from wcwidth.wcwidth import wcswidth

from asciimatics.screen import Screen, TemporaryCanvas
from asciimatics.constants import COLOUR_REGEX
from asciimatics.parsers import AnsiTerminalParser, Parser
from asciimatics.utilities import BoxTool

import logging
from logging import getLogger
logging.basicConfig(filename="vbars.log", level=logging.DEBUG)
logger = getLogger(__name__)


#: Attribute conversion table for the ${c,a} form of attributes for
#: :py:obj:`~.Screen.paint`.
ATTRIBUTES = {
    "1": Screen.A_BOLD,
    "2": Screen.A_NORMAL,
    "3": Screen.A_REVERSE,
    "4": Screen.A_UNDERLINE,
}


class Renderer(with_metaclass(ABCMeta, object)):
    """
    A Renderer is simply a class that will return one or more text renderings
    for display by an Effect.

    In the simple case, this can be a single string that contains some
    unchanging content - e.g. a simple text message.

    It can also represent a sequence of strings that can be played one after
    the other to make a simple animation sequence - e.g. a rotating globe.
    """

    @abstractproperty
    def max_width(self):
        """
        :return: The max width of the rendered text (across all images if an animated renderer).
        """

    @abstractproperty
    def rendered_text(self):
        """
        :return: The next image and colour map in the sequence as a tuple.
        """

    @abstractproperty
    def images(self):
        """
        :return: An iterator of all the images in the Renderer.
        """

    @abstractproperty
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
        super(StaticRenderer, self).__init__()
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
                new_max = max([wcswidth(x) for x in image])
                self._max_width = max(new_max, self._max_width)
        return self._max_width


class DynamicRenderer(with_metaclass(ABCMeta, Renderer)):
    """
    A DynamicRenderer is a Renderer that creates each image as requested.  It
    has a defined maximum size on construction.
    """

    def __init__(self, height, width, clear=True):
        """
        :param height: The max height of the rendered image.
        :param width: The max width of the rendered image.
        """
        super(DynamicRenderer, self).__init__()
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

    @property
    def images(self):
        # We can't return all, so just return the latest rendered image.
        return [self.rendered_text[0]]

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


class FigletText(StaticRenderer):
    """
    This class renders the supplied text using the specified Figlet font.
    See http://www.figlet.org/ for details of available fonts.
    """

    def __init__(self, text, font=DEFAULT_FONT, width=200):
        """
        :param text: The text string to convert with Figlet.
        :param font: The Figlet font to use (optional).
        :param width: The maximum width for this text in characters.
        """
        super(FigletText, self).__init__()
        self._images = [Figlet(font=font, width=width).renderText(text)]


class _ImageSequence(object):
    """
    Simple class to make an iterator for a PIL Image object.
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


class ImageFile(StaticRenderer):
    """
    Renderer to convert an image file (as supported by the Python Imaging
    Library) into an ascii grey scale text image.
    """

    # The ASCII grey scale from darkest to lightest.
    _greyscale = ' .:;rsA23hHG#9&@'

    def __init__(self, filename, height=30, colours=8):
        """
        :param filename: The name of the file to render.
        :param height: The height of the text rendered image.
        :param colours: The number of colours the terminal supports.
        """
        super(ImageFile, self).__init__()
        with Image.open(filename) as image:
            background = image.info['background'] if 'background' in \
                image.info else None
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
                            if colours >= 256:
                                ascii_image += "${%d}" % (232 + col * 23 // 256)
                            else:
                                ascii_image += "${%d,%d}" % (
                                    7 if col >= 85 else 0,
                                    Screen.A_BOLD if col < 85 or col > 170 else
                                    Screen.A_NORMAL
                                )
                            ascii_image += self._greyscale[
                                (int(col) * len(self._greyscale)) // 256]
                self._images.append(ascii_image)


class ColourImageFile(StaticRenderer):
    """
    Renderer to convert an image file (as supported by the Python Imaging
    Library) into an block image of available colours.

    .. warning::

        This is only compatible with 256-colour terminals.  Results in other
        terminals with reduced colour capabilities are severely restricted.
        Since Windows only has 8 base colours, it is recommended that you
        avoid this renderer on that platform.
    """

    def __init__(self, screen, filename, height=30, bg=Screen.COLOUR_BLACK,
                 fill_background=False, uni=False, dither=False):
        """
        :param screen: The screen to use when displaying the image.
        :param filename: The name of the file to render.
        :param height: The height of the text rendered image.
        :param bg: The default background colour for this image.
        :param fill_background: Whether to set background colours too.
        :param uni: Whether to use unicode box characters or not.
        :param dither: Whether to dither the rendered image or not.
        """
        super(ColourImageFile, self).__init__()
        with Image.open(filename) as image:
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
                    (int(frame.size[0] * height * 2.0 / frame.size[1]),
                     height * 2 if uni else height),
                    Image.BICUBIC)
                tmp_img = Image.new("P", (1, 1))
                tmp_img.putpalette(screen.palette)

                # Avoid dithering - this requires a little hack to get directly
                # at the underlying library in PIL.
                new_frame = frame.convert('RGB')
                tmp_img.load()
                new_frame.load()
                new_frame = new_frame._new(
                    new_frame.im.convert("P", 3 if dither else 0, tmp_img.im))

                # Blank out any transparent sections of the image for complex
                # images with alpha blending.
                if background is None and frame.mode == 'RGBA':
                    mask = Image.eval(
                        frame.split()[-1], lambda a: 255 if a <= 64 else 0)
                    new_frame.paste(16, mask)

                # Decide what "brush" we're going to use for the rendering.
                brush = "▄" if uni else "#"

                # Convert the resulting image to coloured ASCII codes.
                for py in range(0, new_frame.size[1], 2 if uni else 1):
                    # Looks like some terminals need a character printed before
                    # they really reset the colours - so insert a dummy char
                    # to reset the background if needed.
                    if uni:
                        ascii_image += "${%d,2,%d}." % (bg, bg)
                    ascii_image += "\n"
                    for px in range(0, new_frame.size[0]):
                        real_col = frame.getpixel((px, py))
                        real_col2 = (frame.getpixel((px, py + 1)) if uni else
                                     real_col)
                        col = new_frame.getpixel((px, py))
                        col2 = new_frame.getpixel((px, py + 1)) if uni else col
                        if ((real_col == real_col2 == background) or
                                (col == col2 == 16)):
                            if fill_background or uni:
                                ascii_image += "${%d,2,%d}." % (bg, bg)
                            else:
                                ascii_image += "${%d} " % bg
                        else:
                            if fill_background or uni:
                                ascii_image += "${%d,2,%d}%s" % (col2, col,
                                                                 brush)
                            else:
                                ascii_image += "${%d}#" % col
                if uni:
                    ascii_image += "${%d,2,%d}." % (bg, bg)
                self._images.append(ascii_image)


class SpeechBubble(StaticRenderer):
    """
    Renders supplied text into a speech bubble.
    """

    def __init__(self, text, tail=None, uni=False):
        """
        :param text: The text to be put into a speech bubble.
        :param tail: Where to put the bubble callout tail, specifying "L" or
                     "R" for left or right tails.  Can be None for no tail.
        """
        super(SpeechBubble, self).__init__()
        max_len = max([wcswidth(x) for x in text.split("\n")])
        if uni:
            bubble = "╭─" + "─" * max_len + "─╮\n"
            for line in text.split("\n"):
                filler = " " * (max_len - len(line))
                bubble += "│ " + line + filler + " │\n"
            bubble += "╰─" + "─" * max_len + "─╯"
        else:
            bubble = ".-" + "-" * max_len + "-.\n"
            for line in text.split("\n"):
                filler = " " * (max_len - len(line))
                bubble += "| " + line + filler + " |\n"
            bubble += "`-" + "-" * max_len + "-`"
        if tail == "L":
            bubble += "\n"
            bubble += "  )/  \n"
            bubble += "-\"`\n"
        elif tail == "R":
            bubble += "\n"
            bubble += (" " * max_len) + "\\(  \n"
            bubble += (" " * max_len) + " `\"-\n"
        self._images = [bubble]


class Box(StaticRenderer):
    """
    Renders a simple box using ASCII characters.  This does not render in
    extended box drawing characters as that requires non-ASCII characters in
    Windows and direct access to curses in Linux.
    """

    def __init__(self, width, height, uni=False):
        """
        :param width: The desired width of the box.
        :param height: The desired height of the box.
        :param uni: Whether to use unicode box characters or not.
        """
        super(Box, self).__init__()
        if uni:
            box = u"┌" + u"─" * (width - 2) + u"┐\n"
            for _ in range(height - 2):
                box += u"│" + u" " * (width - 2) + u"│\n"
            box += u"└" + u"─" * (width - 2) + u"┘\n"
        else:
            box = "+" + "-" * (width - 2) + "+\n"
            for _ in range(height - 2):
                box += "|" + " " * (width - 2) + "|\n"
            box += "+" + "-" * (width - 2) + "+\n"
        self._images = [box]


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
        super(Rainbow, self).__init__()
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


# --- Bar Chart Renders

class _BarChartBase(DynamicRenderer): 
    #: Constant to indicate no axes should be rendered.
    NONE = 0

    #: Constant to indicate just the x axis should be rendered.
    X_AXIS = 1

    #: Constant to indicate just the y axis should be rendered.
    Y_AXIS = 2

    #: Constant to indicate both axes should be rendered.
    BOTH = 3

    def __init__(self, height, width, functions, char="#", colour=Screen.COLOUR_GREEN, 
                 bg=Screen.COLOUR_BLACK, gradient=None, scale=None, axes=Y_AXIS, intervals=None,
                 labels=False, border=True, keys=None, gap=None):
        """
        :param height: The max height of the rendered image.
        :param width: The max width of the rendered image.
        :param functions: List of functions to chart.
        :param char: Character to use for the bar.
        :param colour: Default colour to use for the bars.  This can be a
            single value or list of values (to cycle around for each bar).
        :param bg: Default background colour to use for the bars.  This can be a
            single value or list of values (to cycle around for each bar).
        :param gradient: Colour gradient for use on all bars.  This is a list of
            tuple pairs specifying a threshold and a colour, or triplets to
            include a background colour too.
        :param scale: Maximum value for the bars.  This is used to scale the
            function values to the maximum space available.  Any value over this
            will be truncated when drawn.  Defaults to the number of available
            characters in the chart.
        :param axes: Which axes to draw.
        :param intervals: Units for interval markers on the main axis.
            Defaults to none.
        :param labels: Whether to label the main axis.
        :param border: Whether to draw a border around the chart.
        :param keys: Optional keys for each bar.
        :param gap: distance between bars. A value of None will auto-calculate (default).
        """
        super(_BarChartBase, self).__init__(height, width)
        self._functions = functions
        self._char = char
        self._colours = [colour] if isinstance(colour, int) else colour
        self._bgs = [bg] if isinstance(bg, int) else bg
        self._scale = scale
        self._axes = axes
        self._intervals = intervals
        self._labels = labels
        self._border = border
        self._keys = keys
        self._gap = gap

        # Box drawing tool for border, allows user to change the border line style 
        self._border_lines = BoxTool(self._canvas.unicode_aware, BoxTool.MIXED_LINE) if border \
            else None

        # Box drawing tool for axes
        self._axes_lines = BoxTool(self._canvas.unicode_aware, BoxTool.SINGLE_LINE)

        # Normalize the gradient so that it is 3-tuple wide (bg is optional, if not there, set it)
        self._gradient = None
        if gradient:
            self._gradient = []
            for item in gradient:
                if len(item) == 2:
                    self._gradient.append( (item[0], item[1], Screen.COLOUR_BLACK) )
                elif len(item) == 3:
                    self._gradient.append(item)
                else:
                    raise ValueError("Gradients must be 2-tuple or 3-tuple in size")

    @property
    def border_lines(self):
        """If border=True this object will have a reference to a
        :class:`~asciimatics.utilities.BoxTool` instance. The style of the border can be changed
        through it.  Defaults to a double line using a UNICODE box if supported, otherwise ASCII
        characters.
        """
        return self._border_lines

    @property
    def axes_lines(self):
        """If axes are drawn, this object will have a reference to a
        :class:`~asciimatics.utilities.BoxTool` instance. The style of the axes can be changed
        through it. Defaults to a single line using a UNICODE box if supported, otherwise ASCII
        characters.
        """
        return self._axes_lines

    def _setup_chart(self):
        """Draws any borders and returns initial height, width, and starting X and Y."""
        # Dimensions for the chart.
        int_h = self._canvas.height
        int_w = self._canvas.width
        start_x = key_x = 0
        start_y = 0

        # Create  the box around the chart...
        if self._border:
            draw = self._border_lines.box_top(self._canvas.width)
            self._write(draw, 0, 0)
            for line in range(1, self._canvas.height):
                self._write(self._border_lines.v, 0, line)
                self._write(self._border_lines.v, self._canvas.width - 1, line)
            draw = self._border_lines.box_bottom(self._canvas.width)
            self._write(draw, 0, self._canvas.height - 1)
            int_h -= 4
            int_w -= 6
            start_y += 2
            start_x += 3

        return int_h, int_w, start_x, start_y


class BarChart(_BarChartBase): 
    """
    Renderer to create a horizontal bar chart using the specified functions as inputs for each
    entry.  Can be used to chart distributions or for more graphical effect - e.g. to imitate a
    sound equalizer or a progress indicator.
    """
    def _render_now(self):
        int_h, int_w, start_x, start_y = self._setup_chart()

        # Make room for the keys if supplied.
        if self._keys:
            width = max([len(x) for x in self._keys])
            key_x = start_x
            int_w -= width + 1
            start_x += width + 1

        # Now add the axes - resizing chart space as required...
        if (self._axes & BarChart.X_AXIS) > 0:
            int_h -= 1

        if (self._axes & BarChart.Y_AXIS) > 0:
            int_w -= 2
            start_x += 1

        if self._labels:
            int_h -= 1

        # Use given scale or whatever space is left in the grid
        scale = int_w if self._scale is None else self._scale

        if (self._axes & BarChart.X_AXIS) > 0:
            self._write(self._axes_lines.h * int_w, start_x, start_y + int_h)
        if (self._axes & BarChart.Y_AXIS) > 0:
            for line in range(int_h):
                self._write(self._axes_lines.v, start_x - 1, start_y + line)
        if self._labels:
            self._write("0", start_x, start_y + int_h + 1)
            text = str(scale)
            self._write(text, start_x + int_w - len(text), start_y + int_h + 1)

        # Now add any interval markers if required...
        if self._intervals is not None:
            i = self._intervals
            while i < scale:
                x = start_x + int(i * int_w / scale) - 1
                for line in range(int_h):
                    self._write(self._axes_lines.v_inside, x, start_y + line)
                self._write(self._axes_lines.h_up, x, start_y + int_h)
                if self._labels:
                    val = str(i)
                    self._write(val, x - (len(val) // 2), start_y + int_h + 1)
                i += self._intervals

        # Allow double-width bars if there's space.
        bar_size = 2 if int_h >= (3 * len(self._functions)) - 1 else 1

        gap = self._gap
        if self._gap is None:
            gap = 0 if len(self._functions) <= 1 else (int_h - (bar_size * len(
                self._functions))) / (len(self._functions) - 1)

        # Now add the bars...
        for i, fn in enumerate(self._functions):
            bar_len = int(fn() * int_w / scale)
            y = start_y + (i * bar_size) + int(i * gap)

            # First draw the key if supplied
            if self._keys:
                self._write(self._keys[i], key_x, y)

            # Now draw the bar
            colour = self._colours[i % len(self._colours)]
            bg = self._bgs[i % len(self._bgs)]
            if self._gradient:
                # Colour gradient required - break down into chunks for each
                # color.
                last = 0
                size = 0
                for threshold, colour, bg in self._gradient:
                    value = int(threshold * int_w / scale)
                    if value - last > 0:
                        # Size to fit the available space
                        size = value if bar_len >= value else bar_len
                        if size > int_w:
                            size = int_w
                        for line in range(bar_size):
                            self._write(
                                self._char * (size - last),
                                start_x + last,
                                y + line,
                                colour,
                                bg=bg)

                    # Stop if we reached the end of the line or the chart
                    if bar_len < value or size >= int_w:
                        break
                    last = value
            else:
                # Solid colour - just write the whole block out.
                for line in range(bar_size):
                    self._write(
                        self._char * bar_len, start_x, y + line, colour, bg=bg)

        return self._plain_image, self._colour_map


class VBarChart(_BarChartBase): 
    """
    Renderer to create a vertical bar chart using the specified functions as inputs for each
    entry.  Can be used to chart distributions or for more graphical effect - e.g. to imitate a
    sound equalizer or a progress indicator.
    """
    def _render_now(self):
        int_h, int_w, start_x, start_y = self._setup_chart()

        # Make room for the keys if supplied.
        if self._keys:
            int_h -= 1

        # Now add the axes - resizing chart space as required...
        if (self._axes & VBarChart.X_AXIS) > 0:
            int_h -= 1

        if (self._axes & VBarChart.Y_AXIS) > 0:
            int_w -= 2
            start_x += 1

        # Use given scale or whatever space is left in the grid
        scale = int_h if self._scale is None else self._scale

        # Calculate labels and intervals, adjust width based on widest label
        if self._labels:
            labels = ['' for x in range(int_h)]
            labels[0] = '0'
            labels[-1] = str(scale)

            if self._intervals:
                num_intervals = int(scale / self._intervals)  # must use int(), can't // on float
                skip = int_h // num_intervals

                i = skip
                value = self._intervals
                while value < scale:
                    labels[i] = str(value)
                    value += self._intervals
                    i += skip

            # Change size based on 
            widest_label = max([len(x) for x in labels])
            int_w -= widest_label + 1
            start_x += widest_label + 1

        if (self._axes & VBarChart.X_AXIS) > 0:
            self._write(self._axes_lines.h * int_w, start_x, start_y + int_h)
        if (self._axes & VBarChart.Y_AXIS) > 0:
            for line in range(int_h):
                self._write(self._axes_lines.v, start_x - 1, start_y + line)

        # Draw labels
        if self._labels:
            y = start_y + int_h - 1

            for count, label in enumerate(labels):
                x = start_x - len(label) - 1

                if label != '':
                    self._write(label, x, y)

                y -= 1

        # Draw interval markers
        if self._intervals:
            num_intervals = int(scale / self._intervals)
            skip = int_h // num_intervals

            value = self._intervals
            y = start_y + int_h - 1
            while value < scale:
                y -= skip
                self._write(self._axes_lines.v_right, start_x - 1, y)
                self._write(self._axes_lines.h_inside * int_w, start_x, y)

                value += self._intervals

        # Size bars based on available space
        bar_width = int_w
        gap = 0
        if len(self._functions) > 1:
            if self._gap is None:
                # Evenly size bars and gaps
                bars_and_gaps = 2 * len(self._functions) - 1
                bar_width = int_w // bars_and_gaps
                gap = bar_width
                total_gap_space = gap * (len(self._functions) - 1)
            else:
                # Use given gap size, calculate bar width
                gap = self._gap
                total_gap_space = gap * (len(self._functions) - 1)
                total_bar_space = int_w - total_gap_space
                bar_width = total_bar_space // len(self._functions) 

        if bar_width <= 0:
            raise ValueError("Not enough space to graph bars. " +
                "%s bars + %s space for gaps is > your graph width of %s" % (
                len(self._functions), total_gap_space, int_w))

        # Write keys
        if self._keys:
            x = start_x
            for key in self._keys:
                self._write(key, x, start_y + int_h + 1)
                x += bar_width + gap

        # Write bars
        values = [fn() for fn in self._functions]
        y = start_y + int_h - 1
        scale_factor = scale / int_h

        for pos in range(1, int_h + 1):
            x = start_x
            threshold = pos * scale_factor - (scale_factor / 2)

            for index, value in enumerate(values):
                colour = self._colours[index % len(self._colours)]
                bg = self._bgs[index % len(self._bgs)]
                if value >= threshold:
                    if self._gradient:
                        # First gradient is the base colour
                        draw_colour = self._gradient[0][1]
                        draw_bg = self._gradient[0][2]

                        # Loop through gradients to see if the colour should
                        # be incremented to next value
                        pos_value = scale * (pos / int_h)
                        for gradient in self._gradient[1:]:
                            if pos_value >= gradient[0]:
                                draw_colour = gradient[1]
                                draw_bg = gradient[2]
                            else:
                                break
                    else:
                        draw_colour = colour
                        draw_bg = bg

                    # Uncomment for debug: show value instead of drawing char
                    #self._char = str(pos)[-1]

                    self._write(self._char * bar_width, x, y, draw_colour, bg=draw_bg)

                x += bar_width + gap

            y -= 1

        return self._plain_image, self._colour_map



class Fire(DynamicRenderer):
    """
    Renderer to create a fire effect based on a specified `emitter` that
    defines the heat source.

    The implementation here uses the same techniques described in
    http://freespace.virgin.net/hugo.elias/models/m_fire.htm, although a
    slightly different implementation.
    """

    _COLOURS_16 = [
        (Screen.COLOUR_RED, 0),
        (Screen.COLOUR_RED, 0),
        (Screen.COLOUR_RED, 0),
        (Screen.COLOUR_RED, 0),
        (Screen.COLOUR_RED, 0),
        (Screen.COLOUR_RED, 0),
        (Screen.COLOUR_RED, 0),
        (Screen.COLOUR_RED, Screen.A_BOLD),
        (Screen.COLOUR_RED, Screen.A_BOLD),
        (Screen.COLOUR_RED, Screen.A_BOLD),
        (Screen.COLOUR_RED, Screen.A_BOLD),
        (Screen.COLOUR_YELLOW, Screen.A_BOLD),
        (Screen.COLOUR_YELLOW, Screen.A_BOLD),
        (Screen.COLOUR_YELLOW, Screen.A_BOLD),
        (Screen.COLOUR_YELLOW, Screen.A_BOLD),
        (Screen.COLOUR_WHITE, Screen.A_BOLD),
    ]

    _COLOURS_256 = [
        (0, 0),
        (52, 0),
        (88, 0),
        (124, 0),
        (160, 0),
        (196, 0),
        (202, 0),
        (208, 0),
        (214, 0),
        (220, 0),
        (226, 0),
        (227, 0),
        (228, 0),
        (229, 0),
        (230, 0),
        (231, 0),
    ]

    _CHARS = " ...::$$$&&&@@"

    def __init__(self, height, width, emitter, intensity, spot, colours,
                 bg=False):
        """
        :param height: Height of the box to contain the flames.
        :param width: Width of the box to contain the flames.
        :param emitter: Heat source for the flames.  Any non-whitespace
            character is treated as part of the heat source.
        :param intensity: The strength of the flames.  The bigger the number,
            the hotter the fire.  0 <= intensity <= 1.0.
        :param spot: Heat of each spot source.  Must be an integer > 0.
        :param colours: Number of colours the screen supports.
        :param bg: (Optional) Whether to render background colours only.
        """
        super(Fire, self).__init__(height, width)
        self._emitter = emitter
        self._intensity = intensity
        self._spot_heat = spot
        self._count = len([c for c in emitter if c not in " \n"])
        line = [0 for _ in range(self._canvas.width)]
        self._buffer = [copy.deepcopy(line) for _ in range(self._canvas.width * 2)]
        self._colours = self._COLOURS_256 if colours >= 256 else \
            self._COLOURS_16
        self._bg_too = bg

        # Figure out offset of emitter to centre at the bottom of the buffer
        e_width = 0
        e_height = 0
        for line in self._emitter.split("\n"):
            e_width = max(e_width, len(line))
            e_height += 1
        self._x = (width - e_width) // 2
        self._y = height - e_height

    def _render_now(self):
        # First make the fire rise with convection
        for y in range(len(self._buffer) - 1):
            self._buffer[y] = self._buffer[y + 1]
        self._buffer[len(self._buffer) - 1] = [0 for _ in range(self._canvas.width)]

        # Seed new hot spots
        x = self._x
        y = self._y
        for c in self._emitter:
            if c not in " \n" and random() < self._intensity:
                self._buffer[y][x] += randint(1, self._spot_heat)
            if c == "\n":
                x = self._x
                y += 1
            else:
                x += 1

        # Seed a few cooler spots
        for _ in range(self._canvas.width // 2):
            self._buffer[randint(0, self._canvas.height - 1)][
                randint(0, self._canvas.width - 1)] -= 10

        # Simulate cooling effect of the resulting environment.
        for y in range(len(self._buffer)):
            for x in range(self._canvas.width):
                new_val = self._buffer[y][x]
                if y < len(self._buffer) - 1:
                    new_val += self._buffer[y + 1][x]
                    if x > 0:
                        new_val += self._buffer[y][x - 1]
                    if x < self._canvas.width - 1:
                        new_val += self._buffer[y][x + 1]
                self._buffer[y][x] = new_val // 4

        # Now build the rendered text from the simulated flames.
        self._clear()
        for x in range(self._canvas.width):
            for y in range(len(self._buffer)):
                if self._buffer[y][x] > 0:
                    colour = self._colours[min(len(self._colours) - 1,
                                               self._buffer[y][x])]
                    if self._bg_too:
                        char = " "
                        bg = colour[0]
                    else:
                        char = self._CHARS[min(len(self._CHARS) - 1,
                                           self._buffer[y][x])]
                        bg = 0
                    self._write(char, x, y, colour[0], colour[1], bg)

        return self._plain_image, self._colour_map


class Plasma(DynamicRenderer):
    """
    Renderer to create a "plasma" effect using sinusoidal functions.

    The implementation here uses the same techniques described in
    http://lodev.org/cgtutor/plasma.html
    """

    # The ASCII grey scale from darkest to lightest.
    _greyscale = ' .:;rsA23hHG#9&@'

    # Colours for different environments
    _palette_8 = [
        (Screen.COLOUR_BLUE, Screen.A_NORMAL),
        (Screen.COLOUR_BLUE, Screen.A_NORMAL),
        (Screen.COLOUR_MAGENTA, Screen.A_NORMAL),
        (Screen.COLOUR_MAGENTA, Screen.A_NORMAL),
        (Screen.COLOUR_RED, Screen.A_NORMAL),
        (Screen.COLOUR_RED, Screen.A_BOLD),
    ]
    _palette_256 = [
        (18, 0),
        (19, 0),
        (20, 0),
        (21, 0),
        (57, 0),
        (93, 0),
        (129, 0),
        (201, 0),
        (200, 0),
        (199, 0),
        (198, 0),
        (197, 0),
        (196, 0),
        (196, 0),
        (196, 0),
    ]

    def __init__(self, height, width, colours):
        """
        :param height: Height of the box to contain the plasma.
        :param width: Width of the box to contain the plasma.
        :param colours: Number of colours the screen supports.
        """
        super(Plasma, self).__init__(height, width)
        self._palette = self._palette_256 if colours >= 256 else self._palette_8
        self._t = 0

    def _render_now(self):
        # Internal function for creating a sine wave radiating out from a point
        def f(x1, y1, xp, yp, n):
            return sin(sqrt((x1 - self._canvas.width * xp) ** 2 +
                            4 * ((y1 - self._canvas.height * yp) ** 2)) * pi / n)

        self._t += 1
        for y in range(self._canvas.height - 1):
            for x in range(self._canvas.width - 1):
                value = abs(f(x + self._t / 3, y, 1 / 4, 1 / 3, 15) +
                            f(x, y, 1 / 8, 1 / 5, 11) +
                            f(x, y + self._t / 3, 1 / 2, 1 / 5, 13) +
                            f(x, y, 3 / 4, 4 / 5, 13)) / 4.0
                fg, attr = self._palette[
                    int(round(value * (len(self._palette) - 1)))]
                char = self._greyscale[int((len(self._greyscale) - 1) * value)]
                self._write(char, x, y, fg, attr, 0)

        return self._plain_image, self._colour_map


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
        super(RotatedDuplicate, self).__init__()
        for image in renderer.images:
            mx = (width - max([len(x) for x in image])) // 2
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
        super(Kaleidoscope, self).__init__(height, width)
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
                ox = (dx - self._canvas.width / 4)
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


class AbstractScreenPlayer(DynamicRenderer):
    """
    Abstract renderer to play terminal text with support for ANSI control codes.
    """

    def __init__(self, height, width):
        """
        :param height: required height of the renderer.
        :param width: required width of the renderer.
        """
        super(AbstractScreenPlayer, self).__init__(height, width, clear=False)
        self._parser = AnsiTerminalParser()
        self._current_colours = [Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK]
        self._show_cursor = False
        self._cursor_x = 0
        self._cursor_y = 0
        self._save_cursor_x = 0
        self._save_cursor_y = 0
        self._counter = 0
        self._next = 0
        self._buffer = None
        self._parser.reset("", self._current_colours)
        self._clear()

    def _play_content(self, text):
        """
        Process new raw text.

        :param text: thebraw text to be processed.
        """
        lines = text.split("\n")
        for i, line in enumerate(lines):
            self._parser.append(line)
            for _, command, params in self._parser.parse():
                # logging.debug("Command: {} {}".format(command, params))
                if command == Parser.DISPLAY_TEXT:
                    # Just display the text...  allowing for line wrapping.
                    if self._cursor_x + len(params) >= self._canvas.width:
                        part_1 = params[:self._canvas.width - self._cursor_x]
                        part_2 = params[self._canvas.width - self._cursor_x:]
                        self._print_at(part_1, self._cursor_x, self._cursor_y)
                        self._print_at(part_2, 0, self._cursor_y + 1)
                        self._cursor_x = len(part_2)
                        self._cursor_y += 1
                        if self._cursor_y - self._canvas.start_line >= self._canvas.height:
                            self._canvas.scroll()
                    else:
                        self._print_at(params, self._cursor_x, self._cursor_y)
                        self._cursor_x += len(params)
                elif command == Parser.CHANGE_COLOURS:
                    # Change current text colours.
                    self._current_colours = params
                elif command == Parser.NEXT_TAB:
                    # Move to next tab stop - hard-coded to default of 8 characters.
                    self._cursor_x = (self._cursor_x // 8) * 8 + 8
                elif command == Parser.MOVE_RELATIVE:
                    # Move cursor relative to current position.
                    self._cursor_x += params[0]
                    self._cursor_y += params[1]
                    if self._cursor_y < self._canvas.start_line:
                        self._canvas.scroll(self._cursor_y - self._canvas.start_line)
                elif command == Parser.MOVE_ABSOLUTE:
                    # Move cursor relative to specified absolute position.
                    if params[0] is not None:
                        self._cursor_x = params[0]
                    if params[1] is not None:
                        self._cursor_y = params[1] + self._canvas.start_line
                elif command == Parser.DELETE_LINE:
                    # Delete some/all of the current line.
                    if params == 0:
                        self._print_at(
                            " " * (self._canvas.width - self._cursor_x), self._cursor_x, self._cursor_y)
                    elif params == 1:
                        self._print_at(" " * self._cursor_x, 0, self._cursor_y)
                    elif params == 2:
                        self._print_at(" " * self._canvas.width, 0, self._cursor_y)
                elif command == Parser.DELETE_CHARS:
                    # Delete n characters under the cursor.
                    for x in range(self._cursor_x, self._canvas.width):
                        if x + params < self._canvas.width:
                            cell = self._canvas.get_from(x + params, self._cursor_y)
                        else:
                            cell = (ord(" "),
                                    self._current_colours[0],
                                    self._current_colours[1],
                                    self._current_colours[2])
                        self._canvas.print_at(
                            chr(cell[0]), x, self._cursor_y, colour=cell[1], attr=cell[2], bg=cell[3])
                elif command == Parser.SHOW_CURSOR:
                    # Show/hide the cursor.
                    self._show_cursor = params
                elif command == Parser.SAVE_CURSOR:
                    # Save the cursor position.
                    self._save_cursor_x = self._cursor_x
                    self._save_cursor_y = self._cursor_y
                elif command == Parser.RESTORE_CURSOR:
                    # Restore the cursor position.
                    self._cursor_x = self._save_cursor_x
                    self._cursor_y = self._save_cursor_y
                elif command == Parser.CLEAR_SCREEN:
                    # Clear the screen.
                    self._canvas.clear_buffer(
                        self._current_colours[0], self._current_colours[1], self._current_colours[2])
                    self._cursor_x = 0
                    self._cursor_y = self._canvas.start_line
            # Move to next line, scrolling buffer as needed.
            if i != len(lines) - 1:
                self._cursor_x = 0
                self._cursor_y += 1
                if self._cursor_y - self._canvas.start_line >= self._canvas.height:
                    self._canvas.scroll()

    def _print_at(self, text, x, y):
        """
        Helper function to simplify use of the renderer.
        """
        self._canvas.print_at(
            text,
            x, y,
            colour=self._current_colours[0], attr=self._current_colours[1], bg=self._current_colours[2])


class AnsiArtPlayer(AbstractScreenPlayer):
    """
    Renderer to play ANSI art text files.

    In order to tidy up files, this must be used as a context manager (i.e. using `with`).
    """

    def __init__(self, filename, height=25, width=80, encoding="cp437", strip=False, rate=2):
        """
        :param filename: the file containingi the ANSI art.
        :param height: required height of the renderer.
        :param width: required width of the renderer.
        :param encoding: text encoding ofnthe file.
        :param strip: whether to strip CRLF from the file content.
        :param rate: number of lines to render on each update.
        """
        super(AnsiArtPlayer, self).__init__(height, width)
        self._file = open(filename, "rb")
        self._strip = strip
        self._rate = rate
        self._encoding = encoding

    def __enter__(self):
        """
        Create context for use as a context manager.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Clear up the resources for this context.
        """
        if self._file:
            self._file.close()

    def _render_now(self):
        count = 0
        line = None
        while count < self._rate and line != "":
            line = self._file.readline().decode(self._encoding)
            count += 1
            if self._strip:
                line = line.rstrip("\r\n")
            self._play_content(line)
        return self._plain_image, self._colour_map


class AsciinemaPlayer(AbstractScreenPlayer):
    """
    Renderer to play terminal recordings created by asciinema.

    This only supports the version 2 file format.  Use the max_delay setting to speed up human
    interactions (i.e. to reduce delays from typing).

    In order to tidy up files, this must be used as a context manager (i.e. using `with`).
    """

    def __init__(self, filename, height=None, width=None, max_delay=None):
        """
        :param filename: the file containingi the ANSI art.
        :param height: required height of the renderer.
        :param width: required width of the renderer.
        :param max_delay: maximum time interval (in secs) to wait between frame updates.
        """
        # Open the file and check it looks plausibly like a supported format.
        self._file = open(filename)
        header = json.loads(self._file.readline())
        if header["version"] != 2:
            raise RuntimeError("Unsupported file format")

        # Use file details if not overriden by constructor params.
        height = height if height else header["height"]
        width = width if width else header["width"]

        # Construct the full player now we have all the details.
        super(AsciinemaPlayer, self).__init__(height, width)
        self._max_delay = max_delay

    def __enter__(self):
        """
        Create context for use as a context manager.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Clear up the resources for this context.
        """
        if self._file:
            self._file.close()

    def _render_now(self):
        self._counter += 0.05
        if self._counter >= self._next:
            if self._buffer:
                self._play_content(self._buffer)
                self._buffer = None
            while True:
                try:
                    self._next, _, self._buffer = json.loads(self._file.readline())
                    if self._next > self._counter:
                        # Speed up playback if requested.
                        if self._max_delay and self._next - self._counter > self._max_delay:
                            self._counter = self._next - self._max_delay
                        break
                    self._play_content(self._buffer)
                except ValueError:
                    # Python 3 raises a subclass of this error, so will also be caught.
                    break

        return self._plain_image, self._colour_map
