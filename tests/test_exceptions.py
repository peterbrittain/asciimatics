import unittest
from asciimatics.exceptions import ResizeScreenError, StopApplication
from asciimatics.scene import Scene
from tests.mock_objects import MockEffect


class TestExceptions(unittest.TestCase):
    def test_resize(self):
        """
        Check that we can create a ResizeScreenError
        """
        scene = Scene([MockEffect()])
        message = "Test message"
        error = ResizeScreenError(message, scene)
        self.assertEqual(error.scene, scene)
        self.assertEqual(str(error), message)

    def test_stop_app(self):
        """
        Check that we can create a StopApplication.
        """
        message = "Test message"
        error = StopApplication(message)
        self.assertEqual(str(error), message)


if __name__ == '__main__':
    unittest.main()
