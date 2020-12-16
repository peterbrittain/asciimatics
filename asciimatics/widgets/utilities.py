# -*- coding: utf-8 -*-
"""This module defines commonly used pieces for widgets"""
from logging import getLogger
from math import sqrt
from builtins import str
from collections import defaultdict
from wcwidth import wcswidth, wcwidth
try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache
from asciimatics.screen import Screen

# Logging
logger = getLogger(__name__)

THEMES = {
    "default": {
        "background": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "shadow": (Screen.COLOUR_BLACK, None, Screen.COLOUR_BLACK),
        "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "invalid": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_RED),
        "label": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "borders": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "scroll": (Screen.COLOUR_CYAN, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "title": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "edit_text": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "focus_edit_text": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "readonly": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "focus_readonly": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "button": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "focus_button": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "control": (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "selected_control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "focus_control": (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "selected_focus_control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "field": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "selected_field": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLUE),
        "focus_field": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "selected_focus_field": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
    },
    "monochrome": defaultdict(
        lambda: (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK),
        {
            "invalid": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_RED),
            "label": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "title": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_focus_field": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_edit_text": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_button": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_focus_control": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK),
        }
    ),
    "green": defaultdict(
        lambda: (Screen.COLOUR_GREEN, Screen.A_NORMAL, Screen.COLOUR_BLACK),
        {
            "invalid": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_RED),
            "label": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "title": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_focus_field": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_edit_text": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_button": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_focus_control": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK),
        }
    ),
    "bright": defaultdict(
        lambda: (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
        {
            "invalid": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_RED),
            "label": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_focus_control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_focus_field": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_button": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_edit_text": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK),
        }
    ),
    "tlj256": defaultdict(
        lambda: (16, 0, 15),
        {
            "invalid": (0, 0, 196),
            "label": (88, 0, 15),
            "title": (88, 0, 15),
            "selected_focus_field": (15, 0, 88),
            "focus_edit_text": (15, 0, 88),
            "focus_button": (15, 0, 88),
            "selected_focus_control": (15, 0, 88),
            "disabled": (8, 0, 15),
        }
    ),
    "warning": defaultdict(
        lambda: (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_RED),
        {
            "label": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_RED),
            "title": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_RED),
            "focus_edit_text": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_RED),
            "focus_field": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_RED),
            "focus_button": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_YELLOW),
            "focus_control": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_RED),
            "disabled": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_RED),
            "shadow": (Screen.COLOUR_BLACK, None, Screen.COLOUR_BLACK),
        }
    ),
}
def _enforce_width(text, width, unicode_aware=True):
    """
    Enforce a displayed piece of text to be a certain number of cells wide.  This takes into
    account double-width characters used in CJK languages.

    :param text: The text to be truncated
    :param width: The screen cell width to enforce
    :return: The resulting truncated text
    """
    # Double-width strings cannot be more than twice the string length, so no need to try
    # expensive truncation if this upper bound isn't an issue.
    if (2 * len(text) < width) or (len(text) < width and not unicode_aware):
        return text

    # Can still optimize performance if we are not handling unicode characters.
    if unicode_aware:
        size = 0
        for i, char in enumerate(str(text)):
            c_width = wcwidth(char) if ord(char) >= 256 else 1
            if size + c_width > width:
                return text[0:i]
            size += c_width
    elif len(text) + 1 > width:
        return text[0:width]
    return text


def _find_min_start(text, max_width, unicode_aware=True, at_end=False):
    """
    Find the starting point in the string that will reduce it to be less than or equal to the
    specified width when displayed on screen.

    :param text: The text to analyze.
    :param max_width: The required maximum width
    :param at_end: At the end of the editable line, so allow spaced for cursor.

    :return: The offset within `text` to start at to reduce it to the required length.
    """
    # Is the solution trivial?  Worth optimizing for text heavy UIs...
    if 2 * len(text) < max_width:
        return 0

    # OK - do it the hard way...
    result = 0
    string_len = wcswidth if unicode_aware else len
    char_len = wcwidth if unicode_aware else lambda x: 1
    display_end = string_len(text)
    while display_end > max_width:
        result += 1
        display_end -= char_len(text[0])
        text = text[1:]
    if at_end and display_end == max_width:
        result += 1
    return result


def _get_offset(text, visible_width, unicode_aware=True):
    """
    Find the character offset within some text for a given visible offset (taking into account the
    fact that some character glyphs are double width).

    :param text: The text to analyze
    :param visible_width: The required location within that text (as seen on screen).
    :return: The offset within text (as a character offset within the string).
    """
    result = 0
    width = 0
    if unicode_aware:
        for char in text:
            if visible_width - width <= 0:
                break
            result += 1
            width += wcwidth(char)
        if visible_width - width < 0:
            result -= 1
    else:
        result = min(len(text), visible_width)
    return result


@lru_cache(256)
def _split_text(text, width, height, unicode_aware=True):
    """
    Split text to required dimensions.

    This will first try to split the text into multiple lines, then put a "..." on the last
    3 characters of the last line if this still doesn't fit.

    :param text: The text to split.
    :param width: The maximum width for any line.
    :param height: The maximum height for the resulting text.
    :return: A list of strings of the broken up text.
    """
    # At a high level, just try to split on whitespace for the best results.
    tokens = text.split(" ")
    result = []
    current_line = ""
    string_len = wcswidth if unicode_aware else len
    for token in tokens:
        for i, line_token in enumerate(token.split("\n")):
            if string_len(current_line + line_token) > width or i > 0:
                # Don't bother inserting completely blank lines
                # which should only happen on the very first
                # line (as the rest will inject whitespace/newlines)
                if len(current_line) > 0:
                    result.append(current_line.rstrip())
                current_line = line_token + " "
            else:
                current_line += line_token + " "

    # At this point we've either split nicely or have a hugely long unbroken string
    # (e.g. because the language doesn't use whitespace.
    # Either way, break this last line up as best we can.
    current_line = current_line.rstrip()
    while string_len(current_line) > 0:
        new_line = _enforce_width(current_line, width, unicode_aware)
        result.append(new_line)
        current_line = current_line[len(new_line):]

    # Check for a height overrun and truncate.
    if len(result) > height:
        result = result[:height]
        result[height - 1] = result[height - 1][:width - 3] + "..."

    # Very small columns could be shorter than individual words - truncate
    # each line if necessary.
    for i, line in enumerate(result):
        if len(line) > width:
            result[i] = line[:width - 3] + "..."
    return result


def _euclidian_distance(widget1, widget2):
    """
    Find the Euclidian distance between 2 widgets.

    :param widget1: first widget
    :param widget2: second widget
    """
    point1 = widget1.get_location()
    point2 = widget2.get_location()
    return sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)
