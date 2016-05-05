import unittest
from asciimatics.renderers import StaticRenderer
from asciimatics.screen import Screen


class TestRenderers(unittest.TestCase):
    def test_static_renderer(self):
        """
        Check that the base static renderer class works.
        """
        # Check basic API for a renderer...
        renderer = StaticRenderer(images=["A\nB", "C  "])

        # Max height should match largest height of any entry.
        self.assertEqual(renderer.max_height, 2)

        # Max width should match largest width of any entry.
        self.assertEqual(renderer.max_width, 3)

        # Images should be the parsed versions of the original strings.
        images = renderer.images
        self.assertEqual(next(images), ["A", "B"])
        self.assertEqual(next(images), ["C  "])

        # String presentation should be the first image as a printable string.
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

if __name__ == '__main__':
    unittest.main()
