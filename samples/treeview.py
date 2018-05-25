from asciimatics.event import KeyboardEvent
from asciimatics.widgets import Frame, Layout, FileBrowser, Widget, Label, PopUpDialog, Text, \
    Divider
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication
import sys
import os
try:
    import magic
except ImportError:
    pass


class DemoFrame(Frame):
    def __init__(self, screen):
        super(DemoFrame, self).__init__(
            screen, screen.height, screen.width, has_border=False, name="My Form")

        # Create the (very simple) form layout...
        layout = Layout([1], fill_frame=True)
        self.add_layout(layout)

        # Now populate it with the widgets we want to use.
        self._details = Text()
        self._details.disabled = True
        self._details.custom_colour = "field"
        self._list = FileBrowser(Widget.FILL_FRAME,
                                 os.path.abspath("."),
                                 name="mc_list",
                                 on_select=self.popup,
                                 on_change=self.details)
        layout.add_widget(Label("Local disk browser sample"))
        layout.add_widget(Divider())
        layout.add_widget(self._list)
        layout.add_widget(Divider())
        layout.add_widget(self._details)
        layout.add_widget(Label("Press Enter to select or `q` to quit."))

        # Prepare the Frame for use.
        self.fix()

    def popup(self):
        # Just confirm whenever the user actually selects something.
        self._scene.add_effect(
            PopUpDialog(self._screen, "You selected: {}".format(self._list.value), ["OK"]))

    def details(self):
        # If python magic is installed, provide a little more detail of the current file.
        if self._list.value:
            if os.path.isdir(self._list.value):
                self._details.value = "Directory"
            elif os.path.isfile(self._list.value):
                try:
                    self._details.value = magic.from_file(self._list.value)
                except NameError:
                    self._details.value = "File (run 'pip install python-magic' for more details)"
        else:
            self._details.value = "--"

    def process_event(self, event):
        # Do the key handling for this Frame.
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('q'), ord('Q'), Screen.ctrl("c")]:
                raise StopApplication("User quit")

        # Now pass on to lower levels for normal handling of the event.
        return super(DemoFrame, self).process_event(event)


def demo(screen, old_scene):
    screen.play([Scene([DemoFrame(screen)], -1)], stop_on_resize=True, start_scene=old_scene)


last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
