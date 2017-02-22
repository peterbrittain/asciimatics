# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from builtins import chr
import unittest
from mock.mock import MagicMock
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.exceptions import NextScene, StopApplication, InvalidFields
from asciimatics.scene import Scene
from asciimatics.screen import Screen, Canvas
from asciimatics.widgets import Frame, Layout, Button, Label, TextBox, Text, \
    Divider, RadioButtons, CheckBox, PopUpDialog, ListBox, Widget, MultiColumnListBox


class TestFrame(Frame):
    def __init__(self, screen, has_border=True, reduce_cpu=False):
        super(TestFrame, self).__init__(screen,
                                        screen.height,
                                        screen.width,
                                        name="Test Form",
                                        has_border=has_border,
                                        hover_focus=True,
                                        reduce_cpu=reduce_cpu)
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
            Text(label="Text2:",
                 name="TC",
                 on_change=self._on_change,
                 validator="^[0-9]*$"), 1)
        layout.add_widget(
            Text(label="Text3:",
                 name="TD",
                 on_change=self._on_change,
                 validator=lambda x: x in ("", "a")), 1)
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
        raise NextScene()

    @staticmethod
    def _quit():
        raise StopApplication("User requested exit")


class TestFrame2(Frame):
    def __init__(self, screen, init_values):
        super(TestFrame2, self).__init__(screen,
                                         screen.height,
                                         screen.width,
                                         title="Test Frame 2")
        # Create the form for displaying the list of contacts.
        self._list_view = ListBox(
            Widget.FILL_FRAME,
            init_values,
            name="contacts",
            on_change=self._on_pick)
        self._edit_button = Button("Edit", self._edit)
        self._delete_button = Button("Delete", self._delete)
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        layout.add_widget(self._list_view)
        layout.add_widget(Divider())
        layout2 = Layout([1, 1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(Button("Add", self._add), 0)
        layout2.add_widget(self._edit_button, 1)
        layout2.add_widget(self._delete_button, 2)
        layout2.add_widget(Button("Quit", self._quit), 3)
        self.fix()
        self._on_pick()

    def _on_pick(self):
        self._edit_button.disabled = self._list_view.value is None
        self._delete_button.disabled = self._list_view.value is None

    @staticmethod
    def _add():
        raise NextScene("Add")

    @staticmethod
    def _edit():
        raise NextScene("Edit")

    @staticmethod
    def _delete():
        raise NextScene("Delete")

    @staticmethod
    def _quit():
        raise StopApplication("User pressed quit")


class TestFrame3(Frame):
    def __init__(self, screen):
        super(TestFrame3, self).__init__(screen, 10, 20,
                                         name="Blank",
                                         has_shadow=True)
        self.fix()


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
    def process_keys(form, values, separator=None):
        """
        Inject a set of key events separated by a common key separator.
        """
        for new_value in values:
            if isinstance(new_value, int):
                form.process_event(KeyboardEvent(new_value))
            else:
                for char in new_value:
                    form.process_event(KeyboardEvent(ord(char)))
            if separator:
                form.process_event(KeyboardEvent(separator))

    @staticmethod
    def process_mouse(form, values):
        """
        Inject a set of mouse events.
        """
        for x, y, buttons in values:
            form.process_event(MouseEvent(x, y, buttons))

    def test_form_data(self):
        """
        Check Frame.data works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
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
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
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

    def test_unicode_rendering(self):
        """
        Check Frame renders as expected for unicode environments.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=True)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # Check initial rendering
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "┌──────────────────────────────────────┐\n" +
            "│ Group 1:                             │\n" +
            "│ My First                             █\n" +
            "│ Box:                                 ░\n" +
            "│                                      ░\n" +
            "│                                      ░\n" +
            "│                                      ░\n" +
            "│ Text1:                               ░\n" +
            "│ Text2:                               │\n" +
            "└──────────────────────────────────────┘\n")

        # Check scrolling works.  Should also test label splitting and ellipsis.
        form.move_to(0, 9, 8)
        form.update(1)
        self.assert_canvas_equals(
            canvas,
            "┌──────────────────────────────────────┐\n" +
            "│ Text3:                               │\n" +
            "│                                      ░\n" +
            "│ ──────────────────────────────────   ░\n" +
            "│ Group 2:                             █\n" +
            "│ A Longer   (•) Option 1              ░\n" +
            "│ Selection: ( ) Option 2              ░\n" +
            "│            ( ) Option 3              ░\n" +
            "│ A very...  [ ] Field 1               │\n" +
            "└──────────────────────────────────────┘\n")

        # Now check button rendering.
        form.move_to(0, 18, 8)
        form.update(2)
        self.assert_canvas_equals(
            canvas,
            "┌──────────────────────────────────────┐\n" +
            "│            [ ] Field 3               │\n" +
            "│                                      ░\n" +
            "│ ──────────────────────────────────   ░\n" +
            "│                                      ░\n" +
            "│ < Reset >  < View Data > < Quit >    ░\n" +
            "│                                      ░\n" +
            "│                                      █\n" +
            "│                                      │\n" +
            "└──────────────────────────────────────┘\n")

    def test_no_border(self):
        """
        Check that a Frame with nor border works
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
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
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()
        self.process_keys(form,
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

        # Check that forms ignore unrecognised events.
        event = object()
        self.assertEqual(event, form.process_event(event))

    def test_textbox_input(self):
        """
        Check TextBox input works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # Check basic movement keys
        self.process_keys(form,  ["ABC", Screen.KEY_LEFT, "D"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDC"])
        self.process_keys(form,  [Screen.KEY_RIGHT, Screen.KEY_RIGHT, "E"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDCE"])
        self.process_keys(form,  ["\nFGH", Screen.KEY_UP, Screen.KEY_UP, "I"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICE", "FGH"])
        self.process_keys(form,  [Screen.KEY_DOWN, Screen.KEY_DOWN, "J"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICE", "FGHJ"])
        self.process_keys(form,  [Screen.KEY_HOME, "K"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICE", "KFGHJ"])
        self.process_keys(form,  [Screen.KEY_END, "L"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICE", "KFGHJL"])

        # Backspace - normal and wrapping lines
        self.process_keys(form,  [Screen.KEY_BACK])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICE", "KFGHJ"])
        self.process_keys(form,  [Screen.KEY_HOME, Screen.KEY_BACK])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICEKFGHJ"])

        # Check cursor line-wrapping
        self.process_keys(form,  ["\n"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICE", "KFGHJ"])
        self.process_keys(form,  [Screen.KEY_LEFT, "M"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICEM", "KFGHJ"])
        self.process_keys(form,  [Screen.KEY_RIGHT, "N"])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICEM", "NKFGHJ"])

        # Delete - normal and wrapping lines and at end of all data.
        self.process_keys(form,  [Screen.KEY_DELETE])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICEM", "NFGHJ"])
        self.process_keys(form,
                          [Screen.KEY_UP, Screen.KEY_END, Screen.KEY_DELETE])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICEMNFGHJ"])
        self.process_keys(form, [Screen.KEY_END, Screen.KEY_DELETE])
        form.save()
        self.assertEqual(form.data["TA"], ["ABDICEMNFGHJ"])

        # Check that the current focus ignores unknown events.
        event = object()
        self.assertEqual(event, form.process_event(event))

    def test_text_input(self):
        """
        Check Text input works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # Check basic movement keys
        self.process_keys(form,  [Screen.KEY_TAB, "ABC"])
        form.save()
        self.assertEqual(form.data["TB"], "ABC")
        self.process_keys(form,  [Screen.KEY_HOME, "D"])
        form.save()
        self.assertEqual(form.data["TB"], "DABC")
        self.process_keys(form,  [Screen.KEY_END, "E"])
        form.save()
        self.assertEqual(form.data["TB"], "DABCE")
        self.process_keys(form,  [Screen.KEY_LEFT, "F"])
        form.save()
        self.assertEqual(form.data["TB"], "DABCFE")
        self.process_keys(form,  [Screen.KEY_RIGHT, "G"])
        form.save()
        self.assertEqual(form.data["TB"], "DABCFEG")

        # Backspace
        self.process_keys(form,  [Screen.KEY_BACK])
        form.save()
        self.assertEqual(form.data["TB"], "DABCFE")

        # Delete - including at end of data
        self.process_keys(form,  [Screen.KEY_DELETE])
        form.save()
        self.assertEqual(form.data["TB"], "DABCFE")
        self.process_keys(form,  [Screen.KEY_HOME, Screen.KEY_DELETE])
        form.save()
        self.assertEqual(form.data["TB"], "ABCFE")

        # Check that the current focus ignores unknown events.
        event = object()
        self.assertEqual(event, form.process_event(event))

    def test_validation(self):
        """
        Check free-form text validation works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # Check that save still works with no validation.
        self.process_keys(form,  [Screen.KEY_TAB, Screen.KEY_TAB, "ABC"])
        form.save()
        self.assertEqual(form.data["TC"], "ABC")

        # Check that enforced validation throws exceptions as needed.
        with self.assertRaises(InvalidFields) as cm:
            form.save(validate=True)
        self.assertEqual(cm.exception.fields, ["TC"])

        # Check valid data doesn't throw anything.
        self.process_keys(form,
                          [Screen.KEY_BACK, Screen.KEY_BACK, Screen.KEY_BACK])
        form.save(validate=True)

        # Check functions work as well as regexp strings.
        self.process_keys(form, [Screen.KEY_TAB, "ABC"])
        with self.assertRaises(InvalidFields) as cm:
            form.save(validate=True)
        self.assertEqual(cm.exception.fields, ["TD"])

    def test_checkbox_input(self):
        """
        Check Checkbox input works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # Check basic selection keys
        self.process_keys(
            form,
            [Screen.KEY_TAB, Screen.KEY_TAB, Screen.KEY_TAB, Screen.KEY_TAB,
             Screen.KEY_TAB, " "])
        form.save()
        self.assertEqual(form.data["CA"], True)
        self.process_keys(form, ["\n"])
        form.save()
        self.assertEqual(form.data["CA"], False)
        self.process_keys(form, ["\r"])
        form.save()
        self.assertEqual(form.data["CA"], True)

        # Check that the current focus ignores unknown events.
        event = object()
        self.assertEqual(event, form.process_event(event))

    def test_radiobutton_input(self):
        """
        Check RadioButton input works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # Check basic selection keys - including limit checking
        self.process_keys(
            form,
            [Screen.KEY_TAB, Screen.KEY_TAB, Screen.KEY_TAB, Screen.KEY_TAB])
        form.save()
        self.assertEqual(form.data["Things"], 1)
        self.process_keys(form, [Screen.KEY_UP])
        form.save()
        self.assertEqual(form.data["Things"], 1)
        self.process_keys(form, [Screen.KEY_DOWN])
        form.save()
        self.assertEqual(form.data["Things"], 2)
        self.process_keys(form, [Screen.KEY_DOWN])
        form.save()
        self.assertEqual(form.data["Things"], 3)
        self.process_keys(form, [Screen.KEY_DOWN])
        form.save()
        self.assertEqual(form.data["Things"], 3)
        self.process_keys(form, [Screen.KEY_UP])
        form.save()
        self.assertEqual(form.data["Things"], 2)

        # Check that the current focus ignores unknown events.
        event = object()
        self.assertEqual(event, form.process_event(event))

    def test_mouse_input(self):
        """
        Check mouse input works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.register_scene(scene)
        form.reset()

        # Check focus moves when clicked on a text or textbox
        self.process_mouse(form, [(29, 7, MouseEvent.LEFT_CLICK)])
        self.assertEqual(form._layouts[form._focus]._live_widget, 2)
        self.process_mouse(form, [(29, 2, MouseEvent.LEFT_CLICK)])
        self.assertEqual(form._layouts[form._focus]._live_widget, 1)

        # Check focus doesn't change on scroll or click outside of widgets
        self.process_mouse(form, [(0, 0, 0)])
        self.assertEqual(form._focus, 0)
        self.assertEqual(form._layouts[form._focus]._live_col, 1)
        self.assertEqual(form._layouts[form._focus]._live_widget, 1)
        self.process_mouse(form, [(39, 7, MouseEvent.LEFT_CLICK)])
        self.assertEqual(form._layouts[form._focus]._live_widget, 1)

        # Check focus moves when clicked on a checkbox or radiobutton
        self.process_mouse(form, [(29, 1, MouseEvent.LEFT_CLICK)])
        self.assertEqual(form._layouts[form._focus]._live_widget, 7)
        # Note that the above changes the Frame start-line.
        self.process_mouse(form, [(29, 5, MouseEvent.LEFT_CLICK)])
        self.assertEqual(form._layouts[form._focus]._live_widget, 9)

        # Check focus moves when hovering over a widget
        self.process_mouse(form, [(39, 7, MouseEvent.LEFT_CLICK), (3, 8, 0)])
        self.assertEqual(form._focus, 1)
        self.assertEqual(form._layouts[form._focus]._live_col, 0)
        self.assertEqual(form._layouts[form._focus]._live_widget, 0)

        # Check button click triggers an event.
        with self.assertRaises(StopApplication):
            self.process_mouse(form, [(30, 8, MouseEvent.LEFT_CLICK)])

        # Check that the current focus ignores unknown events.
        event = object()
        self.assertEqual(event, form.process_event(event))

    def test_widget_navigation(self):
        """
        Check widget tab stops work as expected.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # Check default focus at start is first visible widget
        self.assertEqual(form._focus, 0)
        self.assertEqual(form._layouts[form._focus]._live_col, 1)
        self.assertEqual(form._layouts[form._focus]._live_widget, 1)

        # Check BACK_TAB reverses TAB.
        self.process_keys(form, [Screen.KEY_TAB])
        self.assertEqual(form._layouts[form._focus]._live_widget, 2)
        self.process_keys(form, [Screen.KEY_BACK_TAB])
        self.assertEqual(form._layouts[form._focus]._live_widget, 1)

        # Check BACK_TAB/TAB wraps around the form.
        self.process_keys(form, [Screen.KEY_BACK_TAB])
        self.assertEqual(form._focus, 1)
        self.process_keys(form, [Screen.KEY_TAB])
        self.assertEqual(form._focus, 0)

        # Tab out into text fields and check UP/DOWN keys.
        self.process_keys(form, [Screen.KEY_TAB, Screen.KEY_DOWN])
        self.assertEqual(form._layouts[form._focus]._live_widget, 3)
        self.process_keys(form, [Screen.KEY_UP])
        self.assertEqual(form._layouts[form._focus]._live_widget, 2)

        # Tab out into buttons and check LEFT/RIGHT keys.
        self.process_keys(form, [Screen.KEY_TAB, Screen.KEY_TAB, Screen.KEY_TAB,
                                 Screen.KEY_TAB, Screen.KEY_TAB, Screen.KEY_TAB,
                                 Screen.KEY_TAB])
        self.assertEqual(form._focus, 1)
        self.assertEqual(form._layouts[form._focus]._live_col, 1)
        self.assertEqual(form._layouts[form._focus]._live_widget, 0)

        self.process_keys(form, [Screen.KEY_RIGHT])
        self.assertEqual(form._layouts[form._focus]._live_col, 2)
        self.process_keys(form, [Screen.KEY_LEFT])
        self.assertEqual(form._layouts[form._focus]._live_col, 1)

    def test_list_box(self):
        """
        Check ListBox widget works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame2(canvas, [("One", 1), ("Two", 2)])
        form.register_scene(scene)
        form.reset()

        # Check we have a default value for our list.
        form.save()
        self.assertEqual(form.data, {"contacts": 1})

        # Check that UP/DOWN change selection.
        self.process_keys(form, [Screen.KEY_DOWN])
        form.save()
        self.assertEqual(form.data, {"contacts": 2})
        self.process_keys(form, [Screen.KEY_UP])
        form.save()
        self.assertEqual(form.data, {"contacts": 1})

        # Check that the listbox is rendered correctly.
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "+------------ Test Frame 2 ------------+\n" +
            "|One                                   |\n" +
            "|Two                                   O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|--------------------------------------|\n" +
            "| < Add > < Edit > < Delete < Quit >   |\n" +
            "+--------------------------------------+\n")

        # Check that mouse input changes selection.
        self.process_mouse(form, [(2, 2, MouseEvent.LEFT_CLICK)])
        form.save()
        self.assertEqual(form.data, {"contacts": 2})
        self.process_mouse(form, [(2, 1, MouseEvent.LEFT_CLICK)])
        form.save()
        self.assertEqual(form.data, {"contacts": 1})

        # Check that the current focus ignores unknown events.
        event = object()
        self.assertEqual(event, form.process_event(event))

    def test_multi_column_list_box(self):
        """
        Check MultiColumnListBox works as expected.
        """
        # Create a dummy screen.
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 10, 40, 0, 0)

        # Create the form we want to test.
        form = Frame(canvas, canvas.height, canvas.width, has_border=False)
        layout = Layout([100], fill_frame=True)
        form.add_layout(layout)
        layout.add_widget(MultiColumnListBox(
            Widget.FILL_FRAME,
            [3, "4", ">4", "<4", ">10%", "100%"],
            [
                (["1", "2", "3", "4", "5", "6"], 1),
                (["11", "222", "333", "444", "555", "6"], 2),
                (["111", "2", "3", "4", "5", "6"], 3),
                (["1", "2", "33333", "4", "5", "6"], 4),
                (["1", "2", "3", "4", "5", "6666666666666666666666"], 5),
            ],
            titles=["A", "B", "C", "D", "E", "F"],
            name="mc_list"))
        form.fix()
        form.register_scene(scene)
        form.reset()

        # Check we have a default value for our list.
        form.save()
        self.assertEqual(form.data, {"mc_list": 1})

        # Check that UP/DOWN change selection.
        self.process_keys(form, [Screen.KEY_DOWN])
        form.save()
        self.assertEqual(form.data, {"mc_list": 2})
        self.process_keys(form, [Screen.KEY_UP])
        form.save()
        self.assertEqual(form.data, {"mc_list": 1})

        # Check that the widget is rendered correctly.
        self.maxDiff = None
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "A  B      C D      E F                  \n" +
            "1  2      3 4      5 6                  \n" +
            "11 222  333 444  555 6                  \n" +
            "...2      3 4      5 6                  \n" +
            "1  2   3... 4      5 6                  \n" +
            "1  2      3 4      5 6666666666666666666\n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n")

        # Check that mouse input changes selection.
        self.process_mouse(form, [(2, 2, MouseEvent.LEFT_CLICK)])
        form.save()
        self.assertEqual(form.data, {"mc_list": 2})
        self.process_mouse(form, [(2, 1, MouseEvent.LEFT_CLICK)])
        form.save()
        self.assertEqual(form.data, {"mc_list": 1})

        # Check that the current focus ignores unknown events.
        event = object()
        self.assertEqual(event, form.process_event(event))

    def test_disabled_text(self):
        """
        Check disabled TextBox can be used for pre-formatted output.
        """
        # Create a dummy screen.
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 10, 40, 0, 0)

        # Create the form we want to test.
        form = Frame(canvas, canvas.height, canvas.width, has_border=False)
        layout = Layout([100], fill_frame=True)
        form.add_layout(layout)
        text_box = TextBox(1, as_string=True)
        text_box.disabled = True
        layout.add_widget(text_box)
        form.fix()
        form.register_scene(scene)
        form.reset()

        # Check that input has no effect on the programmed value.
        text_box.value = "A test"
        self.process_keys(form, ["A"])
        form.save()
        self.assertEqual(text_box.value, "A test")

        # Check that we can provide a custom colour.  Since the default palette has no "custom"
        # key, this will throw an exception.
        self.assertEqual(text_box._pick_colours("blah"), form.palette["disabled"])
        with self.assertRaises(KeyError) as cm:
            text_box.custom_colour = "custom"
            text_box._pick_colours("blah")
        self.assertIn("custom", str(cm.exception))

    def test_pop_up_widget(self):
        """
        Check widget tab stops work as expected.
        """
        def test_on_click(selection):
            raise NextScene(str(selection))

        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = PopUpDialog(canvas, "Message", ["Yes", "No"], test_on_click)
        form.register_scene(scene)
        form.reset()

        # Check that the pop-up is rendered correctly.
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "                                        \n" +
            "                                        \n" +
            "          +------------------+          \n" +
            "          |Message           |          \n" +
            "          |                  |          \n" +
            "          | < Yes >  < No >  |          \n" +
            "          +------------------+          \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n")

        # Check that mouse input triggers the close function.
        with self.assertRaises(NextScene):
            self.process_mouse(form, [(14, 5, MouseEvent.LEFT_CLICK)])

        # Check that the pop-up swallows all events.
        event = object()
        self.assertIsNone(form.process_event(event))

    def test_shadow(self):
        """
        Check Frames support shadows.
        """
        def test_on_click(selection):
            raise NextScene(str(selection))

        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 10, 40, 0, 0)
        for y in range(10):
            canvas.print_at("X" * 40, 0, y)
        form = PopUpDialog(
            canvas, "Message", ["Yes", "No"], test_on_click, has_shadow=True)
        form.register_scene(scene)
        form.reset()

        # Check that the pop-up is rendered correctly.
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n" +
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n" +
            "XXXXXXXXXX+------------------+XXXXXXXXXX\n" +
            "XXXXXXXXXX|Message           |XXXXXXXXXX\n" +
            "XXXXXXXXXX|                  |XXXXXXXXXX\n" +
            "XXXXXXXXXX| < Yes >  < No >  |XXXXXXXXXX\n" +
            "XXXXXXXXXX+------------------+XXXXXXXXXX\n" +
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n" +
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n" +
            "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\n")

    def test_clone(self):
        """
        Check Frame cloning works.
        """
        def test_on_click(selection):
            raise NextScene(str(selection))

        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        scene2 = Scene([], 10)
        canvas = Canvas(screen, 10, 40, 0, 0)

        # Check that pop-up dialogs get copied to the new Scene
        form = PopUpDialog(
            canvas, "Message", ["Yes", "No"], test_on_click, has_shadow=True)
        form.register_scene(scene)
        form.clone(canvas, scene2)
        self.assertEqual(len(scene2.effects), 1)
        self.assertEqual(scene2.effects[0]._text, "Message")
        self.assertEqual(scene2.effects[0]._buttons, ["Yes", "No"])

        # Check that normal Frame data gets copied to the new Scene.
        frame = TestFrame(canvas)
        frame2 = TestFrame(canvas)
        scene2 = Scene([frame2], 10)
        frame.register_scene(scene)
        frame2.register_scene(scene)
        frame.data = {"TA": "something"}
        frame2.data = {}

        self.assertEqual(frame2.data, {})
        self.assertNotEqual(frame2.data, frame.data)
        frame.clone(canvas, scene2)
        self.assertEqual(frame2.data, frame.data)

    def test_frame_rate(self):
        """
        Check Frame rate limiting works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # With no special CPU consideration, and a cursor to animate, there
        # should be a 5 frame pause.
        self.assertEqual(form.reduce_cpu, False)
        self.assertEqual(form.frame_update_count, 5)

        # Shift focus away from a text input (to get no cursor animation).
        self.process_keys(form, [Screen.KEY_BACK_TAB])

        # With no special CPU consideration, and no cursors to animate, there
        # should be a (very!) long pause.
        self.assertEqual(form.reduce_cpu, False)
        self.assertEqual(form.frame_update_count, 1000000)

    def test_cpu_saving(self):
        """
        Check Frame rate limiting is even more extreme when in cpu saving mode.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas, reduce_cpu=True)
        form.reset()

        # In this mode, it shouldn't matter where we are on the Frame - all
        # widgets will basically say they don't need animation.
        self.assertEqual(form.reduce_cpu, True)
        self.assertEqual(form.frame_update_count, 1000000)

        # Shift focus away from a text input, just to be sure.
        self.process_keys(form, [Screen.KEY_BACK_TAB])
        self.assertEqual(form.frame_update_count, 1000000)

    def test_stop_frame(self):
        """
        Check Frames always request no end to the Scene.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas, reduce_cpu=True)
        self.assertEqual(form.stop_frame, -1)

    def test_empty_frame(self):
        """
        Check empty Frames still work.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        canvas = Canvas(screen, 10, 40, 0, 0)
        scene = MagicMock(spec=Scene)
        form = TestFrame3(canvas)
        form.register_scene(scene)
        form.reset()

        # Check all keyboard events get swallowed
        self.assertIsNone(form.process_event(KeyboardEvent(ord("A"))))

        # Check Mouse events over the Frame are swallowed and others allowed
        # to bubble down the input stack.
        self.assertIsNone(
            form.process_event(MouseEvent(20, 5, MouseEvent.LEFT_CLICK)))
        self.assertIsNotNone(
            form.process_event(MouseEvent(5, 5, MouseEvent.LEFT_CLICK)))

        # Check form data is empty.
        form.save()
        self.assertEqual(form.data, {})

if __name__ == '__main__':
    unittest.main()
