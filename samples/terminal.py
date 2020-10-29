#!/usr/bin/env python3
from asciimatics.widgets import Frame, Layout, Widget
from asciimatics.effects import Background
from asciimatics.scene import Scene
from asciimatics.screen import Screen, Canvas
from asciimatics.exceptions import ResizeScreenError
from asciimatics.parsers import AnsiTerminalParser, Parser
from asciimatics.event import KeyboardEvent
import sys
import subprocess
import threading
import logging
try:
    import select
    import pty
    import os
    import fcntl
    import curses
    import struct
    import termios
except Exception:
    print("This demo only runs on Unix systems.")
    sys.exit(0)


logging.basicConfig(filename="term.log", level=logging.ERROR)


class Terminal(Widget):
    """
    Widget to handle ansi terminals running a bash shell.
    """
    def __init__(self, name, height):
        super(Terminal, self).__init__(name)
        self._required_height = height
        self._parser = AnsiTerminalParser()
        self._canvas = None
        self._current_colours = None
        self._cursor_x, self._cursor_y = 0, 0
        self._show_cursor = True

        # Supported key mappings
        self._map = {}
        for k, v in [
            (Screen.KEY_LEFT, "kcub1"),
            (Screen.KEY_RIGHT, "kcuf1"),
            (Screen.KEY_UP, "kcuu1"),
            (Screen.KEY_DOWN, "kcud1"),
            (Screen.KEY_HOME, "khome"),
            (Screen.KEY_END, "kend"),
            (Screen.KEY_DELETE, "kdch1"),
            (Screen.KEY_BACK, "kbs"),
        ]:
            self._map[k] = curses.tigetstr(v)
        self._map[Screen.KEY_TAB] = "\t".encode()

        # Open a pseudo TTY to control the interactive session.  Make it non-blocking.
        self._master, self._slave = pty.openpty()
        fl = fcntl.fcntl(self._master, fcntl.F_GETFL)
        fcntl.fcntl(self._master, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        # Start the shell and thread to pull data from it.
        self._shell = subprocess.Popen(
            ["bash", "-i"], preexec_fn=os.setsid, stdin=self._slave, stdout=self._slave, stderr=self._slave)
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._background)
        self._thread.daemon = True
        self._thread.start()

    def set_layout(self, x, y, offset, w, h):
        """
        Resize the widget (and underlying TTY) to the required size.
        """
        super(Terminal, self).set_layout(x, y, offset, w, h)
        self._canvas = Canvas(self._frame.canvas, h, w, x=x, y=y)
        winsize = struct.pack("HHHH", h, w, 0, 0)
        fcntl.ioctl(self._slave, termios.TIOCSWINSZ, winsize)

    def update(self, frame_no):
        """
        Draw the current terminal content to screen.
        """
        # Don't allow background thread to update values mid screen refresh.
        with self._lock:
            # Push current terminal output to screen.
            self._canvas.refresh()

            # Draw cursor if needed.
            if frame_no % 10 < 5 and self._show_cursor:
                origin = self._canvas.origin
                x = self._cursor_x + origin[0]
                y = self._cursor_y + origin[1] - self._canvas.start_line
                details = self._canvas.get_from(self._cursor_x, self._cursor_y)
                if details:
                    char, colour, attr, bg = details
                    attr |= Screen.A_REVERSE
                    self._frame.canvas.print_at(chr(char), x, y, colour, attr, bg)

    def process_event(self, event):
        """
        Pass any recognised input on to the TTY.
        """
        if isinstance(event, KeyboardEvent):
            if event.key_code > 0:
                os.write(self._master, chr(event.key_code).encode())
                return
            elif event.key_code in self._map:
                os.write(self._master, self._map[event.key_code])
                return
        return event

    def _add_stream(self, value):
        """
        Process any output from the TTY.
        """
        lines = value.split("\n")
        for i, line in enumerate(lines):
            self._parser.reset(line, self._current_colours)
            for offset, command, params in self._parser.parse():
                if command == Parser.DISPLAY_TEXT:
                    # Just display the text...  allowing for line wrapping.
                    if self._cursor_x + len(params) > self._w:
                        part_1 = params[:self._w - self._cursor_x]
                        part_2 = params[self._w - self._cursor_x:]
                        self._print_at(part_1, self._cursor_x, self._cursor_y)
                        self._print_at(part_2, 0, self._cursor_y + 1)
                        self._cursor_x = len(part_2)
                        self._cursor_y += 1
                        if self._cursor_y - self._canvas.start_line >= self._h:
                            self._canvas.scroll()
                    else:
                        self._print_at(params, self._cursor_x, self._cursor_y)
                        self._cursor_x += len(params)
                elif command == Parser.CHANGE_COLOURS:
                    # Change current text colours.
                    self._current_colours = params
                elif command == Parser.NEXT_TAB:
                    # Move to next tab stop - hard-coded to default of 8 characters.
                    self._cursor_x = (self._cursor_x // 8) * 8 + 8
                elif command == Parser.MOVE_RELATIVE:
                    # Move cursor relative to current position.
                    self._cursor_x += params[0]
                    self._cursor_y += params[1]
                elif command == Parser.MOVE_ABSOLUTE:
                    # Move cursor relative to specified absolute position.
                    if params[0] is not None:
                        self._cursor_x = params[0]
                    if params[1] is not None:
                        self._cursor_y = params[1] + self._canvas.start_line
                elif command == Parser.DELETE_LINE:
                    # Delete some/all of the current line.
                    if params == 0:
                        self._print_at(" " * (self._w - self._cursor_x), self._cursor_x, self._cursor_y)
                    elif params == 1:
                        self._print_at(" " * self._cursor_x, 0, self._cursor_y)
                    elif params == 2:
                        self._print_at(" " * self._w, 0, self._cursor_y)
                elif command == Parser.DELETE_CHARS:
                    # Delete n characters under the cursor.
                    for x in range(self._cursor_x, self._w):
                        if x + params < self._w:
                            cell = self._canvas.get_from(x + params, self._cursor_y)
                        else:
                            cell = (ord(" "),
                                    self._current_colours[0],
                                    self._current_colours[1],
                                    self._current_colours[2])
                        self._canvas.print_at(
                            chr(cell[0]), x, self._cursor_y, colour=cell[1], attr=cell[2], bg=cell[3])
                elif command == Parser.SHOW_CURSOR:
                    # Show/hide the cursor.
                    self._show_cursor = params
                elif command == Parser.CLEAR_SCREEN:
                    # Clear the screen.
                    self._canvas.clear_buffer(
                        self._current_colours[0], self._current_colours[1], self._current_colours[2])
            # Move to next line, scrolling buffer as needed.
            if i != len(lines) - 1:
                self._cursor_x = 0
                self._cursor_y += 1
                if self._cursor_y - self._canvas.start_line >= self._h:
                    self._canvas.scroll()

    def _print_at(self, text, x, y):
        """
        Helper function to simplify use of the canvas.
        """
        self._canvas.print_at(
            text,
            x, y,
            colour=self._current_colours[0], attr=self._current_colours[1], bg=self._current_colours[2])

    def _background(self):
        """
        Backround thread running the IO between the widget and the TTY session.
        """
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
                            self._add_stream(value)
                            self._frame.screen.force_update()
                        break

    def reset(self):
        """
        Reset the widget to a blank screen.
        """
        self._canvas = Canvas(self._frame.canvas, self._h, self._w, x=self._x, y=self._y)
        self._cursor_x, self._cursor_y = 0, 0
        self._current_colours = (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)

    def required_height(self, offset, width):
        """
        Required height for the terminal.
        """
        return self._required_height

    @property
    def frame_update_count(self):
        """
        Frame update rate required.
        """
        # Force refresh for cursor.
        return 5

    @property
    def value(self):
        """
        Terminal value - not needed for demo.
        """
        return

    @value.setter
    def value(self, new_value):
        return


class DemoFrame(Frame):
    def __init__(self, screen):
        super(DemoFrame, self).__init__(screen, screen.height, screen.width)

        # Create the widgets for the demo.
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(Terminal("term", Widget.FILL_FRAME))
        self.fix()
        self.set_theme("monochrome")


def demo(screen, scene):
    screen.play([
        Scene([
            Background(screen),
            DemoFrame(screen)
        ], -1)
    ], stop_on_resize=True, start_scene=scene, allow_int=True)


last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
