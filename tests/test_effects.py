import unittest
from mock.mock import MagicMock
from random import randint
from asciimatics.effects import Print, Cycle, BannerText, Mirage, Scroll, Stars, \
    Matrix, Snow, Wipe
from asciimatics.renderers import FigletText, StaticRenderer
from asciimatics.scene import Scene
from asciimatics.screen import Screen, Canvas
from tests.mock_objects import MockEffect


class TestEffects(unittest.TestCase):
    def assert_blank(self, canvas):
        """
        Check that a specified canvas is blank.
        """
        for x in range(canvas.width):
            for y in range(canvas.height):
                self.assertEqual(canvas.get_from(x, y), (32, 7, 0, 0))

    def check_canvas(self, canvas, buffer, assert_fn):
        changed = False
        for x in range(canvas.width):
            for y in range(canvas.height):
                value = canvas.get_from(x, y)
                assert_fn(value)
                if value != buffer[y][x]:
                    changed = True
                    buffer[y][x] = value
        return changed

    def test_text_effects(self):
        """
        Check effects can be played.        
        """
        # A lot of effects are just about the visual output working when played
        # so check that playing a load of text effects doesn't crash.
        #
        # It's really not a great test, but it's important to show Effects are
        # dynamically compatible with Screen.play().
        def internal_checks(screen):
            screen.play([
                Scene([
                    MockEffect(count=5),
                    Print(screen, FigletText("hello"), 2),
                    Cycle(screen, FigletText("world"), 6),
                    BannerText(screen, FigletText("world"), 10, 3),
                    Mirage(screen, FigletText("huh?"), 14, 2)], 0)])

        Screen.wrapper(internal_checks, height=25)

    def test_scroll(self):
        """
        Check that Scroll works.
        """
        # Check that it will attempt to scroll the screen at the required rate.
        screen = MagicMock(spec=Screen)
        effect = Scroll(screen, 2)
        effect.reset()
        effect.update(1)
        screen.scroll.assert_not_called()
        effect.update(2)
        screen.scroll.assert_called_once()

        # Check there is no stop frame
        self.assertEqual(effect.stop_frame, 0)

    def test_cycle(self):
        """
        Check that Cycle works.
        """
        # Check that cycle swaps colours every other frame.
        screen = MagicMock(spec=Screen)
        effect = Cycle(screen, StaticRenderer(images=["hello"]), 2)
        effect.reset()
        # First 2 calls should do nothing and use black.
        effect.update(0)
        screen.centre.assert_not_called()
        effect.update(1)
        screen.centre.assert_called_with("hello", 2, 0)
        # Next 2 calls should do nothing and use red.
        screen.centre.reset_mock()
        effect.update(2)
        screen.centre.assert_not_called()
        effect.update(3)
        screen.centre.assert_called_with("hello", 2, 1)

        # Check there is no stop frame
        self.assertEqual(effect.stop_frame, 0)

    def test_banner(self):
        """
        Check that BannerText works.
        """
        # Check that banner redraws every frame.
        screen = MagicMock(spec=Screen)
        canvas = Canvas(screen, 10, 100, 0, 0)
        effect = BannerText(canvas, StaticRenderer(images=["hello"]), 2, 3)
        effect.reset()
        effect.update(0)
        self.assertEqual(canvas.get_from(canvas.width - 1, 2),
                         (ord("h"), 3, 0, 0))
        effect.update(1)
        self.assertEqual(canvas.get_from(canvas.width - 1, 2),
                         (ord("e"), 3, 0, 0))

        # Check there is some stop frame - will vary according to screen width
        self.assertGreater(effect.stop_frame, 0)

    def test_print(self):
        """
        Check that the Print Effect works.
        """
        # Check that print only redraws on specified rate.
        screen = MagicMock(spec=Screen)
        effect = Print(screen, StaticRenderer(images=["hello"]), 2, 1)
        effect.reset()
        effect.update(0)
        screen.paint.assert_called_with(
            "hello", 1, 2, 7,
            attr=0,
            bg=0,
            colour_map=[(None, None) for _ in range(5)],
            transparent=True)
        screen.paint.reset_mock()
        effect.update(1)
        effect.update(2)
        effect.update(3)
        screen.paint.assert_not_called()

        # Check there is no stop frame by default.
        self.assertEqual(effect.stop_frame, 0)

    def test_mirage(self):
        """
        Check that Mirage works.
        """
        # Check that Mirage randomly updates the Screen every other frame.
        screen = MagicMock(spec=Screen)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = Mirage(canvas, FigletText("hello"), 3, 1)
        effect.reset()
        effect.update(0)
        self.assert_blank(canvas)
        effect.update(1)
        changed = False
        for x in range(canvas.width):
            for y in range(canvas.height):
                if canvas.get_from(x, y) != (32, 7, 0, 0):
                    changed = True
        self.assertTrue(changed)

        # Check there is no stop frame by default.
        self.assertEqual(effect.stop_frame, 0)

    def test_stars(self):
        """
        Check that Stars works.
        """
        # Check that Stars randomly updates the Screen every frame.
        screen = MagicMock(spec=Screen)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = Stars(canvas, 100)
        effect.reset()
        self.assert_blank(canvas)
        buffer = [[(32, 7, 0, 0) for _ in range(40)] for _ in range(10)]
        for i in range(10):
            effect.update(i)
            self.assertTrue(self.check_canvas(
                canvas,
                buffer,
                lambda value: self.assertIn(chr(value[0]), " .+x*")))

        # Check there is no stop frame by default.
        self.assertEqual(effect.stop_frame, 0)

    def test_matrix(self):
        """
        Check that the Matrix works.
        """
        # Check that Matrix randomly updates the Screen every other frame.
        screen = MagicMock(spec=Screen)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = Matrix(canvas)
        effect.reset()
        self.assert_blank(canvas)
        buffer = [[(32, 7, 0, 0) for _ in range(40)] for _ in range(10)]
        for i in range(10):
            effect.update(i)
            self.assertEqual(self.check_canvas(
                canvas,
                buffer,
                lambda value: self.assertTrue(value[0] == 32 or value[1] == 2)),
                i % 2 == 0)

        # Check there is no stop frame by default.
        self.assertEqual(effect.stop_frame, 0)

    def test_snow(self):
        """
        Check that Snow works.
        """
        # Check that Snow randomly updates the Screen every 3rd frame.
        screen = MagicMock(spec=Screen)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = Snow(canvas)
        effect.reset()
        self.assert_blank(canvas)
        buffer = [[(32, 7, 0, 0) for _ in range(40)] for _ in range(10)]
        for i in range(10):
            effect.update(i)
            self.assertEqual(self.check_canvas(
                canvas,
                buffer,
                lambda value: self.assertIn(chr(value[0]), ".+* ,;#@")),
                i % 3 == 0)

        # Check there is no stop frame by default.
        self.assertEqual(effect.stop_frame, 0)

    def test_wipe(self):
        """
        Check that Wipe works.
        """
        # Check that Wipe clears lines going down the screen.
        screen = MagicMock(spec=Screen)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = Wipe(canvas)
        effect.reset()
        self.assert_blank(canvas)
        buffer = [[(32, 7, 0, 0) for _ in range(40)] for _ in range(10)]
        for x in range(canvas.width):
            for y in range(canvas.height):
                canvas.print_at(chr(randint(1, 128)), x, y)
                buffer[y][x] = canvas.get_from(x, y)
        for i in range(10):
            effect.update(i)
            self.assertEqual(self.check_canvas(
                canvas,
                buffer,
                lambda value: self.assertLess(value[0], 129)),
                i % 2 == 0)

        # Check there is no stop frame by default.
        self.assertEqual(effect.stop_frame, 0)


if __name__ == '__main__':
    unittest.main()
