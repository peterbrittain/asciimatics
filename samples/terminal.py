from asciimatics.widgets import Frame, TextBox, Layout, Divider, Text, Button, Background, Widget
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
from asciimatics.parsers import AnsiTerminalParser
import sys
import subprocess
import threading
import select
import pty
import os
import fcntl
import time


class DemoFrame(Frame):
    def __init__(self, screen):
        super(DemoFrame, self).__init__(screen, screen.height, screen.width)

        # Create the widgets for the demo.
        layout = Layout([1, 18, 1], fill_frame=True)
        self.add_layout(layout)
        self._term_out = TextBox(Widget.FILL_FRAME, line_wrap=True, parser=AnsiTerminalParser())
        layout.add_widget(self._term_out, 1)
        layout.add_widget(Divider(height=2), 1)
        layout2 = Layout([1, 15, 3, 1])
        self.add_layout(layout2)
        self._term_in = Text()
        layout2.add_widget(self._term_in, 1)
        layout2.add_widget(Button("Run", self._run), 2)
        self.fix()
        self.set_theme("monochrome")

        # Open a pseudo TTY to control the interactive session.  Make it non-blocking.
        self._master, slave = pty.openpty()
        fl = fcntl.fcntl(self._master, fcntl.F_GETFL)
        fcntl.fcntl(self._master, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        # Start the shell and thread to pull data from it.
        self._shell = subprocess.Popen(["bash", "-i"], preexec_fn=os.setsid, stdin=slave, stdout=slave, stderr=slave)
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._background)
        self._thread.daemon = True
        self._thread.start()

    def update(self, frame_no):
        # Don't allow background thread to update values mid screen refresh.
        with self._lock:
            super(DemoFrame, self).update(frame_no)

    def _run(self):
        entry = self._term_in.value + "\n"
        os.write(self._master, entry.encode())
        self._term_in.value = ""

    def _background(self):
        while True:
            ready, _, _ = select.select([self._master], [], [])
            for stream in ready:
                value = ""
                while True:
                    try:
                        data = os.read(stream, 102400)
                        data = data.decode("utf8").replace("\r", "")
                        value += data
                    except BlockingIOError:
                        with self._lock:
                            value = "\n".join([x.raw_text for x in self._term_out.value]) + value
                            self._term_out.value = value.split("\n")[-100:]
                            self._screen.force_update()
                        break

def demo(screen, scene):
    screen.play([Scene([
        Background(screen),
        DemoFrame(screen)
    ], -1)], stop_on_resize=True, start_scene=scene, allow_int=True)


if sys.platform != "linux":
    print("This demo only runs on Unix systems.")
    sys.exit(0)
last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
