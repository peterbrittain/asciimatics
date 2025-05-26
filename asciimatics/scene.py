"""
This module defines Scene objects for animation purposes.  For more details, see
http://asciimatics.readthedocs.io/en/latest/animation.html
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any, List, Optional
if TYPE_CHECKING:
    from asciimatics.effects import Effect
    from asciimatics.event import Event
    from asciimatics.screen import Screen


class Scene():
    """
    Class to store the details of a single scene to be displayed.  This is
    made up of a set of :py:obj:`.Effect` objects.  See the documentation for
    Effect to understand the interaction between the two classes and
    http://asciimatics.readthedocs.io/en/latest/animation.html for how to use them together.
    """

    def __init__(self,
                 effects: List[Effect],
                 duration: int = 0,
                 clear: bool = True,
                 name: Optional[str] = None):
        """
        :param effects: The list of effects to apply to this scene.
        :param duration: The number of frames in this Scene.  A value of 0 means that the Scene
            should query the Effects to find the duration.  A value of -1 means don't stop.
        :param clear: Whether to clear the Screen at the start of the Scene.
        :param name: Optional name to identify the scene.
        """
        self._effects: list[Effect] = []
        for effect in effects:
            self.add_effect(effect, reset=False)
        self._duration = duration
        if duration == 0:
            self._duration = max(x.stop_frame for x in effects)
        self._clear = clear
        self._name = name

    def reset(self, old_scene: Optional["Scene"] = None, screen: Optional[Screen] = None):
        """
        Reset the scene ready for playing.

        :param old_scene: The previous version of this Scene that was running before the
            application reset - e.g. due to a screen resize.
        :param screen: New screen to use if old_scene is not None.
        """
        # Always reset all the effects.
        for effect in self._effects:
            effect.reset()

        # If we have an old Scene to recreate, get the data out of that and
        # apply it where possible by cloning objects where appropriate.
        if old_scene:
            for old_effect in old_scene.effects:
                # catching AttributeErrors here has hidden bugs, so explicitly
                # check for the cloning interface before calling it.
                if hasattr(old_effect, "clone"):
                    old_effect.clone(screen, self)

    def exit(self):
        """
        Handle any tidy up required on the exit of the Scene.
        """
        # Save off any persistent state for each effect.
        for effect in self._effects:
            if hasattr(effect, "save"):
                effect.save()

    def add_effect(self, effect: Effect, reset: bool = True):
        """
        Add an effect to the Scene.

        This method can be called at any time - even when playing the Scene.  The default logic
        assumes that the Effect needs to be reset before being displayed.  This can be overridden
        using the `reset` parameter.

        :param effect: The Effect to be added.
        :param reset: Whether to reset the Effect that has just been added.
        """
        # Reset the effect in case this is in the middle of a Scene.
        if reset:
            effect.reset()
        effect.register_scene(self)
        self._effects.append(effect)

    def remove_effect(self, effect: Effect):
        """
        Remove an effect from the scene.

        :param effect: The effect to remove.
        """
        self._effects.remove(effect)

    def process_event(self, event: Event) -> Optional[Event]:
        """
        Process a new input event.

        This method will pass the event on to any Effects in reverse Z order so that the
        top-most Effect has priority.

        :param event: The Event that has been triggered.
        :returns: None if the Scene processed the event, else the original event.
        """
        for effect in reversed(self._effects):
            new_event = effect.process_event(event)
            if new_event is None:
                break
            event = new_event
        return event

    @property
    def name(self) -> Optional[str]:
        """
        :return: The name of this Scene.  May be None.
        """
        return self._name

    @property
    def effects(self) -> List[Any]:
        """
        :return: The list of Effects in this Scene.
        """
        return self._effects

    @property
    def duration(self) -> int:
        """
        :return: The length of the scene in frames.
        """
        return self._duration

    @property
    def clear(self) -> bool:
        """
        :return: Whether the Scene should clear at the start.
        """
        return self._clear
