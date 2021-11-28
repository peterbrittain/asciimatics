# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import unittest
import os
import sys
from asciimatics.renderers import (StaticRenderer, FigletText, SpeechBubble, Box, Rainbow, Fire, 
    Plasma, Kaleidoscope, RotatedDuplicate, Scale, VScale)
from asciimatics.screen import Screen
if sys.platform != "win32":
    import curses


class TestRendererOthers(unittest.TestCase):
    def test_figlet(self):
        """
        Check that the Figlet renderer works.
        """
        renderer = FigletText("hello")
        self.assertEqual(
            str(renderer),
            " _          _ _       \n" +
            "| |__   ___| | | ___  \n" +
            "| '_ \ / _ \ | |/ _ \ \n" +
            "| | | |  __/ | | (_) |\n" +
            "|_| |_|\___|_|_|\___/ \n" +
            "                      \n")

    def test_bubble(self):
        """
        Check that the SpeechBubble renderer works.
        """
        # Standard rendering.
        renderer = SpeechBubble("hello")
        self.assertEqual(str(renderer),
                         ".-------.\n" +
                         "| hello |\n" +
                         "`-------`")

        # Left bubble.
        renderer = SpeechBubble("world", tail="L")
        self.assertEqual(str(renderer),
                         ".-------.\n" +
                         "| world |\n" +
                         "`-------`\n" +
                         "  )/  \n" +
                         "-\"`\n")

        # Right bubble
        renderer = SpeechBubble("bye!", tail="R")
        self.assertEqual(str(renderer),
                         ".------.\n" +
                         "| bye! |\n" +
                         "`------`\n" +
                         "    \\(  \n" +
                         "     `\"-\n")

        # Unicode rendering.
        renderer = SpeechBubble("hello", uni=True)
        self.assertEqual(str(renderer),
                         u"╭───────╮\n"
                         u"│ hello │\n"
                         u"╰───────╯")

        # Multiline text rendering
        text = "Hello\n" \
               "World! \n" \
               "Hello World!"

        renderer = SpeechBubble(text, uni=True)
        self.assertEqual(str(renderer),
                         "╭──────────────╮\n" +
                         "│ Hello        │\n" +
                         "│ World!       │\n" +
                         "│ Hello World! │\n" +
                         "╰──────────────╯")

        # Test render height
        renderer = SpeechBubble("Hello World", uni=True)
        self.assertEqual(renderer.max_height, 3)

    def test_box(self):
        """
        Check that the Box renderer works.
        """
        renderer = Box(10, 3)
        self.assertEqual(str(renderer),
                         "+--------+\n" +
                         "|        |\n" +
                         "+--------+\n")

        # Unicode rendering.
        renderer = Box(10, 3, uni=True)
        self.assertEqual(str(renderer),
                         "┌────────┐\n" +
                         "│        │\n" +
                         "└────────┘\n")

    def test_rainbow(self):
        """
        Check that the Rainbow renderer works.
        """
        # Skip for non-Windows if the terminal definition is incomplete.
        # This typically means we're running inside a non-standard terminal.
        # For example, this happens when embedded in PyCharm.
        if sys.platform != "win32":
            if not (("FORCE_TTY" in os.environ and os.environ["FORCE_TTY"] == "Y") or sys.stdout.isatty()):
                self.skipTest("Not a valid TTY")
            curses.initscr()
            if curses.tigetstr("ri") is None:
                self.skipTest("No valid terminal definition")

        def internal_checks(screen):
            # Create a base renderer
            plain_text = (".-------.\n" +
                          "| hello |\n" +
                          "`-------`")
            renderer = SpeechBubble("hello")
            self.assertEqual(str(renderer), plain_text)

            # Pretend that we always have an 8 colour palette for the test.
            screen.colours = 8

            # Check that the Rainbow renderer doesn't change this.
            rainbow = Rainbow(screen, renderer)
            self.assertEqual(str(rainbow), plain_text)

            # Check rainbow colour scheme.
            self.assertEqual(
                rainbow.rendered_text[1], [
                    [(1, 1, None), (1, 1, None), (3, 1, None), (3, 1, None), (2, 1, None),
                     (2, 1, None), (6, 1, None), (6, 1, None), (4, 1, None)],
                    [(1, 1, None), (3, 1, None), (3, 1, None), (2, 1, None), (2, 1, None),
                     (6, 1, None), (6, 1, None), (4, 1, None), (4, 1, None)],
                    [(3, 1, None), (3, 1, None), (2, 1, None), (2, 1, None), (6, 1, None),
                     (6, 1, None), (4, 1, None), (4, 1, None), (5, 1, None)]])

        Screen.wrapper(internal_checks, height=15)

    def test_fire(self):
        """
        Check that the Fire renderer works.
        """
        # Allow the fire to burn for a bit...
        renderer = Fire(5, 10, "xxxxxxxx", 1.0, 20, 8)
        output = None
        for _ in range(100):
            output = renderer.rendered_text

        # Output should be something like this, but we can't check exactly due
        # to the random nature of the effect and the difference in RNG between
        # Python2 and Python3.
        #
        #    "  .:...   \n" +
        #    "  .::.    \n" +
        #    " .:$$::.. \n" +
        #    "..::$$$$. \n" +
        #    " ..:$&&:  "
        for char in "\n".join(output[0]):
            self.assertIn(char, " .:$&@\n")

        # Check dimensions
        self.assertEqual(renderer.max_height, 5)
        self.assertEqual(renderer.max_width, 10)

        # Check multi-line seeds work too...
        renderer = Fire(5, 10, "xxxx\nxxxx\nxxxx", 1.0, 20, 8)
        for _ in range(100):
            output = renderer.rendered_text
        for char in "\n".join(output[0]):
            self.assertIn(char, " .:$&@\n")

        # Check BG flag renders to BG colours only...
        renderer = Fire(5, 10, "xxxx\nxxxx\nxxxx", 1.0, 20, 8, bg=True)
        for _ in range(100):
            output = renderer.rendered_text
        for char in "\n".join(output[0]):
            self.assertIn(char, " \n")

    def test_plasma(self):
        """
        Check that the Plasma renderer works.
        """
        # Check basic content of the renderer
        renderer = Plasma(5, 10, 8)

        # Check several renderings
        for _ in range(10):
            output = renderer.rendered_text
            for char in "\n".join(output[0]):
                self.assertIn(char, ' .:;rsA23hHG#9&@\n')

        # Check dimensions
        self.assertEqual(renderer.max_height, 5)
        self.assertEqual(renderer.max_width, 10)

    def test_kaleidoscope(self):
        """
        Check that the Kaleidoscope renderer works.
        """
        # Check basic content of the renderer
        renderer = Kaleidoscope(5, 10, StaticRenderer(["# # #\n" * 5]), 3)

        # Check several renderings
        for _ in range(180):
            output = renderer.rendered_text
            for char in "\n".join(output[0]):
                self.assertIn(char, ' #\n')

        # Check dimensions
        self.assertEqual(renderer.max_height, 5)
        self.assertEqual(renderer.max_width, 10)

    def test_rotated_dup(self):
        """
        Check that the RotatedDuplicate renderer works.
        """
        # Check zero padding
        renderer = RotatedDuplicate(5, 2, StaticRenderer(["ASCII"]))
        self.assertEqual(renderer.rendered_text[0], ['ASCII', 'IICSA'])

        # Check negative padding
        renderer = RotatedDuplicate(3, 2, StaticRenderer(["ASCII\nRULES"]))
        self.assertEqual(renderer.rendered_text[0], ['ULE', 'ELU'])

        # Check positive padding
        renderer = RotatedDuplicate(7, 4, StaticRenderer(["ASCII"]))
        self.assertEqual(renderer.rendered_text[0], [' ', ' ASCII ', ' IICSA ', ' '])

    def test_scale(self):
        renderer = Scale(25)
        self.assertEqual(str(renderer), "----+----1----+----2----+")

    def test_vscale(self):
        renderer = VScale(5)
        self.assertEqual(str(renderer), "1\n2\n3\n4\n5")

if __name__ == '__main__':
    unittest.main()
