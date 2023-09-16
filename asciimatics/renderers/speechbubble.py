"""
This module implements a speech-bubble effect renderer.
"""
from wcwidth.wcwidth import wcswidth

from asciimatics.renderers.base import StaticRenderer


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
        super().__init__()
        max_len = max(wcswidth(x) for x in text.split("\n"))
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
