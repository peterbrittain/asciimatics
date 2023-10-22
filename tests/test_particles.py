import random
import unittest
from unittest.mock import MagicMock
from asciimatics.particles import ShootScreen, DropScreen, Explosion, Rain, \
    StarFirework, PalmFirework, RingFirework, SerpentFirework
from asciimatics.screen import Screen, Canvas


class TestParticles(unittest.TestCase):
    def setUp(self):
        random.seed(42)

    def check_effect(self, canvas, effect, assert_fn,
                     is_blank=True, iterations=40, warm_up=0):
        """
        Basic checks for all effects.  Since they are all randomised to a
        certain extent, just check the overall content for expected values.
        """
        # Asciimatics always calls reset on entering a new Scene.
        effect.reset()

        # Check canvas is in desired starting state.
        if is_blank:
            for x in range(canvas.width):
                for y in range(canvas.height):
                    self.assertEqual(canvas.get_from(x, y), (32, 7, 0, 0))

        # Set up blank my_buffer - OK this should copy the existing screen, but
        # we just lose one iteration on the checks (when not really blank).
        my_buffer = [[(32, 7, 0, 0) for _ in range(40)] for _ in range(10)]

        # Re-draw comparing the my_buffer with what's on the canvas
        for i in range(iterations):
            effect.update(i)
            changed = False
            if i >= warm_up:
                view = ""
                for y in range(canvas.height):
                    for x in range(canvas.width):
                        value = canvas.get_from(x, y)
                        assert_fn(value)
                        if value != my_buffer[y][x]:
                            changed = True
                            my_buffer[y][x] = value
                        view += chr(value[0])
                    view += "\n"
                self.assertTrue(changed, "failed at step %d %s" % (i, view))

        # Check there is no stop frame by default.
        self.assertEqual(effect.stop_frame, 0)

    def test_shoot_screen(self):
        """
        Test that ShootScreen works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        canvas.centre("Hello World!", 5)
        effect = ShootScreen(canvas, canvas.width // 2, canvas.height // 2, 100, diameter=10)
        self.check_effect(canvas,
                          effect,
                          lambda value: self.assertIn(chr(value[0]),
                                                      'HeloWrd! '),
                          is_blank=False,
                          iterations=4)

    def test_drop_screen(self):
        """
        Test that DropScreen works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        canvas.centre("Hello World!", 0)
        effect = DropScreen(canvas, 100)
        self.check_effect(canvas,
                          effect,
                          lambda value: self.assertIn(chr(value[0]),
                                                      'HeloWrd! '),
                          is_blank=False,
                          warm_up=3,
                          iterations=10)

    def test_explosion(self):
        """
        Test that Explosion works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = Explosion(canvas, 4, 4, 25)
        self.check_effect(canvas,
                          effect,
                          lambda value: self.assertIn(chr(value[0]), ' #'),
                          iterations=25)

    def test_rain(self):
        """
        Test that Rain works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = Rain(canvas, 200)
        self.check_effect(canvas,
                          effect,
                          lambda value: self.assertIn(chr(value[0]), ' `\\v'))

    def test_star_firework(self):
        """
        Test that StarFirework works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = StarFirework(canvas, 4, 4, 25)
        self.check_effect(canvas,
                          effect,
                          lambda value: self.assertIn(chr(value[0]), '|+:,. '),
                          iterations=25)

    def test_palm_firework(self):
        """
        Test that PalmFirework works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = PalmFirework(canvas, 4, 4, 25)
        self.check_effect(canvas,
                          effect,
                          lambda value: self.assertIn(chr(value[0]), '|*+:,. '),
                          iterations=26)

    def test_ring_firework(self):
        """
        Test that RingFirework works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = RingFirework(canvas, 4, 4, 25)
        self.check_effect(canvas,
                          effect,
                          lambda value: self.assertIn(chr(value[0]), '|*:. '),
                          iterations=15)

    def test_serpent_firework(self):
        """
        Test that SerpentFirework works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        effect = SerpentFirework(canvas, 4, 4, 25)
        self.check_effect(canvas,
                          effect,
                          lambda value: self.assertIn(chr(value[0]), '|+- '),
                          iterations=20)


if __name__ == '__main__':
    unittest.main()
