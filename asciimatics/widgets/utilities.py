"""This module defines commonly used pieces for widgets"""
from __future__ import annotations
from logging import getLogger
from math import sqrt
from collections import defaultdict
from functools import lru_cache
from typing import TYPE_CHECKING, List, Tuple, Optional, Union
from wcwidth import wcswidth, iter_graphemes, wrap as wcwidth_wrap
from asciimatics.screen import Screen
if TYPE_CHECKING:
    from asciimatics.widgets.widget import Widget
    from asciimatics.strings import ColouredText

# Logging
logger = getLogger(__name__)

#: Standard palettes for use with :py:meth:`~Frame.set_theme`.
#: Each entry in THEMES contains a colour palette for use by the widgets within a Frame.
#: Each colour palette is a dictionary mapping a colour key to a 3-tuple of
#: (foreground colour, attribute, background colour).
#: The "default" theme defines all the required keys for a palette.
THEMES: dict[str, dict[str, tuple[Optional[int], Optional[int], Optional[int]]]] = {
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
        "selected_control": (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "focus_control": (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "selected_focus_control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_CYAN),
        "field": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
        "selected_field": (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLUE),
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
        }),
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
        }),
    "bright": defaultdict(
        lambda: (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK),
        {
            "invalid": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_RED),
            "label": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_focus_control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "selected_focus_field": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_button": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "focus_edit_text": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLACK),
            "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLACK),
        }),
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
        }),
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
        }),
}


def _enforce_width(text: Union[str, ColouredText],
                   width: int,
                   unicode_aware: bool = True,
                   split_on_words: bool = False) -> Union[str, ColouredText]:
    """
    Enforce a displayed piece of text to be a certain number of cells wide.  This takes into
    account double-width characters used in CJK languages.

    :param text: The text to be truncated
    :param width: The screen cell width to enforce
    :param unicode_aware: Whether the text needs unicode-aware handling.
    :param split_on_words: Whether to respect word boundaries when splitting.
    :return: The resulting truncated text
    """
    return _enforce_width_ext(
        text, width, unicode_aware=unicode_aware, split_on_words=split_on_words)[0]


def _enforce_width_ext(text: Union[str, ColouredText],
                       width: int,
                       unicode_aware: bool = True,
                       split_on_words: bool = False) -> Tuple[Union[str, ColouredText], bool]:
    """
    Enforce a displayed piece of text to be a certain number of cells wide.  This takes into
    account double-width characters used in CJK languages and grapheme clusters.

    :param text: The text to be truncated
    :param width: The screen cell width to enforce
    :param unicode_aware: Whether the text needs unicode-aware handling.
    :param split_on_words: Whether to respect word boundaries when splitting.
    :return: Tuple of the resulting new text and whether it was truncated.
    """
    # Double-width strings cannot be more than twice the string length, so no need to try
    # expensive truncation if this upper bound isn't an issue.
    if (2 * len(text) < width) or (len(text) < width and not unicode_aware):
        return text, False

    # Can still optimize performance if we are not handling unicode characters.
    if unicode_aware or split_on_words:
        size = 0
        pos = 0
        last_space_pos = 9999999999
        text_str = str(text)
        for grapheme in iter_graphemes(text_str):
            g_width = wcswidth(grapheme)
            if split_on_words and grapheme in (" ", "\t"):
                last_space_pos = pos + len(grapheme)
            if size + g_width > width:
                return text[0:min(pos, last_space_pos)], True
            size += g_width
            pos += len(grapheme)
    elif len(text) + 1 > width:
        return text[0:width], True
    return text, False


def _find_min_start(text: str, max_width: int, unicode_aware: bool = True,
                    at_end: bool = False) -> int:
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

    # OK - do it the hard way, iterating by grapheme cluster to avoid splitting them...
    result = 0
    if unicode_aware:
        display_end = wcswidth(text)
        for grapheme in iter_graphemes(text):
            if display_end <= max_width:
                break
            display_end -= wcswidth(grapheme)
            result += len(grapheme)
    else:
        display_end = len(text)
        while display_end > max_width:
            result += 1
            display_end -= 1
    if at_end and display_end == max_width:
        result += len(next(iter_graphemes(text[result:]), "")) if unicode_aware else 1
    return result


def _get_offset(text: str, visible_width: int, unicode_aware: bool = True) -> int:
    """
    Find the character offset within some text for a given visible offset (taking into account the
    fact that some character glyphs are double width and grapheme clusters).

    :param text: The text to analyze
    :param visible_width: The required location within that text (as seen on screen).
    :return: The offset within text (as a character offset within the string).
    """
    result = 0
    width = 0
    if unicode_aware:
        for grapheme in iter_graphemes(text):
            g_width = wcswidth(grapheme)
            if width + g_width > visible_width:
                break
            result += len(grapheme)
            width += g_width
    else:
        result = min(len(text), visible_width)
    return result


@lru_cache(256)
def _split_text(text: str, width: int, height: int, unicode_aware: bool = True) -> List[str]:
    """
    Split text to required dimensions.

    This will first try to split the text into multiple lines, then put a "..." on the last
    3 characters of the last line if this still doesn't fit.

    :param text: The text to split.
    :param width: The maximum width for any line.
    :param height: The maximum height for the resulting text.
    :return: A list of strings of the broken up text.
    """
    string_len = wcswidth if unicode_aware else len

    if unicode_aware:
        # Use wcwidth.wrap() for grapheme, east-asian, emoji, and terminal sequence-aware word
        # wrapping, modeled after standard python textwrap.wrap().  We split on newlines first to
        # preserve newlines, as documented at bottom of API document of wcwidth.wrap(), its what
        # most people prefer, like the html classic '<br><br><br>' sometimes you want them.
        result = []
        for paragraph in text.split("\n"):
            if paragraph:
                result.extend(wcwidth_wrap(paragraph, width, break_long_words=True))
            else:
                result.append("")
    else:
        # Legacy non-unicode path
        tokens = text.split(" ")
        result = []
        current_line = ""
        for token in tokens:
            for i, line_token in enumerate(token.split("\n")):
                if len(current_line + line_token) > width or i > 0:
                    if len(current_line) > 0:
                        result.append(current_line.rstrip())
                    current_line = line_token + " "
                else:
                    current_line += line_token + " "
        current_line = current_line.rstrip()
        while len(current_line) > 0:
            new_line = current_line[:width]
            result.append(new_line)
            current_line = current_line[len(new_line):]

    # Check for a height overrun and truncate with ellipsis.
    if len(result) > height:
        result = result[:height]
        last_line = result[height - 1]
        truncated = _enforce_width(last_line, width - 3, unicode_aware)
        result[height - 1] = str(truncated) + "..."

    # Very small columns could be shorter than individual words - truncate
    # each line if necessary.
    for i, line in enumerate(result):
        if string_len(line) > width:
            truncated = _enforce_width(line, width - 3, unicode_aware)
            result[i] = str(truncated) + "..."
    return result


def _euclidian_distance(widget1: Widget, widget2: Widget) -> float:
    """
    Find the Euclidian distance between 2 widgets.

    :param widget1: first widget
    :param widget2: second widget
    """
    point1 = widget1.get_location()
    point2 = widget2.get_location()
    return sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
