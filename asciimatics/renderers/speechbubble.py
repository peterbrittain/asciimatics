"""
This module implements a speech-bubble effect renderer.
"""
from typing import Optional, Union
from wcwidth.wcwidth import wcswidth
from asciimatics.renderers.base import StaticRenderer, Renderer


class SpeechBubble(StaticRenderer):
    """
    Renders supplied text into a speech bubble.
    """

    def __init__(self, text: Union[str, Renderer], tail: Optional[str] = None, uni: bool = False):
        """
        :param text: The text to be put into a speech bubble.
        :param tail: Where to put the bubble callout tail, specifying "L" or
                     "R" for left or right tails.  Can be None for no tail.
        :param uni: Whether to use unicode characters or not.
        """
        super().__init__()
        source = text.images if isinstance(text, Renderer) else [text.split("\n")]
        for text_list in source:
            max_len = max(wcswidth(x) for x in text_list)
            if uni:
                bubble = "╭─" + "─" * max_len + "─╮\n"
                for line in text_list:
                    filler = " " * (max_len - len(line))
                    bubble += "│ " + line + filler + " │\n"
                bubble += "╰─" + "─" * max_len + "─╯"
            else:
                bubble = ".-" + "-" * max_len + "-.\n"
                for line in text_list:
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
            self._images.append(bubble)
