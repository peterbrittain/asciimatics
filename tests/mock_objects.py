from asciimatics.effects import Effect
from asciimatics.exceptions import StopApplication, NextScene


class MockEffect(Effect):
    """
    Dummy Effect use for some UTs.
    """
    def __init__(self, count=10, stop=True, swallow=False, next_scene=None):
        """
        :param count: When to stop effect
        :param stop: Whether to stop the application or skip to next scene.
        :param swallow: Whether to swallow any events or not.
        """
        super(MockEffect, self).__init__()
        self.stop_called = False
        self.reset_called = False
        self.event_called = False
        self.save_called = False
        self._count = count
        self._stop = stop
        self._swallow = swallow
        self._next_scene = next_scene

    @property
    def stop_frame(self):
        self.stop_called = True
        return 5

    def _update(self, frame_no):
        self._count -= 1
        if self._count <= 0:
            if self._stop:
                raise StopApplication("End of test")
            else:
                raise NextScene(self._next_scene)

    def reset(self):
        self.reset_called = True

    def process_event(self, event):
        self.event_called = True
        return None if self._swallow else event

    def save(self):
        self.save_called = True
