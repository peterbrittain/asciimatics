from asciimatics.effects import Julia
from asciimatics.widgets import Frame, TextBox, Layout, Label, Divider, Text, \
    CheckBox, RadioButtons, Button, PopUpDialog
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError
import sys

# Initial data for the form
form_data = {
    "TA": ["Hello world!", "How are you?"],
    "TB": "Value1",
    "TC": "Value2",
    "TD": "Value3",
    "Things": 2,
    "CB": True,
    "CC": False,
}


class DemoFrame(Frame):
    def __init__(self, screen):
        super(DemoFrame, self).__init__(screen,
                                        int(screen.height * 2 // 3),
                                        int(screen.width * 2 // 3))
        layout = Layout([1, 18, 1])
        self.add_layout(layout)
        layout.add_widget(Label("Group 1:"), 1)
        layout.add_widget(TextBox(5, label="My First Box:", name="TA"), 1)
        layout.add_widget(Text(label="Text1:", name="TB"), 1)
        layout.add_widget(Text(label="Text2:", name="TC"), 1)
        layout.add_widget(Text(label="Text3:", name="TD"), 1)
        layout.add_widget(Divider(height=2), 1)
        layout.add_widget(Label("Group 2:"), 1)
        layout.add_widget(RadioButtons([("Option 1", 1),
                                        ("Option 2", 2),
                                        ("Option 3", 3)],
                                       label="A Longer Selection:",
                                       name="Things"), 1)
        layout.add_widget(CheckBox("Field 1",
                                   label="A very silly long name for fields:",
                                   name="CA"), 1)
        layout.add_widget(CheckBox("Field 2", name="CB"), 1)
        layout.add_widget(CheckBox("Field 3", name="CC"), 1)
        layout.add_widget(Divider(height=3), 1)
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("OK", self._ok), 0)
        layout2.add_widget(Button("Cancel", self._cancel), 3)
        self.fix()

    def _ok(self):
        self._scene.add_effect(
            PopUpDialog(self._canvas._screen, "OK pressed", ["OK"]))

    def _cancel(self):
        self._scene.add_effect(
            PopUpDialog(self._canvas._screen, "Cancel pressed", ["OK"]))


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
        Screen.wrapper(demo, catch_interrupt=False)
        sys.exit(0)
    except ResizeScreenError:
        pass
