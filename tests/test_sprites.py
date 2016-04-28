import unittest
from asciimatics.paths import Path
from asciimatics.sprites import Sam, Arrow, Plot


class TestSprites(unittest.TestCase):
    def test_init(self):
        # Most of the function in these classes is actually in the Sprite
        # base Effect - so just check we can build these classes
        self.assertIsNotNone(Sam(None, Path()))
        self.assertIsNotNone(Arrow(None, Path()))
        self.assertIsNotNone(Plot(None, Path()))


if __name__ == '__main__':
    unittest.main()
