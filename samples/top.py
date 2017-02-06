from asciimatics.event import KeyboardEvent
from asciimatics.widgets import Frame, Layout, MultiColumnListBox, Widget, Label
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication
import sys
try:
    import psutil
except ImportError:
    print("This sample requires psutil.")
    print("Please run `pip install psutil` and try again.")
    sys.exit(0)


class DemoFrame(Frame):
    def __init__(self, screen):
        super(DemoFrame, self).__init__(screen,
                                        screen.height,
                                        screen.width,
                                        has_border=False,
                                        name="My Form")
        # Internal state for doing periodic updates
        self._last_frame = 0
        self._sort = 5
        self._reverse = True
        self._list = MultiColumnListBox(Widget.FILL_FRAME,
                                        [6, 10, 3, 10, 10, 5, 5, 100],
                                        [], name="mc_list")
        self._list.disabled = True

        # Create the basic form layout...
        layout = Layout([1], fill_frame=True)
        self._header = Label("")
        footer = Label("Press `<`/`>` to change sort, `r` to toggle order, or `q` to quit.")
        self.add_layout(layout)
        layout.add_widget(self._header)
        layout.add_widget(self._list)
        layout.add_widget(footer)
        self.fix()

        # Add my own colour palette
        for key in self.palette:
            self.palette[key] = (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)
        for key in ["selected_focus_field", "label"]:
            self.palette[key] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK)

    def process_event(self, event):
        # Allow for normal handling in all widgets.
        event = super(DemoFrame, self).process_event(event)

        # Now do some global key handling for this Frame.
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('q'), ord('Q'), Screen.ctrl("c")]:
                raise StopApplication("User quit")
            elif event.key_code in [ord("r"), ord("R")]:
                self._reverse = not self._reverse
            elif event.key_code == ord("<"):
                self._sort = max(0, self._sort - 1)
            elif event.key_code == ord(">"):
                self._sort = min(7, self._sort + 1)

            # Force a refresh for improved responsiveness
            self._last_frame = 0

    def _update(self, frame_no):
        # Refresh the list view if needed
        if frame_no - self._last_frame >= 20 or self._last_frame == 0:
            self._last_frame = frame_no

            # Create the data to go in the multi-column list...
            last_selection = self._list.value
            list_data = []
            for process in psutil.process_iter():
                memory = process.memory_info()
                data = [
                    process.pid,
                    process.username(),
                    process.nice(),
                    memory.vms,
                    memory.rss,
                    process.cpu_percent(),
                    process.memory_percent(),
                    " ".join(process.cmdline()) if process.cmdline() else process.name()
                ]
                list_data.append(data)

            # Apply current sort and reformat for humans
            list_data = sorted(list_data,
                               key=lambda x: x[self._sort],
                               reverse=self._reverse)
            # TODO: handle other types better?
            new_data = [
                ([
                    str(x[0]),
                    x[1],
                    str(x[2]),
                    str(int(x[3] / 1024 / 1024)),
                    str(int(x[4] / 1024 / 1024)),
                    str(round(x[5] * 10, 0) / 10),
                    str(round(x[6] * 10, 0) / 10),
                    x[7]
                ], x[0]) for x in list_data
            ]

            # Update the list and try to reset the last selection.
            self._list.options = new_data
            self._list.value = last_selection

            # TODO: don't like the access to this internal field.
            # TODO: better options for formatting layouts within a text box?
            memory = psutil.virtual_memory()
            self._header._text = (
                "CPU usage: {}%   Memory available: {}M".format(
                        str(round(psutil.cpu_percent() * 10, 0) / 10),
                        str(int(memory.available / 1024 / 1024))))

        # Now redraw as normal
        super(DemoFrame, self)._update(frame_no)

    @property
    def frame_update_count(self):
        # Refresh once a second...
        return 40


def demo(screen):
    screen.play([Scene([DemoFrame(screen)], -1)], stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True)
        sys.exit(0)
    except ResizeScreenError:
        pass
