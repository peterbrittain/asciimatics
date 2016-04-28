import unittest
from asciimatics.event import KeyboardEvent, MouseEvent


class TestEvents(unittest.TestCase):
    def test_keyboard_event(self):
        """
        Check Keyboard event is consistent.
        """
        code = 123
        event = KeyboardEvent(code)
        self.assertEqual(event.key_code, code)
        self.assertIn(str(code), str(event))

    def test_mouse_event(self):
        """
        Check Mouse event is consistent.
        """
        x = 1
        y = 2
        buttons = MouseEvent.DOUBLE_CLICK
        event = MouseEvent(x, y, buttons)
        self.assertEqual(event.x, x)
        self.assertEqual(event.y, y)
        self.assertEqual(event.buttons, buttons)
        self.assertIn("({}, {})".format(x, y), str(event))
        self.assertIn(str(buttons), str(event))


if __name__ == '__main__':
    unittest.main()
