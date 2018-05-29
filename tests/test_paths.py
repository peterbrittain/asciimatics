import unittest
from asciimatics.event import MouseEvent
from asciimatics.paths import Path, DynamicPath


class TestPaths(unittest.TestCase):
    def assert_path_equals(self, path, oracle):
        path.reset()
        positions = []
        while not path.is_finished():
            positions.append(path.next_pos())
        self.assertEqual(positions, oracle)

    def test_jump_and_wait(self):
        """
        Check basic movement of cursor works.
        """
        path = Path()
        path.jump_to(10, 10)
        path.wait(3)
        self.assert_path_equals(path, [(10, 10), (10, 10), (10, 10), (10, 10)])

    def test_straight_lines(self):
        """
        Check a path works in straight lines.
        """
        # Horizontal
        path = Path()
        path.jump_to(10, 10)
        path.move_straight_to(15, 10, 5)
        self.assert_path_equals(
            path,
            [(10, 10), (11, 10), (12, 10), (13, 10), (14, 10), (15, 10)])

        # Vertical
        path = Path()
        path.jump_to(5, 5)
        path.move_straight_to(5, 10, 5)
        self.assert_path_equals(
            path,
            [(5, 5), (5, 6), (5, 7), (5, 8), (5, 9), (5, 10)])

        # Diagonal spaced
        path = Path()
        path.jump_to(5, 5)
        path.move_straight_to(15, 15, 5)
        self.assert_path_equals(
            path,
            [(5, 5), (7, 7), (9, 9), (11, 11), (13, 13), (15, 15)])

    def test_spline(self):
        """
        Check a path works with a spline curve.
        """
        path = Path()
        path.jump_to(0, 10)
        path.move_round_to([(0, 10), (20, 0), (40, 10), (20, 20), (0, 10)], 20)
        self.assert_path_equals(
            path,
            [(0, 10), (0, 10), (0, 10), (0, 10), (0, 10), (5, 7),
             (10, 4), (15, 1), (20, 0), (25, 1), (30, 3), (35, 7),
             (40, 10), (35, 12), (30, 16), (25, 18), (20, 20),  (15, 18),
             (10, 15), (5, 12), (0, 10)])

    def test_dynamic_path(self):
        """
        Check a dynamic path works as expected.
        """
        class TestPath(DynamicPath):
            def process_event(self, event):
                # Assume that we're always passing in a MouseEvent.
                self._x = event.x
                self._y = event.y

        # Initial path should start at specified location.
        path = TestPath(None, 0, 0)
        self.assertEqual(path.next_pos(), (0, 0))
        self.assertFalse(path.is_finished())

        # Process event should move location.
        path.process_event(MouseEvent(10, 5, 0))
        self.assertEqual(path.next_pos(), (10, 5))

        # Reset should return to original location.
        path.reset()
        self.assertEqual(path.next_pos(), (0, 0))


if __name__ == '__main__':
    unittest.main()
