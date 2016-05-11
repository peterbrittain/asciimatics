import unittest
from mock.mock import MagicMock
from asciimatics.effects import Print, Cycle, BannerText, Mirage, Scroll
from asciimatics.renderers import FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from tests.mock_objects import MockEffect


class TestEffects(unittest.TestCase):
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

if __name__ == '__main__':
    unittest.main()
