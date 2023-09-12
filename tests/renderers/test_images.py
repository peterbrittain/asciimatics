import unittest
import os
import sys
from asciimatics.renderers import ImageFile, ColourImageFile
from asciimatics.screen import Screen
if sys.platform != "win32":
    import curses


class TestRendererImages(unittest.TestCase):
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
        self.maxDiff = None
        self.assertEqual(
            image,
            ['',
             '     sA3h3h3Hr2     ',
             '  ;:;G#99G@&2;;;r   ',
             ' .::#9&&@@G;rrrr;;3 ',
             '.:;;A&@AAGsssssrr;#H',
             '.:;;;r29@srssssrr;A2',
             '.::;;rrrrr@@@@9;r;;A',
             's.:;;;;rr2@@@@@@#;; ',
             ' s.::;;;;;;9&&&3;:  ',
             '   ..::;;;;9#r::2   ',
             '      s...r.;       '])

    def test_colour_image_file(self):
        """
        Check that the ColourImageFile renderer works.
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
            self.maxDiff = None
            self.assertEqual(
                image,
                ['',
                 '     ##########     ',
                 '  ###############   ',
                 ' ################## ',
                 '####################',
                 '####################',
                 '####################',
                 '################### ',
                 ' #################  ',
                 '   ##############   ',
                 '      #######       '])

            # Also check the BG rendering
            renderer2 = ColourImageFile(
                screen,
                os.path.join(os.path.dirname(__file__), "globe.gif"),
                fill_background=True,
                height=10)

            # Check BG rendering doesn't change the visible text output.
            # Note that BG rendering needs to print dots for some terminals.
            image2 = [x.replace(".", " ") for x in next(renderer2.images)]
            self.assertEqual(image, image2)

            # Check BG rendering gives same colours for FG and BG as original
            # rendering
            for a, b in zip(renderer.rendered_text[1],
                            renderer2.rendered_text[1]):
                for attr1, attr2 in zip(a, b):
                    if attr1[0] is None:
                        self.assertEqual(0, attr2[0])
                        self.assertEqual(0, attr2[2])
                    else:
                        self.assertEqual(attr1[0], attr2[0])
                        self.assertEqual(attr2[0], attr2[2])

        Screen.wrapper(internal_checks, height=15)

    def test_uni_image_files(self):
        """
        Check that the unicode ColourImageFile rendering works.
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
            # Check the original FG only rendering
            renderer = ColourImageFile(
                screen,
                os.path.join(os.path.dirname(__file__), "globe.gif"),
                height=10, uni=True, dither=True)

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
                ['.',
                 '....▄▄▄▄▄▄▄▄▄▄▄▄.....',
                 '..▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄...',
                 '.▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄..',
                 '▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄.',
                 '▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄.',
                 '▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄.',
                 '▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄..',
                 '.▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄..',
                 '..▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄....',
                 '.....▄▄▄▄▄▄▄▄▄▄......'])

        Screen.wrapper(internal_checks, height=15)


if __name__ == '__main__':
    unittest.main()
