import unittest
from asciimatics.renderers import Typewriter, StaticRenderer


class TestRendererTypewriter(unittest.TestCase):

    def test_typewriter(self):
        """
        Check that the Typewriter renderer works.
        """
        # Check basic operation
        renderer = Typewriter(StaticRenderer(["Hello\nWorld"]))
        output = "\n".join(renderer.rendered_text[0])
        self.assertEqual(output, "H    \n     ")
        output = "\n".join(renderer.rendered_text[0])
        self.assertEqual(output, "He   \n     ")
        output = "\n".join(renderer.rendered_text[0])
        self.assertEqual(output, "Hel  \n     ")
        output = "\n".join(renderer.rendered_text[0])
        self.assertEqual(output, "Hell \n     ")
        output = "\n".join(renderer.rendered_text[0])
        self.assertEqual(output, "Hello\n     ")
        output = "\n".join(renderer.rendered_text[0])
        self.assertEqual(output, "Hello\nW    ")
        output = "\n".join(renderer.rendered_text[0])
        self.assertEqual(output, "Hello\nWo   ")
        output = "\n".join(renderer.rendered_text[0])
        self.assertEqual(output, "Hello\nWor  ")
        output = "\n".join(renderer.rendered_text[0])
        self.assertEqual(output, "Hello\nWorl ")
        output = "\n".join(renderer.rendered_text[0])
        self.assertEqual(output, "Hello\nWorld")

        # Check dimensions
        self.assertEqual(renderer.max_height, 2)
        self.assertEqual(renderer.max_width, 5)

    def test_generator(self):
        """
        Check that the Typewriter generator works.
        """
        # Check images operation works for embedding in static renderers
        renderer = Typewriter(StaticRenderer(["Hello"]))
        output = renderer.images
        self.assertEqual(output, [["H    "], ["He   "], ["Hel  "], ["Hell "], ["Hello"]])


if __name__ == '__main__':
    unittest.main()
