from asciimatics.effects import Julia
from asciimatics.widgets import Frame, TextBox, Layout, Label, Divider, Text, \
    CheckBox, RadioButtons, Button, PopUpDialog
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
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
                                        int(screen.width * 2 // 3),
                                        data=form_data)
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
        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Reset", self._reset), 0)
        layout2.add_widget(Button("View Data", self._view), 1)
        layout2.add_widget(Button("Quit", self._quit), 2)
        self.fix()

    def _reset(self):
        self.reset()
        raise NextScene()

    def _view(self):
        # Build result of this form and display it.
        self.save()
        message = "Values entered are:\n\n"
        for key, value in self.data.items():
            message += "- {}: {}\n".format(key, value)
        # TODO: Fix up direct access to canvas _screen property
        self._scene.add_effect(
            PopUpDialog(self._canvas._screen, message, ["OK"]))

    def _quit(self):
        # TODO: Fix up direct access to canvas _screen property
        self._scene.add_effect(
            PopUpDialog(self._canvas._screen,
                        "Are you sure?",
                        ["Yes", "No"],
                        on_close=self._quit_on_yes))

    @staticmethod
    def _quit_on_yes(selected):
        # Yes is the first button
        if selected == 0:
            raise StopApplication("User requested exit")

def demo(screen, scene):
    global last_scene
    scenes = []
    effects = [
        Julia(screen),
        DemoFrame(screen)
    ]
    scenes.append(Scene(effects, -1))

    screen.play(scenes, stop_on_resize=True, start_scene=scene)

last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
