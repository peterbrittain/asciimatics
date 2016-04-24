from random import randint
import unittest
from asciimatics.screen import Screen

class TestScreen(unittest.TestCase):
    def test_wrapper(self):
        """
        Check that you can create a blank Screen.
        """
        def internal_checks(screen):
            # Check screen basically exists
            self.assertIsNotNone(screen)
            self.assertGreater(screen.width, 0)
            self.assertGreater(screen.height, 0)
            self.assertGreater(screen.colours, 0)

            # Check that the Screen is cleared ready for use.
            for x in range(screen.width):
                for y in range(screen.height):
                    char, fg, attr, bg = screen.get_from(x, y)
                    self.assertEqual(char, ord(" "))
                    self.assertEqual(fg, Screen.COLOUR_WHITE)
                    self.assertEqual(attr, 0)
                    self.assertEqual(bg, Screen.COLOUR_BLACK)

        Screen.wrapper(internal_checks)

    def test_print_and_get(self):
        """
        Check that basic print_at and get_from work as expected.
        """
        def internal_checks(screen):
            for x in range(screen.width):
                for y in range(screen.height):
                    char = randint(0, 255)
                    fg = randint(0, Screen.COLOUR_WHITE)
                    bg = randint(0, Screen.COLOUR_WHITE)
                    attr = randint(0, Screen.A_UNDERLINE)
                    screen.print_at(chr(char), x, y, fg, attr, bg)
                    char2, fg2, attr2, bg2 = screen.get_from(x, y)
                    self.assertEqual(char, char2)
                    self.assertEqual(fg, fg2)
                    self.assertEqual(attr, attr2)
                    self.assertEqual(bg, bg2)

        Screen.wrapper(internal_checks)

    def test_visible(self):
        """
        Check that is_visible works as expected.
        """
        def internal_checks(screen):
            # Check some points that must always be visible
            self.assertTrue(screen.is_visible(0, 0))
            self.assertTrue(screen.is_visible(
                screen.width - 1, screen.height - 1))

            # Check some points that cannot be visible
            self.assertFalse(screen.is_visible(-1, -1))
            self.assertFalse(screen.is_visible(
                screen.width, screen.height))

        Screen.wrapper(internal_checks)

    def test_paint(self):
        """
        Check that paint with colour map works.
        """
        def internal_checks(screen):
            # Put a simple colour map to screen.
            screen.paint(
                "Text", 0, 0, colour_map=((1, 0, 4), (2, 0, 3), (3, 0, 2), (4, 0, 1)))

            # Check it is rendered as expected.
            char, fg, _, bg = screen.get_from(0, 0)
            self.assertEqual(fg, 1)
            self.assertEqual(bg, 4)
            char, fg, _, bg = screen.get_from(3, 0)
            self.assertEqual(fg, 4)
            self.assertEqual(bg, 1)


        Screen.wrapper(internal_checks)


if __name__ == '__main__':
    unittest.main()
