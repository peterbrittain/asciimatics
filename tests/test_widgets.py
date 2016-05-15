import unittest
from mock.mock import MagicMock
from asciimatics.event import KeyboardEvent
from asciimatics.exceptions import NextScene, StopApplication
from asciimatics.screen import Screen, Canvas
from asciimatics.widgets import Frame, Layout, Button, Label, TextBox, Text, \
    Divider, RadioButtons, CheckBox, PopUpDialog


class TestFrame(Frame):
    def __init__(self, screen, has_border=True):
        super(TestFrame, self).__init__(screen,
                                        screen.height,
                                        screen.width,
                                        name="Test Form",
                                        has_border=has_border)
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
        for key, value in self.data.items():
            if isinstance(value, bool):
                if value:
                    changed = True
                    break
            if isinstance(value, int):
                if value != 1:
                    changed = True
                    break
            elif value is None:
                continue
            elif len(value) != 0:
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

    def assert_canvas_equals(self, canvas, expected):
        """
        Assert output to canvas is as expected.
        """
        output = ""
        for y in range(canvas.height):
            for x in range(canvas.width):
                char, _, _, _ = canvas.get_from(x, y)
                output += chr(char)
            output += "\n"
        self.assertEqual(output, expected)

    @staticmethod
    def process_input(form, values, separator=None):
        """
        Inject a set of values separated by a common key separator.
        """
        for new_value in values:
            if isinstance(new_value, int):
                form.process_event(KeyboardEvent(new_value))
            else:
                for char in new_value:
                    form.process_event(KeyboardEvent(ord(char)))
            if separator:
                form.process_event(KeyboardEvent(separator))

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
        form.reset()
        form.save()
        self.assertEqual(
            form.data,
            {
                'CA': False,
                'CB': False,
                'CC': False,
                'TA': [''],
                'TB': '',
                'TC': '',
                'TD': '',
                'Things': 1
            })

    def test_rendering(self):
        """
        Check Frame renders as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # Check initial rendering
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "| Group 1:                             |\n" +
            "| My First                             O\n" +
            "| Box:                                 |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "| Text1:                               |\n" +
            "| Text2:                               |\n" +
            "+--------------------------------------+\n")

        # Check scrolling works.  Should also test label splitting and ellipsis.
        form.move_to(0, 9, 8)
        form.update(1)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "| Text3:                               |\n" +
            "|                                      |\n" +
            "| ----------------------------------   |\n" +
            "| Group 2:                             O\n" +
            "| A Longer   (X) Option 1              |\n" +
            "| Selection: ( ) Option 2              |\n" +
            "|            ( ) Option 3              |\n" +
            "| A very...  [ ] Field 1               |\n" +
            "+--------------------------------------+\n")

        # Now check button rendering.
        form.move_to(0, 18, 8)
        form.update(2)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "|            [ ] Field 3               |\n" +
            "|                                      |\n" +
            "| ----------------------------------   |\n" +
            "|                                      |\n" +
            "| < Reset >  < View Data > < Quit >    |\n" +
            "|                                      |\n" +
            "|                                      O\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

    def test_no_border(self):
        """
        Check that a Frame with nor border works
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas, has_border=False)
        form.reset()

        # Check initial rendering
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "  Group 1:                              \n" +
            "  My First                              \n" +
            "  Box:                                  \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "  Text1:                                \n" +
            "  Text2:                                \n" +
            "  Text3:                                \n" +
            "                                        \n")

        # Check scrolling works.  Should also test label splitting and ellipsis.
        form.move_to(0, 10, 10)
        form.update(1)
        self.assert_canvas_equals(
            canvas,
            "  ------------------------------------  \n" +
            "  Group 2:                              \n" +
            "  A Longer    (X) Option 1              \n" +
            "  Selection:  ( ) Option 2              \n" +
            "              ( ) Option 3              \n" +
            "  A very si...[ ] Field 1               \n" +
            "              [ ] Field 2               \n" +
            "              [ ] Field 3               \n" +
            "                                        \n" +
            "  ------------------------------------  \n")

    def test_form_input(self):
        """
        Check Frame input works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()
        self.process_input(form,
                           ["ABC\nDEF", "GHI", "jkl", "MN", " ", " ", "", " "],
                           Screen.KEY_TAB)
        form.save()
        self.assertEqual(
            form.data,
            {
                'CA': True,
                'CB': False,
                'CC': True,
                'TA': ['ABC', 'DEF'],
                'TB': 'GHI',
                'TC': 'jkl',
                'TD': 'MN',
                'Things': 1
            })

    def test_textbox_input(self):
        """
        Check TextBox input works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # Check basic movement keys
        self.process_input(form,  ["ABC", Screen.KEY_LEFT, "D"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDC"])
        self.process_input(form,  [Screen.KEY_RIGHT, "E"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDCE"])
        self.process_input(form,  ["\nFGH", Screen.KEY_UP, "I"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICE", "FGH"])
        self.process_input(form,  [Screen.KEY_DOWN, "J"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICE", "FGHJ"])
        self.process_input(form,  [Screen.KEY_HOME, "K"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICE", "KFGHJ"])
        self.process_input(form,  [Screen.KEY_END, "L"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICE", "KFGHJL"])

        # Backspace
        self.process_input(form,  [Screen.KEY_BACK])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICE", "KFGHJ"])

    def test_text_input(self):
        """
        Check Text input works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # Check basic movement keys
        self.process_input(form,  [Screen.KEY_TAB, "ABC"])
        form.save()
        self.assertEqual(form.data["TB"], "ABC")
        self.process_input(form,  [Screen.KEY_HOME, "D"])
        form.save()
        self.assertEqual(form.data["TB"], "DABC")
        self.process_input(form,  [Screen.KEY_END, "E"])
        form.save()
        self.assertEqual(form.data["TB"], "DABCE")
        self.process_input(form,  [Screen.KEY_LEFT, "F"])
        form.save()
        self.assertEqual(form.data["TB"], "DABCFE")
        self.process_input(form,  [Screen.KEY_RIGHT, "G"])
        form.save()
        self.assertEqual(form.data["TB"], "DABCFEG")

        # Backspace
        self.process_input(form,  [Screen.KEY_BACK])
        form.save()
        self.assertEqual(form.data["TB"], "DABCFE")

    def test_checkbox_input(self):
        """
        Check Checkbox input works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # Check basic selection keys
        self.process_input(
            form,
            [Screen.KEY_TAB, Screen.KEY_TAB, Screen.KEY_TAB, Screen.KEY_TAB,
             Screen.KEY_TAB, " "])
        form.save()
        self.assertEqual(form.data["CA"], True)
        self.process_input(form, ["\n"])
        form.save()
        self.assertEqual(form.data["CA"], False)
        self.process_input(form, ["\r"])
        form.save()
        self.assertEqual(form.data["CA"], True)

    def test_radiobutton_input(self):
        """
        Check RadioButton input works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # Check basic selection keys
        self.process_input(
            form,
            [Screen.KEY_TAB, Screen.KEY_TAB, Screen.KEY_TAB, Screen.KEY_TAB])
        form.save()
        self.assertEqual(form.data["Things"], 1)
        self.process_input(form, [Screen.KEY_DOWN])
        form.save()
        self.assertEqual(form.data["Things"], 2)
        self.process_input(form, [Screen.KEY_UP])
        form.save()
        self.assertEqual(form.data["Things"], 1)


if __name__ == '__main__':
    unittest.main()
