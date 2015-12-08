from asciimatics.effects import Julia
from asciimatics.widgets import Frame, TextBox, Layout, Label, Divider, Text, \
    CheckBox, RadioButtons
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import sys


class DemoFrame(Frame):
    def __init__(self, screen):
        super(DemoFrame, self).__init__(screen,
                                        int(screen.height * 2 // 3),
                                        int(screen.width * 2 // 3))
        layout = Layout([1, 18, 1])
        self.add_layout(layout)
        layout.add_widget(Label("Group 1:"), 1)
        layout.add_widget(TextBox("", 5, label="My First Box:", name="TA"), 1)
        layout.add_widget(Text("Value1", label="Text1:", name="TB"), 1)
        layout.add_widget(Text("Value2", label="Text2:", name="TC"), 1)
        layout.add_widget(Text("Value3", label="Text3:", name="TD"), 1)
        layout.add_widget(Divider(height=2), 1)
        layout.add_widget(RadioButtons([("Option 1", 1),
                                        ("Option 2", 2),
                                        ("Option 3", 3)],
                                       label="Selection:", name="Things"), 1)
        layout.add_widget(CheckBox("Field 1:", label="Fields:", name="CA"), 1)
        layout.add_widget(CheckBox("Field 2:", name="CB"), 1)
        layout.add_widget(CheckBox("Field 3:", name="CC"), 1)
        # layout2 = Layout([100])
        # self.add_layout(layout2)
        # layout2.add_widget(Label("Empty!"))
        self.fix()


def demo(screen):
    scenes = []
    effects = [
        Julia(screen),
        DemoFrame(screen)
    ]
    scenes.append(Scene(effects, -1))

    screen.play(scenes, stop_on_resize=True)

while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True)
        sys.exit(0)
    except ResizeScreenError:
        pass
