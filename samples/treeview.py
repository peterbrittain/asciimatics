from datetime import date, datetime
from asciimatics.event import KeyboardEvent
from asciimatics.widgets import Frame, Layout, MultiColumnListBox, Widget, Label, PopUpDialog
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication
import sys
import os


# Global state for the application
# TODO: Figure out how to remember this across resize when actually a widget...
root_dir = os.path.abspath(".")


# TODO: Consider exposing these and others in utilities?
def readable_mem(mem):
    for suffix in ["", "K", "M", "G", "T"]:
        if mem < 10000:
            return "{}{}".format(int(mem), suffix)
        mem /= 1024
    return "{}P".format(int(mem))


def readable_timestamp(stamp):
    if date.fromtimestamp(stamp) == date.today():
        return str(datetime.fromtimestamp(stamp).strftime("%I:%M:%S%p"))
    else:
        return str(date.fromtimestamp(stamp))


class DemoFrame(Frame):
    def __init__(self, screen):
        super(DemoFrame, self).__init__(screen,
                                        screen.height,
                                        screen.width,
                                        has_border=False,
                                        name="My Form")
        # Internal state required for doing periodic updates
        self._last_frame = 0
        self._root = root_dir

        # Create the basic form layout...
        layout = Layout([1], fill_frame=True)
        # TODO: Create a new widget for the file viewer?
        self._list = MultiColumnListBox(
            Widget.FILL_FRAME,
            [0, ">8", ">14"],
            [],
            titles=["Filename", "Size", "Last modified"],
            name="mc_list",
            on_select=self.on_select)
        self.add_layout(layout)
        layout.add_widget(Label("Local disk browser"))
        layout.add_widget(self._list)
        layout.add_widget(Label("Press `q` to quit."))
        self.fix()
        self._populate_list()

    def on_select(self):
        global root_dir
        # Update the list data as needed.
        if self._list.value and os.path.isdir(self._list.value):
            self._root = root_dir = self._list.value
            self._populate_list()
        else:
            self._scene.add_effect(
                PopUpDialog(self._screen, "You selected: {}".format(self._list.value), ["OK"]))

        # Force a refresh for improved responsiveness
        self._last_frame = 0

    def process_event(self, event):
        # Do the key handling for this Frame.
        if isinstance(event, KeyboardEvent):
            if event.key_code in [ord('q'), ord('Q'), Screen.ctrl("c")]:
                raise StopApplication("User quit")

        # Now pass on to lower levels for normal handling of the event.
        return super(DemoFrame, self).process_event(event)

    def _populate_list(self):
        last_selection = self._list.value
        last_start = self._list.start_line

        tree_view = []
        # The absolute expansion of "/" or "\" is the root of the disk, so is a cross-platform
        # way of spotting when to insert ".." or not.
        if len(self._root) > len(os.path.abspath(os.sep)):
            tree_view.append((["|-+ .."], os.path.abspath(os.path.join(self._root, ".."))))
        tree_dirs = []
        tree_files = []
        files = os.listdir(self._root)
        for file in files:
            full_path = os.path.join(self._root, file)
            details = os.stat(full_path)
            if os.path.isdir(full_path):
                tree_dirs.append((["|-+ {}".format(file),
                                   "",
                                   readable_timestamp(details.st_mtime)], full_path))
            else:
                tree_files.append((["|-- {}".format(file),
                                    readable_mem(details.st_size),
                                    readable_timestamp(details.st_mtime)], full_path))

        tree_view.extend(sorted(tree_dirs))
        tree_view.extend(sorted(tree_files))

        self._list.options = tree_view
        self._list.value = last_selection
        self._list.start_line = last_start
        self._list._titles[0] = self._root


def demo(screen, old_scene):
    screen.play([Scene([DemoFrame(screen)], -1)], stop_on_resize=True, start_scene=old_scene)

last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
