import unittest
from mock.mock import MagicMock
from asciimatics.exceptions import NextScene, StopApplication
from asciimatics.screen import Screen, Canvas
from asciimatics.widgets import Frame, Layout, Button, Label, TextBox, Text, \
    Divider, RadioButtons, CheckBox, PopUpDialog


class TestFrame(Frame):
    def __init__(self, screen):
        super(TestFrame, self).__init__(screen, 10, 20, name="Test Form")
        layout = Layout([1, 18, 1])
        self.add_layout(layout)
        self._reset_button = Button("Reset", self._reset)
        layout.add_widget(Label("Group 1:"), 1)
        layout.add_widget(TextBox(5,
                                  label="My First Box:",
                                  name="TA",
                                  on_change=self._on_change), 1)
        layout.add_widget(
            Text(label="Text1:", name="TB", on_change=self._on_change), 1)
        layout.add_widget(
            Text(label="Text2:", name="TC", on_change=self._on_change), 1)
        layout.add_widget(
            Text(label="Text3:", name="TD", on_change=self._on_change), 1)
        layout.add_widget(Divider(height=2), 1)
        layout.add_widget(Label("Group 2:"), 1)
        layout.add_widget(RadioButtons([("Option 1", 1),
                                        ("Option 2", 2),
                                        ("Option 3", 3)],
                                       label="A Longer Selection:",
                                       name="Things",
                                       on_change=self._on_change), 1)
        layout.add_widget(CheckBox("Field 1",
                                   label="A very silly long name for fields:",
                                   name="CA",
                                   on_change=self._on_change), 1)
        layout.add_widget(
            CheckBox("Field 2", name="CB", on_change=self._on_change), 1)
        layout.add_widget(
            CheckBox("Field 3", name="CC", on_change=self._on_change), 1)
        layout.add_widget(Divider(height=3), 1)
        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(self._reset_button, 0)
        layout2.add_widget(Button("View Data", self._view), 1)
        layout2.add_widget(Button("Quit", self._quit), 2)
        self.fix()

    def _on_change(self):
        changed = False
        self.save()
        for _, value in self.data.items():
            if len(value) != 0:
                changed = True
                break
        self._reset_button.disabled = not changed

    def _reset(self):
        self.reset()
        raise NextScene()

    def _view(self):
        # Build result of this form and display it.
        self.save()
        message = "Values entered are:\n\n"
        for key, value in self.data.items():
            message += "- {}: {}\n".format(key, value)
        self._scene.add_effect(
            PopUpDialog(self._screen, message, ["OK"]))

    @staticmethod
    def _quit(self):
        raise StopApplication("User requested exit")


class TestWidgets(unittest.TestCase):
    def test_form_data(self):
        """
        Check Frame.data works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)

        # Should be empty on construction
        self.assertEqual(form.data, {})

        # Should be blank values after saving.
        form.save()
        self.assertEqual(
            form.data,
            {
                'CA': None,
                'CB': None,
                'CC': None,
                'TA': [''],
                'TB': None,
                'TC': None,
                'TD': None,
                'Things': None
            })

if __name__ == '__main__':
    unittest.main()
