
"""
This module is just a collection of simple helper functions.
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

#: Attribute conversion table for the ${c,a} form of attributes for
#: :py:obj:`~.Screen.paint`.
MAPPING_ATTRIBUTES = {
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
}

#: Regex for asciimatics ${c,a,b} embedded colour attributes.
COLOUR_REGEX = r"^\$\{((\d+),(\d+),(\d+)|(\d+),(\d+)|(\d+))\}(.*)"

# Text attributes for use when printing to the Screen.
A_BOLD = 1
A_NORMAL = 2
A_REVERSE = 3
A_UNDERLINE = 4

# Text colours for use when printing to the Screen.
COLOUR_DEFAULT = -1
COLOUR_BLACK = 0
COLOUR_RED = 1
COLOUR_GREEN = 2
COLOUR_YELLOW = 3
COLOUR_BLUE = 4
COLOUR_MAGENTA = 5
COLOUR_CYAN = 6
COLOUR_WHITE = 7
