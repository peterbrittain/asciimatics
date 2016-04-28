import unittest
from asciimatics.event import MouseEvent
from asciimatics.scene import Scene
from tests.mock_objects import MockEffect


class TestScene(unittest.TestCase):
    def test_properties(self):
        """
        Check properties work as expected.
        """
        effect = MockEffect()
        scene = Scene([effect], duration=10, clear=False, name="blah")
        self.assertEqual(scene.name, "blah")
        self.assertEqual(scene.duration, 10)
        self.assertFalse(scene.clear)

    def test_dynamic_effects(self):
        """
        Check adding and removing effects works.
        """
        # Start with no effects
        effect = MockEffect()
        scene = Scene([], duration=10)
        self.assertEqual(scene.effects, [])

        # Add one - check internals for presence
        scene.add_effect(effect)
        self.assertEqual(scene.effects, [effect])

        # Remove it - check it's gone
        scene.remove_effect(effect)
        self.assertEqual(scene.effects, [])

    def test_events(self):
        """
        Check event processing is queued correctly.
        """
        # Check that the scene passes events through to the effects
        effect1 = MockEffect()
        effect2 = MockEffect()
        scene = Scene([effect1, effect2], duration=10)
        scene.process_event(MouseEvent(10, 5, 0))
        self.assertTrue(effect1.event_called)
        self.assertTrue(effect2.event_called)

        # Check that the scene passes stops event processing when required
        effect1 = MockEffect()
        effect2 = MockEffect(swallow=True)
        scene = Scene([effect1, effect2], duration=10)
        scene.process_event(MouseEvent(10, 5, 0))
        self.assertFalse(effect1.event_called)
        self.assertTrue(effect2.event_called)

    def test_save(self):
        """
        Check scene will save data on exit if needed.
        """
        effect = MockEffect()
        scene = Scene([effect], duration=10)
        self.assertFalse(effect.save_called)
        scene.exit()
        self.assertTrue(effect.save_called)


if __name__ == '__main__':
    unittest.main()
