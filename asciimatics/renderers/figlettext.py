# -*- coding: utf-8 -*-
"""
This module implements Figlet text renderer.
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from pyfiglet import Figlet, DEFAULT_FONT

from asciimatics.renderers.base import StaticRenderer


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
