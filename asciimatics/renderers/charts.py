# -*- coding: utf-8 -*-
"This module implements bar chart renderers."
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from abc import abstractmethod

from asciimatics.constants import DOUBLE_LINE, SINGLE_LINE
from asciimatics.renderers.base import DynamicRenderer
from asciimatics.screen import Screen
from asciimatics.utilities import BoxTool

#import logging
#logging.basicConfig(filename="debug.log", level=logging.DEBUG)
#logger = logging.getLogger(__name__)

class _BarChartBase(DynamicRenderer):
    #: Constant to indicate no axes should be rendered.
    NONE = 0
    NO_AXIS = 0

    #: Constant to indicate just the x axis should be rendered.
    X_AXIS = 1

    #: Constant to indicate just the y axis should be rendered.
    Y_AXIS = 2

    #: Constant to indicate both axes should be rendered.
    BOTH = 3
    BOTH_AXES = 3

    def __init__(self, height, width, functions, char="#", colour=Screen.COLOUR_GREEN,
                 bg=Screen.COLOUR_BLACK, gradient=None, scale=None, axes=Y_AXIS, intervals=None,
                 labels=False, border=True, keys=None, gap=None):
        ### See children BarChart and VBarChart for argument descriptions and pydocs
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
        self._border_lines = BoxTool(self._canvas.unicode_aware, DOUBLE_LINE) if border else None

        # Box drawing tool for axes
        self._axes_lines = BoxTool(self._canvas.unicode_aware, SINGLE_LINE)

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

    @abstractmethod
    def _render_now(self):
        pass

    @property
    def line_style(self):
        """Returns the current drawing style of the border and axes. Possible values are defined in
        :mod:`~asciimatics.constants`:

        * `ASCII_LINE` -- ASCII safe characters
        * `SINGLE_LINE` -- UNICODE based single line
        * `DOUBLE_LINE` -- UNICODE based double line

        Note that your canvas must support UNICODE style characters to use them

        Single and double-line styles use a single-line axes. The ASCII style uses ASCII for the
        border and the axes.
        """
        return self._border_lines.style

    @line_style.setter
    def line_style(self, style):
        if self._border_lines:
            self._border_lines.style = style

            if style == DOUBLE_LINE:
                self._axes_lines.style = SINGLE_LINE
            else:
                self._axes_lines.style = style

    def _setup_chart(self):
        """Draws any borders and returns initial height, width, and starting X and Y."""
        # Dimensions for the chart.
        int_h = self._canvas.height
        int_w = self._canvas.width
        start_x = 0
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
    def __init__(self, height, width, functions, char="#", colour=Screen.COLOUR_GREEN,
                 bg=Screen.COLOUR_BLACK, gradient=None, scale=None, axes=_BarChartBase.Y_AXIS,
                 intervals=None, labels=False, border=True, keys=None, gap=None):
        """
        :param height: The max height of the rendered image.
        :param width: The max width of the rendered image.
        :param functions: List of functions to chart.
        :param char: Character to use for the bar. Defaults to '#'
        :param colour: Colour(s) to use for the bars.  This can be a single value or list of
            values (to cycle around for each bar). Defaults to green.
        :param bg: Background colour to use for the bars.  This can be a single value or list of
            values (to cycle around for each bar). Defaults to black.
        :param gradient: Colour gradient to use for the bars.  This is a list of tuple pairs
            specifying a threshold and a colour, or triplets to include a background colour too.
            Defaults to no gradients.
        :param scale: Maximum value for the bars.  This is used to scale the function values to
            the maximum space available.  Any value over this will be truncated when drawn.
            Defaults to the number of available characters in the chart.
        :param axes: Which axes to draw.
        :param intervals: Units for interval markers on the main axis. Defaults to none.
        :param labels: Whether to draw size indication labels on the x-axis.
        :param border: Whether to draw a border around the chart.
        :param keys: Optional keys to name each bar on the y-axis.
        :param gap: distance between bars. A value of None will auto-calculate (default).

        If the scale parameter is not specified, the maximum length of the bar is based on the
        available space. A chart with no borders, no axes, no keys or labels will have a bar
        length based solely on the width of the graph.

            * Borders use 4 characters height and 6 characters width
            * Keys use the width of the widest key plus 1
            * Labels use a height of 1
            * An X_AXIS uses a height of 1
            * A Y_AXIS uses a width of 1
        """
        # Have to have a call to super as the defaults for the class are different than the parent
        super(BarChart, self).__init__(height, width, functions, char, colour, bg, gradient,
            scale, axes, intervals, labels, border, keys, gap)

    def _render_now(self):
        int_h, int_w, start_x, start_y = self._setup_chart()

        # Make room for the keys if supplied.
        if self._keys:
            max_key = max([len(x) for x in self._keys])
            key_x = start_x
            int_w -= max_key + 1
            start_x += max_key + 1

        # Now add the axes - resizing chart space as required...
        if (self._axes & BarChart.X_AXIS) > 0:
            int_h -= 1

        if (self._axes & BarChart.Y_AXIS) > 0:
            int_w -= 1
            start_x += 1

        if self._labels:
            int_h -= 1

        # Use given scale or whatever space is left in the grid
        scale = int_w if self._scale is None else self._scale
        #logger.debug('*** int_h=%s int_w=%s scale=%s', int_h, int_w, scale)

        if self._axes & BarChart.X_AXIS:
            self._write(self._axes_lines.h * int_w, start_x, start_y + int_h)
        if self._axes & BarChart.Y_AXIS:
            for line in range(int_h):
                self._write(self._axes_lines.v, start_x - 1, start_y + line)
        if self._axes & BarChart.BOTH == BarChart.BOTH:
            self._write(self._axes_lines.up_right, start_x - 1, start_y + int_h)

        if self._labels:
            pos = start_y + int_h
            if self._axes & BarChart.X_AXIS:
                pos += 1

            self._write("0", start_x, pos)
            text = str(scale)
            self._write(text, start_x + int_w - len(text), pos)

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
                key = self._keys[i]
                pos = max_key - len(key)
                self._write(key, key_x + pos, y)

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

    def __init__(self, height, width, functions, char="#", colour=Screen.COLOUR_GREEN,
                 bg=Screen.COLOUR_BLACK, gradient=None, scale=None, axes=_BarChartBase.X_AXIS,
                 intervals=None, labels=False, border=True, keys=None, gap=None):
        """
        :param height: The max height of the rendered image.
        :param width: The max width of the rendered image.
        :param functions: List of functions to chart.
        :param char: Character to use for the bar. Defaults to '#'
        :param colour: Colour(s) to use for the bars.  This can be a single value or list of
            values (to cycle around for each bar). Defaults to green.
        :param bg: Background colour to use for the bars.  This can be a single value or list of
            values (to cycle around for each bar). Defaults to black.
        :param gradient: Colour gradient to use for the bars.  This is a list of tuple pairs
            specifying a threshold and a colour, or triplets to include a background colour too.
            Defaults to no gradients.
        :param scale: Maximum value for the bars.  This is used to scale the function values to
            the maximum space available.  Any value over this will be truncated when drawn.
            Defaults to the number of available characters in the chart.
        :param axes: Which axes to draw.
        :param intervals: Units for interval markers on the main axis. Defaults to none.
        :param labels: Whether to draw size indication labels on the y-axis.
        :param border: Whether to draw a border around the chart.
        :param keys: Optional keys to name each bar on the x-axis.
        :param gap: distance between bars. A value of None will auto-calculate (default). Minimum
            value when auto-calculated is 1, for no gaps specify 0.

        If the scale parameter is not specified, the maximum length of the bar is based on the
        available space. A chart with no borders, no axes, no keys or labels will have a bar
        height based solely on the width of the graph.

            * Borders use 4 characters height and 6 characters width
            * Keys use a height of 1
            * Labels vertical bar chart use the width of the widest label plus 1 (label values
            depend on the scale of the chart)
            * An X_AXIS uses a height of 1
            * A Y_AXIS uses a width of 1
        """
        super(VBarChart, self).__init__(height, width, functions, char, colour, bg, gradient,
            scale, axes, intervals, labels, border, keys, gap)

        self._precision = 0
        if self._intervals:
            point = str(self._intervals).find('.')
            if point != -1:
                # Interval is a float with a decimal point
                self._precision = len(str(self._intervals)[point + 1:])

    def _render_now(self):
        int_h, int_w, start_x, start_y = self._setup_chart()

        # Make room for the keys if supplied.
        if self._keys:
            int_h -= 1

        # Now add the axes - resizing chart space as required...
        if self._axes & VBarChart.X_AXIS:
            int_h -= 1

        if self._axes & VBarChart.Y_AXIS:
            int_w -= 1
            start_x += 1

        # Use given scale or whatever space is left in the grid
        scale = int_h if self._scale is None else self._scale
        #logger.debug('*** int_h=%s int_w=%s scale=%s', int_h, int_w, scale)

        # Calculate labels and intervals, adjust width based on widest label
        if self._labels:
            labels = ['' for x in range(int_h)]

            labels[0] = '0'
            labels[-1] = str(scale)

            if self._intervals:
                value = 0
                next_interval = self._intervals
                delta = scale / int_h

                for i in range(0, len(labels)):
                    value += delta
                    value = round(value, self._precision)
                    if value >= next_interval:
                        labels[i] = str(next_interval)
                        next_interval += self._intervals

            # Change size based on
            widest_label = max([len(x) for x in labels])
            int_w -= widest_label + 1
            start_x += widest_label + 1

        if self._axes & VBarChart.X_AXIS:
            self._write(self._axes_lines.h * int_w, start_x, start_y + int_h)
        if self._axes & VBarChart.Y_AXIS:
            for line in range(int_h):
                self._write(self._axes_lines.v, start_x - 1, start_y + line)
        if self._axes & VBarChart.BOTH == BarChart.BOTH:
            self._write(self._axes_lines.up_right, start_x - 1, start_y + int_h)

        # Draw labels
        if self._labels:
            y = start_y + int_h - 1

            for label in labels:
                x = start_x - len(label) - 1

                if label != '':
                    self._write(label, x, y)

                y -= 1

        # Draw interval markers
        if self._intervals:
            value = 0
            next_interval = self._intervals
            delta = scale / int_h
            y = start_y + int_h - 1

            for _ in range(int_h):
                value += delta
                value = round(value, self._precision)
                if value >= next_interval:
                    self._write(self._axes_lines.v_right, start_x - 1, y)
                    self._write(self._axes_lines.h_inside * int_w, start_x, y)

                    next_interval += self._intervals

                y -= 1

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
            y = start_y + int_h
            if self._axes & VBarChart.X_AXIS:
                y += 1

            x = start_x
            for key in self._keys:
                self._write(key, x, y)
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
