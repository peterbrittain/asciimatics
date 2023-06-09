#!/usr/bin/env python3

from asciimatics.widgets import Frame, Layout, Label, Divider, Button, ReadBox
from asciimatics.effects import Background
from asciimatics.event import MouseEvent
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication, InvalidFields
from asciimatics.parsers import AsciimaticsParser
import sys
import re
import datetime
import logging

# Test data
tree = r"""
       ${3,1}*
${2}      / \
${2}     /${1}o${2}  \
${2}    /_   _\ ${1}
This is the first wrapping line, wrap wrap wrap, and then wrap some more.  These are the Daves I know I know, these are the Daves I know
123456789 123456789 123456789 123456789 123456789abcdefgh
${2}     /   \${4}b
${2}    /     \
${2}   /   ${1}o${2}   \
${2}  /__     __\
  ${1}d${2} / ${4}o${2}   \
${2}   /       \
${2}  / ${4}o     ${1}o${2}.\
${2} /___________\
      ${3}|||
      ${3}|||

This is a very long line that goes on and on, it might wrap for you
""".split("\n")

# Initial data for the form
form_data = {
    "TA": tree,
}

logging.basicConfig(filename="debug.log", level=logging.DEBUG)


class DemoFrame(Frame):
    def __init__(self, screen):
        super(DemoFrame, self).__init__(screen,
                                        int(screen.height * 2 // 3),
                                        int(screen.width * 2 // 3),
                                        data=form_data,
                                        has_shadow=True,
                                        name="My Form")
        layout = Layout([1, 18, 1])
        self.add_layout(layout)
        layout.add_widget(Label("Thing"), 1)

        layout.add_widget(ReadBox(15,
                                  label="ReadBox:",
                                  name="TA",
                                  parser=AsciimaticsParser(),
                                  line_wrap=True), 1)
        layout.add_widget(Divider(height=3), 1)

        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Quit", self._quit), 2)
        self.fix()

    def _quit(self):
        raise StopApplication("User requested exit")


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
