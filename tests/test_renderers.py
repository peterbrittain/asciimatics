import unittest
import os
from asciimatics.renderers import StaticRenderer, FigletText, ImageFile, \
    ColourImageFile, SpeechBubble, Box
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
        renderer = SpeechBubble("hello")
        self.assertEqual(str(renderer),
                         ".-------.\n" +
                         "| hello |\n" +
                         "`-------`\n")

        renderer = SpeechBubble("world", tail="L")
        self.assertEqual(str(renderer),
                         ".-------.\n" +
                         "| world |\n" +
                         "`-------`\n" +
                         "  )/  \n" +
                         "-\"`\n")

        renderer = SpeechBubble("bye!", tail="R")
        self.assertEqual(str(renderer),
                         ".------.\n" +
                         "| bye! |\n" +
                         "`------`\n" +
                         "    \\(  \n" +
                         "     `\"-\n")

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
        def internal_checks(screen):
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

        Screen.wrapper(internal_checks, height=15)

if __name__ == '__main__':
    unittest.main()
