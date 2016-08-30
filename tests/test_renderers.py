# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import unittest
import os
import sys
if sys.platform != "win32":
    import curses
from asciimatics.renderers import StaticRenderer, FigletText, ImageFile, \
    ColourImageFile, SpeechBubble, Box, Rainbow, BarChart, Fire
from asciimatics.screen import Screen


class TestRenderers(unittest.TestCase):
    def test_height(self):
        """
        Check that the max_height property works.
        """
        # Max height should match largest height of any entry.
        renderer = StaticRenderer(images=["A\nB", "C  "])
        self.assertEqual(renderer.max_height, 2)

    def test_width(self):
        """
        Check that the max_width property works.
        """
        # Max width should match largest width of any entry.
        renderer = StaticRenderer(images=["A\nB", "C  "])
        self.assertEqual(renderer.max_width, 3)

    def test_images(self):
        """
        Check that the images property works.
        """
        # Images should be the parsed versions of the original strings.
        renderer = StaticRenderer(images=["A\nB", "C  "])
        images = renderer.images
        self.assertEqual(next(images), ["A", "B"])
        self.assertEqual(next(images), ["C  "])

    def test_repr(self):
        """
        Check that the string representation works.
        """
        # String presentation should be the first image as a printable string.
        renderer = StaticRenderer(images=["A\nB", "C  "])
        self.assertEqual(str(renderer), "A\nB")

    def test_colour_maps(self):
        """
        Check that the ${} syntax is parsed correctly.
        """
        # Check the ${fg, attr, bg} variant
        renderer = StaticRenderer(images=["${3,1,2}*"])
        output = renderer.rendered_text
        self.assertEqual(len(output[0]), len(output[1]))
        self.assertEqual(output[0], ["*"])
        self.assertEqual(
            output[1][0][0],
            (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_GREEN))

        # Check the ${fg, attr} variant
        renderer = StaticRenderer(images=["${3,1}*"])
        output = renderer.rendered_text
        self.assertEqual(len(output[0]), len(output[1]))
        self.assertEqual(output[0], ["*"])
        self.assertEqual(output[1][0][0], (Screen.COLOUR_YELLOW, Screen.A_BOLD))

        # Check the ${fg} variant
        renderer = StaticRenderer(images=["${1}XY${2}Z"])
        output = renderer.rendered_text
        self.assertEqual(len(output[0]), len(output[1]))
        self.assertEqual(output[0], ["XYZ"])
        self.assertEqual(output[1][0][0], (Screen.COLOUR_RED, 0))
        self.assertEqual(output[1][0][1], (Screen.COLOUR_RED, 0))
        self.assertEqual(output[1][0][2], (Screen.COLOUR_GREEN, 0))

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
                         "`-------`\n")

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
                         u"╰───────╯\n")

    def test_box(self):
        """
        Check that the Box renderer works.
        """
        renderer = Box(10, 3)
        self.assertEqual(str(renderer),
                         "+--------+\n" +
                         "|        |\n" +
                         "+--------+\n")

    def test_image_files(self):
        """
        Check that the ImageFile renderer works.
        """
        renderer = ImageFile(
            os.path.join(os.path.dirname(__file__), "globe.gif"), height=10)

        # Check renderer got all images from the file.
        count = 0
        for image in renderer.images:
            count += 1
            self.assertIsNotNone(image)
            self.assertIsNotNone(len(image) <= renderer.max_height)
        self.assertEqual(count, 11)

        # Check an image looks plausible
        image = next(renderer.images)
        self.assertEqual(
            image,
            ['',
             '        .:;rA       ',
             '    :2HG#;H2;s;;2   ',
             '  .::#99&G@@hsr;;s3 ',
             ' .:;;9&@@@Hrssrrr;22',
             's.:;;;@Hs2GArsssrrr#',
             '..:;;;rrsGA&&Gsrrr;r',
             ' .:;;;;rsr@@@@@@Hs;:',
             ' ;.:;;;;rrA@@@@@G;: ',
             '   .::;;;;;2&9G:;:  ',
             '     ..:::;Gr::s    '])

    def test_colour_image_file(self):
        """
        Check that the ColourImageFile renderer works.
        """
        # Skip for non-Windows if the terminal definition is incomplete.
        # This typically means we're running inside a non-standard terminal.
        # For example, this happens when embedded in PyCharm.
        if sys.platform != "win32":
            curses.initscr()
            if curses.tigetstr("ri") is None:
                self.skipTest("No valid terminal definition")

        def internal_checks(screen):
            # Check the original FG only rendering
            renderer = ColourImageFile(
                screen,
                os.path.join(os.path.dirname(__file__), "globe.gif"),
                height=10)

            # Check renderer got all images from the file.
            count = 0
            for image in renderer.images:
                count += 1
                self.assertIsNotNone(image)
                self.assertIsNotNone(len(image) <= renderer.max_height)
            self.assertEqual(count, 11)

            # Check an image looks plausible
            image = next(renderer.images)
            self.assertEqual(
                image,
                ['',
                 '        #####       ',
                 '    #############   ',
                 '  ################# ',
                 ' ###################',
                 '####################',
                 '####################',
                 ' ###################',
                 ' ################## ',
                 '   ###############  ',
                 '     ###########    '])

            # Also check the BG rendering
            renderer2 = ColourImageFile(
                screen,
                os.path.join(os.path.dirname(__file__), "globe.gif"),
                fill_background=True,
                height=10)

            # Check BG rendering doesn't change the text output.
            image2 = next(renderer2.images)
            self.assertEqual(image, image2)

            # Check BG rendering gives same colours for FG and BG as original
            # rendering
            for a, b in zip(renderer.rendered_text[1], renderer2.rendered_text[1]):
                for attr1, attr2 in zip(a, b):
                    if attr1[0] is None:
                        self.assertEqual(0, attr2[0])
                        self.assertEqual(0, attr2[2])
                    else:
                        self.assertEqual(attr1[0], attr2[0])
                        self.assertEqual(attr2[0], attr2[2])

        Screen.wrapper(internal_checks, height=15)

    def test_rainbow(self):
        """
        Check that the Rainbow renderer works.
        """
        # Skip for non-Windows if the terminal definition is incomplete.
        # This typically means we're running inside a non-standard terminal.
        # For example, this happens when embedded in PyCharm.
        if sys.platform != "win32" and curses.tigetstr("ri") is None:
            self.skipTest("No valid terminal definition")

        def internal_checks(screen):
            # Create a base renderer
            plain_text = (".-------.\n" +
                          "| hello |\n" +
                          "`-------`\n")
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
                    [(1, 1), (1, 1), (3, 1), (3, 1), (2, 1), (2, 1), (6, 1),
                     (6, 1), (4, 1)],
                    [(1, 1), (3, 1), (3, 1), (2, 1), (2, 1), (6, 1), (6, 1),
                     (4, 1), (4, 1)],
                    [(3, 1), (3, 1), (2, 1), (2, 1), (6, 1), (6, 1), (4, 1),
                     (4, 1), (5, 1)],
                    []])

        Screen.wrapper(internal_checks, height=15)

    def test_bar_chart(self):
        """
        Check that the BarChart renderer works.
        """
        # Internal test function for rendering
        def fn():
            return 10

        # Check default implementation
        renderer = BarChart(7, 20, [fn, fn])
        self.assertEqual(
            str(renderer),
            "+------------------+\n" +
            "|                  |\n" +
            "|  |######         |\n" +
            "|  |               |\n" +
            "|  |######         |\n" +
            "|                  |\n" +
            "+------------------+")

        self.assertEqual(
            "\n".join(renderer.images[0]),
            "+------------------+\n" +
            "|                  |\n" +
            "|  |######         |\n" +
            "|  |               |\n" +
            "|  |######         |\n" +
            "|                  |\n" +
            "+------------------+")

        # Switch on non-defaults
        renderer = BarChart(5, 30, [fn, fn], scale=10.0, axes=BarChart.BOTH,
                            intervals=2.5, labels=True, border=False,
                            keys=["A", "B"])
        self.assertEqual(
            str(renderer),
            "A |########################## \n" +
            "  |      :      :     :       \n" +
            "B |########################## \n" +
            "  +------+------+-----+------ \n" +
            "   0    2.5    5.0   7.5 10.0 ")

        # Check gradients
        renderer = BarChart(7, 20, [fn, fn], gradient=[(4, 1), (8, 2), (15, 2)])
        self.assertEqual(
            str(renderer),
            "+------------------+\n" +
            "|                  |\n" +
            "|  |######         |\n" +
            "|  |               |\n" +
            "|  |######         |\n" +
            "|                  |\n" +
            "+------------------+")
        self.assertEqual(
            renderer.rendered_text[1][2],
            [(7, 2, 0),
             (None, 0, 0),
             (None, 0, 0),
             (7, 2, 0),
             (1, 2, 0),
             (1, 2, 0),
             (2, 2, 0),
             (2, 2, 0),
             (2, 2, 0),
             (2, 2, 0),
             (None, 0, 0),
             (None, 0, 0),
             (None, 0, 0),
             (None, 0, 0),
             (None, 0, 0),
             (None, 0, 0),
             (None, 0, 0),
             (None, 0, 0),
             (None, 0, 0),
             (7, 2, 0)])

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

if __name__ == '__main__':
    unittest.main()
