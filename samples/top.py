from asciimatics.event import KeyboardEvent
from asciimatics.widgets import Frame, Layout, MultiColumnListBox, Widget, Label
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication
import sys
import psutil

# Text constants for the UI
FOOTER_L = "Another example from asciimatics"
FOOTER_R = "written by Peter Brittain"


class DemoFrame(Frame):
    def __init__(self, screen):
        super(DemoFrame, self).__init__(screen,
                                        screen.height,
                                        screen.width,
                                        has_border=False,
                                        name="My Form")
        # Internal state for doing periodic updates
        self._last_frame = 0
        self._list = MultiColumnListBox(Widget.FILL_FRAME,
                                        [6, 10, 3, 10, 10, 5, 5, 100],
                                        [], name="mc_list")
        self._list.disabled = True

        # Create the basic form layout...
        layout = Layout([1], fill_frame=True)
        header = Label("")
        footer = Label("")
        self.add_layout(layout)
        layout.add_widget(header)
        layout.add_widget(self._list)
        layout.add_widget(footer)
        self.fix()

        # Update the dynamic header and footer.
        # TODO: don't like the access to this internal field.
        header._text = "  Some info:  86%, 10%, 4%        Some more: 1.2GB"
        footer._text = "{}{:{}}{}".format(FOOTER_L,
                                          "",
                                          max(1, self._canvas.width - len(FOOTER_L) - len(FOOTER_R)),
                                          FOOTER_R)

        # Add my own colour palette
        for key in self.palette:
            self.palette[key] = (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)
        for key in ["selected_focus_field", "label"]:
            self.palette[key] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK)

    def process_event(self, event):
        # Allow for normal handling in alll widgets.
        event = super(DemoFrame, self).process_event(event)

        # Now do some global key handling for this Frame.
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('q'), ord('Q')]:
                raise StopApplication("User quit")

    def _update(self, frame_no):
        # Refresh the list view if needed
        if frame_no - self._last_frame >= 20 or self._last_frame == 0:
            self._last_frame = frame_no

            # Create the data to go in the mutli-column list...
            last_selection = self._list.value
            list_data = []
            for process in psutil.process_iter():
                memory = process.memory_info()
                # TODO: handle other types better?
                data = [
                    str(process.pid),
                    process.username(),
                    str(process.nice()),
                    str(memory.vms),
                    str(memory.rss),
                    str(round(process.cpu_percent() * 10, 0) / 10),
                    str(round(process.memory_percent() * 10, 0) / 10),
                    process.name()
                ]
                list_data.append((data, process.pid))

            # Apply current sort
            list_data = sorted(list_data, key=lambda x: x[0][5], reverse=True)

            # Update the list and try to reset the last selection.
            self._list.options = list_data
            self._list.value = last_selection

        # Now redraw as normal
        super(DemoFrame, self)._update(frame_no)

    @property
    def frame_update_count(self):
        # TODO: something better to handle this?
        return 20


def demo(screen):
    screen.play([Scene([DemoFrame(screen)], -1)], stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True)
        sys.exit(0)
    except ResizeScreenError:
        pass
