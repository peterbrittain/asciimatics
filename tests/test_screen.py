from random import randint
import unittest
from asciimatics.effects import Effect
from asciimatics.exceptions import StopApplication
from asciimatics.scene import Scene
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
                "Text", 0, 0,
                colour_map=((1, 0, 4), (2, 0, 3), (3, 0, 2), (4, 0, 1)))

            # Check it is rendered as expected.
            char, fg, _, bg = screen.get_from(0, 0)
            self.assertEqual(fg, 1)
            self.assertEqual(bg, 4)
            char, fg, _, bg = screen.get_from(3, 0)
            self.assertEqual(fg, 4)
            self.assertEqual(bg, 1)

        Screen.wrapper(internal_checks)

    def test_limits(self):
        """
        Check that get_from and print_at limit checking works.
        """
        def internal_checks(screen):
            # Check we have some canvas dimensions
            self.assertEqual(screen.dimensions[1], screen.width)
            self.assertEqual(screen.dimensions[0], screen.height)

            # Basic limit checking
            self.assertIsNone(screen.get_from(-1, -1))
            self.assertIsNone(screen.get_from(screen.width, screen.height))

            # Printing off-screen should not fail, but do nothing.
            screen.print_at("hello", 0, -1)
            screen.print_at("hello", 0, screen.height)

            # Printing across screen edge should crop.
            screen.print_at("12345", -1, 0)
            char, fg, _, bg = screen.get_from(0, 0)
            self.assertEqual(char, ord("2"))
            self.assertEqual(fg, Screen.COLOUR_WHITE)
            self.assertEqual(bg, Screen.COLOUR_BLACK)

        Screen.wrapper(internal_checks)

    def test_scroll(self):
        """
        Check that scrolling works as expected.
        """
        def internal_checks(screen):
            # New screen is not scrolled.
            self.assertEqual(screen.start_line, 0)

            # Scroll and check it has moved
            screen.scroll()
            self.assertEqual(screen.start_line, 1)

            # Scroll to specific location and check it has moved
            screen.scroll_to(0)
            self.assertEqual(screen.start_line, 0)

        Screen.wrapper(internal_checks)

    def test_centre(self):
        """
        Check that centre works as expected.
        """
        def internal_checks(screen):
            screen.centre("1234", 0)
            char, fg, _, bg = screen.get_from((screen.width - 4) // 2, 0)
            self.assertEqual(char, ord("1"))
            self.assertEqual(fg, Screen.COLOUR_WHITE)
            self.assertEqual(bg, Screen.COLOUR_BLACK)

        Screen.wrapper(internal_checks)

    def test_draw(self):
        """
        Check that line drawing works as expected.
        """
        def internal_checks(screen):
            # Draw thick and thin lines
            for line_type in (True, False):
                # Draw in opposite directions
                for start in range(0, 11, 10):
                    screen.print_at(str(start), 11, 2)
                    # Horizontal line
                    screen.move(start, 0)
                    screen.draw(10 - start, 0, thin=line_type)
                    res = screen.get_from(1, 0)
                    self.assertEqual(res[0], ord("^" if line_type else "#"))

                    # Check clearing works too
                    screen.draw(start, 0, char=" ", thin=line_type)
                    res = screen.get_from(1, 0)
                    self.assertEqual(res[0], ord(" "))

                    # Vertical line
                    screen.move(0, start)
                    screen.draw(0, 10 - start, thin=line_type)
                    res = screen.get_from(0, 1)
                    self.assertEqual(res[0], ord("|" if line_type else "#"))

                    # Check clearing works too
                    screen.draw(0, start, char=" ", thin=line_type)
                    res = screen.get_from(0, 1)
                    self.assertEqual(res[0], ord(" "))

                    # Diagonal line
                    screen.move(0, start)
                    screen.draw(10, 10 - start, thin=line_type)
                    res = screen.get_from(1, 9 if start else 1)
                    if line_type:
                        self.assertEqual(res[0], ord("/" if start else "\\"))
                    else:
                        self.assertEqual(res[0], ord("d" if start else "Y"))

                    # Check clearing works too
                    screen.move(0, start)
                    screen.draw(10, 10 - start, char=" ", thin=line_type)
                    res = screen.get_from(1, 9 if start else 1)
                    self.assertEqual(res[0], ord(" "))

        Screen.wrapper(internal_checks)

    def test_palette(self):
        """
        Check that we have a valid colour palette.
        """
        def internal_checks(screen):
            # Check basic length
            self.assertGreater(screen.colours, 0)
            self.assertEqual(len(screen.palette), 256 * 3)

            # Should always have fundamental console colours
            for i, c in enumerate((0, 0, 0)):
                self.assertEqual(screen.palette[i], c)
            for i, c in enumerate((128, 0, 0)):
                self.assertEqual(screen.palette[i+3], c)
            for i, c in enumerate((0, 128, 0)):
                self.assertEqual(screen.palette[i+6], c)
            for i, c in enumerate((128, 128, 0)):
                self.assertEqual(screen.palette[i+9], c)
            for i, c in enumerate((0, 0, 128)):
                self.assertEqual(screen.palette[i+12], c)
            for i, c in enumerate((128, 0, 128)):
                self.assertEqual(screen.palette[i+15], c)
            for i, c in enumerate((0, 128, 128)):
                self.assertEqual(screen.palette[i+18], c)
            for i, c in enumerate((192, 192, 192)):
                self.assertEqual(screen.palette[i+21], c)

        Screen.wrapper(internal_checks)

    def test_putch_and_getch(self):
        """
        Check deprecated features still work.
        """
        def internal_checks(screen):
            for x in range(screen.width):
                for y in range(screen.height):
                    char = randint(0, 255)
                    fg = randint(0, Screen.COLOUR_WHITE)
                    bg = randint(0, Screen.COLOUR_WHITE)
                    attr = randint(0, Screen.A_UNDERLINE)
                    screen.putch(chr(char), x, y, fg, attr, bg)
                    char2, fg2, attr2, bg2 = screen.getch(x, y)
                    self.assertEqual(char, char2)
                    self.assertEqual(fg, fg2)
                    self.assertEqual(attr, attr2)
                    self.assertEqual(bg, bg2)

        Screen.wrapper(internal_checks)

    def test_play(self):
        """
        Check that we can play a basic Effect in a Scene.
        """
        class TestEffect(Effect):
            def __init__(self):
                super(TestEffect, self).__init__()
                self.stop_called = False
                self.reset_called = False
                self._count = 10

            @property
            def stop_frame(self):
                self.stop_called = True
                return 5

            def _update(self, frame_no):
                self._count -= 1
                if self._count <= 0:
                    raise StopApplication("End of test")

            def reset(self):
                self.reset_called = True

        def internal_checks(screen):
            # Since the Screen draws things, there's not too much we can do
            # to genuinely verify this without verifying all Scene and Effect
            # function too.  Just play a dummy Effect for now.
            test_effect = TestEffect()
            screen.play([Scene([test_effect], 0)])
            self.assertTrue(test_effect.stop_called)
            self.assertTrue(test_effect.reset_called)

            # Now check that the desired duration is used.
            test_effect = TestEffect()
            screen.play([Scene([test_effect], 15)])
            self.assertFalse(test_effect.stop_called)
            self.assertTrue(test_effect.reset_called)

        Screen.wrapper(internal_checks)

if __name__ == '__main__':
    unittest.main()
