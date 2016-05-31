import unittest
from datetime import datetime
from mock.mock import MagicMock, patch
from random import randint
import sys
if sys.platform != "win32":
    import curses
from asciimatics.effects import Print, Cycle, BannerText, Mirage, Scroll, Stars, \
    Matrix, Snow, Wipe, Clock, Cog, RandomNoise, Julia
from asciimatics.paths import Path
from asciimatics.renderers import FigletText, StaticRenderer
from asciimatics.scene import Scene
from asciimatics.screen import Screen, Canvas
from asciimatics.sprites import Sam
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
        # Skip for non-Windows if the terminal definition is incomplete.
        # This typically means we're running inside a non-standard termina;.
        # For example, thi happens when embedded in PyCharm.
        if sys.platform != "win32":
            curses.initscr()
            if curses.tigetstr("ri") is None:
                self.skipTest("No valid terminal definition")

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
        screen = MagicMock(spec=Screen, colours=8)
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
        screen = MagicMock(spec=Screen, colours=8)
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
        screen = MagicMock(spec=Screen, colours=8)
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
        screen = MagicMock(spec=Screen, colours=8)
        effect = Print(screen, StaticRenderer(images=["hello"]), 2, 1)
        effect.reset()
        effect.update(0)
        screen.paint.assert_called_with(
            "hello", 1, 2, 7,
            attr=0,
            bg=0,
            colour_map=[(None, None, None) for _ in range(5)],
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
        screen = MagicMock(spec=Screen, colours=8)
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
        screen = MagicMock(spec=Screen, colours=8)
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
        screen = MagicMock(spec=Screen, colours=8)
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
        screen = MagicMock(spec=Screen, colours=8)
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
        screen = MagicMock(spec=Screen, colours=8)
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

    @patch("datetime.datetime")
    def test_clock(self, mock_datetime):
        """
        Check that Clock works.
        """
        # Check that Clock updates every second.
        screen = MagicMock(spec=Screen, colours=8)
        mock_datetime.now.return_value = datetime
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = Clock(canvas, 10, 5, 5)
        effect.reset()
        self.assert_blank(canvas)
        buffer = [[(32, 7, 0, 0) for _ in range(40)] for _ in range(10)]

        # Set a time for the next update and check it is drawn.
        mock_datetime.now.return_value = \
            datetime(1900, 1, 2, 3, 59, 40)
        effect.update(0)
        mock_datetime.now.assert_called()
        self.assertEqual(self.check_canvas(
            canvas,
            buffer,
            lambda value: self.assertLess(value[0], 129)),
            True)

        # Check redrawing with the same time has no effect.
        mock_datetime.now.reset_mock()
        mock_datetime.now.return_value = \
            datetime(1900, 1, 2, 3, 59, 40)
        effect.update(1)
        mock_datetime.now.assert_called()
        self.assertEqual(self.check_canvas(
            canvas,
            buffer,
            lambda value: self.assertLess(value[0], 129)),
            False)

        # Check a new time results in an update.
        mock_datetime.now.reset_mock()
        mock_datetime.now.return_value = \
            datetime(1900, 1, 2, 3, 59, 41)
        effect.update(2)
        mock_datetime.now.assert_called()
        self.assertEqual(self.check_canvas(
            canvas,
            buffer,
            lambda value: self.assertLess(value[0], 129)),
            True)

        # Check there is no stop frame by default.
        self.assertEqual(effect.stop_frame, 0)

    def test_sprite(self):
        """
        Check that Sprites work.
        """
        # Check that we can move a Sprite around the screen.
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        path = Path()
        path.jump_to(10, 5)
        path.move_straight_to(20, 10, 5)
        path.move_straight_to(30, 5, 5)
        path.move_straight_to(20, 0, 5)
        path.move_straight_to(10, 5, 5)
        effect = Sam(canvas, path)
        effect.reset()
        self.assert_blank(canvas)
        buffer = [[(32, 7, 0, 0) for _ in range(40)] for _ in range(10)]
        for i in range(30):
            effect.update(i)
            self.assertEqual(self.check_canvas(
                canvas,
                buffer,
                lambda value: self.assertLess(value[0], 129)),
                i % 2 == 0, "Bad update on frame %d" % i)

        # Check there is no stop frame by default.
        self.assertEqual(effect.stop_frame, 0)

    def test_cog(self):
        """
        Check that Cog works.
        """
        # Check that Cog updates the Screen every other frame.
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = Cog(canvas, 10, 5, 5)
        effect.reset()
        self.assert_blank(canvas)
        buffer = [[(32, 7, 0, 0) for _ in range(40)] for _ in range(10)]
        for i in range(20):
            effect.update(i)
            self.assertEqual(self.check_canvas(
                canvas,
                buffer,
                lambda value: self.assertIn(
                    chr(value[0]), " ''^.|/7.\\|Ywbd#")),
                i % 2 == 0)

        # Check there is no stop frame by default.
        self.assertEqual(effect.stop_frame, 0)

    def test_noise(self):
        """
        Check that RandomNoise works.
        """
        # Check that RandomNoise updates every frame.
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = RandomNoise(canvas)
        effect.reset()
        self.assert_blank(canvas)
        buffer = [[(32, 7, 0, 0) for _ in range(40)] for _ in range(10)]
        for i in range(20):
            effect.update(i)
            self.assertEqual(self.check_canvas(
                canvas,
                buffer,
                lambda value: self.assertLess(value[0], 129)),
                True)

        # Check there is no stop frame by default.
        self.assertEqual(effect.stop_frame, 0)

    def test_julia(self):
        """
        Check that Julia works.
        """
        # Check that Julia updates every frame.
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = Julia(canvas)
        effect.reset()
        self.assert_blank(canvas)
        buffer = [[(32, 7, 0, 0) for _ in range(40)] for _ in range(10)]
        for i in range(20):
            effect.update(i)
            self.assertEqual(self.check_canvas(
                canvas,
                buffer,
                lambda value: self.assertIn(chr(value[0]), '@&9#GHh32As;:. ')),
                True)

        # Check there is no stop frame by default.
        self.assertEqual(effect.stop_frame, 0)

if __name__ == '__main__':
    unittest.main()
