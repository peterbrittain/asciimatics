# -*- coding: utf-8 -*-
"This module implements an ASCII box renderer."
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from asciimatics.constants import SINGLE_LINE
from asciimatics.renderers.base import StaticRenderer
from asciimatics.utilities import BoxTool

class Box(StaticRenderer):
    """
    Renders a simple box using ASCII characters.  This does not render in
    extended box drawing characters as that requires non-ASCII characters in
    Windows and direct access to curses in Linux.
    """

    def __init__(self, width, height, uni=False, style=SINGLE_LINE):
        """
        :param width: width of box
        :param height: height of box
        :param uni: True to use UNICODE character set, defaults to False
        :param style: desired line style, based on line style definitions in
            :mod:`~asciimatics.constants`: `ASCII_LINE`, `SINGLE_LINE`,
            `DOUBLE_LINE`. `uni` parameter takes precedence and the style will be
            ignored if `uni==False`
        """
        super(Box, self).__init__()
        self._images = [BoxTool(uni, style).box(width, height)]
