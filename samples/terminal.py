from asciimatics.widgets import Frame, TextBox, Layout, Background, Widget
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
from asciimatics.parsers import AnsiTerminalParser
from asciimatics.event import KeyboardEvent
import sys
import subprocess
import threading
try:
    import select
    import pty
    import os
    import fcntl
    import curses
except Exception:
    print("This demo only runs on Unix systems.")
    sys.exit(0)


class Terminal(TextBox):
    def __init__(self, height):
        super(Terminal, self).__init__(height, line_wrap=True, parser=AnsiTerminalParser())

        #Key definitions
        self._map = {}
        for k, v in [
            (Screen.KEY_LEFT, "kcub1"),
            (Screen.KEY_RIGHT, "kcuf1"),
            (Screen.KEY_UP, "kcuu1"),
            (Screen.KEY_DOWN, "kcud1"),
            (Screen.KEY_HOME, "khome"),
            (Screen.KEY_END, "kend"),
            (Screen.KEY_BACK, "kbs"),
        ]:
            self._map[k] = curses.tigetstr(v)
        self._map[Screen.KEY_TAB] = "\t".encode()

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
            super(Terminal, self).update(frame_no)

    def process_event(self, event):
        if isinstance(event, KeyboardEvent):
            if event.key_code > 0:
                os.write(self._master, chr(event.key_code).encode())
                return
            elif event.key_code in self._map:
                os.write(self._master, self._map[event.key_code])
                return
        return event

    def _background(self):
        while True:
            ready, _, _ = select.select([self._master], [], [])
            for stream in ready:
                value = ""
                while True:
                    try:
                        data = os.read(stream, 102400)
                        data = data.decode("utf8", "replace")
                        value += data
                    # Python 2 and 3 raise different exceptions when they would block
                    except Exception:
                        with self._lock:
                            value = value.split("\n")
                            if len(self.value) > 0:
                                value = self.value[:-1] + ["".join([self.value[-1].raw_text, value[0]])] + value[1:]
                            self.value = value[-self._h:]
                            cursor = self.value[-1:][0]._cursor
                            if cursor > 0:
                                self._column -= cursor
                            self._frame.screen.force_update()
                        break

class DemoFrame(Frame):
    def __init__(self, screen):
        super(DemoFrame, self).__init__(screen, screen.height, screen.width)

        # Create the widgets for the demo.
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(Terminal(Widget.FILL_FRAME))
        self.fix()
        self.set_theme("monochrome")

def demo(screen, scene):
    screen.play([Scene([
        Background(screen),
        DemoFrame(screen)
    ], -1)], stop_on_resize=True, start_scene=scene, allow_int=True)


last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
