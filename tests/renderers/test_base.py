import unittest
from asciimatics.renderers import StaticRenderer
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
        self.assertEqual(output[1][0][0], (Screen.COLOUR_YELLOW, Screen.A_BOLD, None))

        # Check the ${fg} variant
        renderer = StaticRenderer(images=["${1}XY${2}Z"])
        output = renderer.rendered_text
        self.assertEqual(len(output[0]), len(output[1]))
        self.assertEqual(output[0], ["XYZ"])
        self.assertEqual(output[1][0][0], (Screen.COLOUR_RED, 0, None))
        self.assertEqual(output[1][0][1], (Screen.COLOUR_RED, 0, None))
        self.assertEqual(output[1][0][2], (Screen.COLOUR_GREEN, 0, None))


if __name__ == '__main__':
    unittest.main()
