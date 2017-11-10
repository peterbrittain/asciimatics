# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from datetime import date, time
from time import sleep
from mock import patch
from builtins import chr
import unittest
import sys
from mock.mock import MagicMock
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.exceptions import NextScene, StopApplication, InvalidFields
from asciimatics.scene import Scene
from asciimatics.screen import Screen, Canvas
from asciimatics.widgets import Frame, Layout, Button, Label, TextBox, Text, \
    Divider, RadioButtons, CheckBox, PopUpDialog, ListBox, Widget, MultiColumnListBox, FileBrowser, \
    DatePicker, TimePicker, Background


class TestFrame(Frame):
    def __init__(self, screen, has_border=True, reduce_cpu=False, label_height=1):
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
        self.label = Label("Group 1:", height=label_height)
        layout.add_widget(self.label, 1)
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
                                         data={"selected": "None"},
                                         title="Test Frame 2")
        # Create the form for displaying the list of contacts.
        self._list_view = ListBox(
            Widget.FILL_FRAME,
            init_values,
            name="contacts",
            on_change=self._on_pick,
            on_select=self._on_select)
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
        layout3 = Layout([100])
        self.add_layout(layout3)
        self._info_text = Text(label="Selected:", name="selected")
        self._info_text.disabled = True
        layout3.add_widget(self._info_text)
        self.fix()
        self._on_pick()

    def _on_select(self):
        self._info_text.value = str(self._list_view.value)
        self.save()

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


class TestFrame4(Frame):
    def __init__(self, screen):
        super(TestFrame4, self).__init__(
            screen, screen.height, screen.width, has_border=False, name="My Form")

        # State tracking for callbacks
        self.selected = None
        self.highlighted = None

        # Simple full-page Widget
        layout = Layout([1], fill_frame=True)
        self.add_layout(layout)
        self.file_list = FileBrowser(Widget.FILL_FRAME,
                                     "/",
                                     name="file_list",
                                     on_select=self.select,
                                     on_change=self.change)
        layout.add_widget(self.file_list)
        self.fix()

    def select(self):
        self.selected = self.file_list.value

    def change(self):
        self.highlighted = self.file_list.value


class TestFrame5(Frame):
    def __init__(self, screen):
        super(TestFrame5, self).__init__(
            screen, screen.height, screen.width, has_border=True, name="My Form")

        # Simple full-page Widget
        layout = Layout([1], fill_frame=True)
        self.add_layout(layout)
        self.date_widget = DatePicker(
            label="Date:", name="date", year_range=range(1999, 2020), on_change=self._changed)
        self.date_widget.value = date(2017, 1, 2)
        layout.add_widget(self.date_widget)
        self.time_widget = TimePicker(
            label="Time:", name="time", seconds=True, on_change=self._changed)
        self.time_widget.value = time(12, 0, 59)
        layout.add_widget(self.time_widget)
        self.fix()

        # State tracking for widgets
        self.changed = False

    def _changed(self):
        self.changed = True


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
        self.assertEqual(form.data, {"selected": "None", "contacts": 1})

        # Check that UP/DOWN change selection.
        self.process_keys(form, [Screen.KEY_DOWN])
        form.save()
        self.assertEqual(form.data, {"selected": "None", "contacts": 2})
        self.process_keys(form, [Screen.KEY_UP])
        form.save()
        self.assertEqual(form.data, {"selected": "None", "contacts": 1})

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
            "|--------------------------------------|\n" +
            "| < Add > < Edit > < Delete < Quit >   |\n" +
            "|Selected: None                        |\n" +
            "+--------------------------------------+\n")

        # Check that mouse input changes selection.
        self.process_mouse(form, [(2, 2, MouseEvent.LEFT_CLICK)])
        form.save()
        self.assertEqual(form.data, {"selected": "None", "contacts": 2})
        self.process_mouse(form, [(2, 1, MouseEvent.LEFT_CLICK)])
        form.save()
        self.assertEqual(form.data, {"selected": "None", "contacts": 1})

        # Check that enter key handles correctly.
        self.process_keys(form, [Screen.ctrl("m")])
        form.save()
        self.assertEqual(form.data, {"selected": "1", "contacts": 1})

        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "+------------ Test Frame 2 ------------+\n" +
            "|One                                   |\n" +
            "|Two                                   O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|--------------------------------------|\n" +
            "| < Add > < Edit > < Delete < Quit >   |\n" +
            "|Selected: 1                           |\n" +
            "+--------------------------------------+\n")

        # Check that mouse double click handles correctly.
        self.process_mouse(form, [(2, 2, MouseEvent.DOUBLE_CLICK)])
        form.save()
        self.assertEqual(form.data, {"selected": "2", "contacts": 2})

        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "+------------ Test Frame 2 ------------+\n" +
            "|One                                   |\n" +
            "|Two                                   O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|--------------------------------------|\n" +
            "| < Add > < Edit > < Delete < Quit >   |\n" +
            "|Selected: 2                           |\n" +
            "+--------------------------------------+\n")

        # Check that the current focus ignores unknown events.
        event = object()
        self.assertEqual(event, form.process_event(event))

    def test_title(self):
        """
        Check Frame titles work as expected.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame2(canvas, [("One", 1), ("Two", 2)])
        form.register_scene(scene)
        form.reset()

        # Check that the title is rendered correctly.
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "+------------ Test Frame 2 ------------+\n" +
            "|One                                   |\n" +
            "|Two                                   O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|--------------------------------------|\n" +
            "| < Add > < Edit > < Delete < Quit >   |\n" +
            "|Selected: None                        |\n" +
            "+--------------------------------------+\n")

        # Check that a new title is rendered correctly.
        form.title = "A New Title!"
        form.update(1)
        self.assert_canvas_equals(
            canvas,
            "+------------ A New Title! ------------+\n" +
            "|One                                   |\n" +
            "|Two                                   O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|--------------------------------------|\n" +
            "| < Add > < Edit > < Delete < Quit >   |\n" +
            "|Selected: None                        |\n" +
            "+--------------------------------------+\n")

    def test_focus_callback(self):
        """
        Check that the _on_focus & _on_blur callbacks work as expected.
        """
        def _on_focus():
            self._did_focus = True

        def _on_blur():
            self._did_blur = True

        # Create a dummy screen
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 2, 40, 0, 0)

        # Create the form we want to test.
        form = Frame(canvas, canvas.height, canvas.width, has_border=False)
        layout = Layout([100], fill_frame=True)
        form.add_layout(layout)
        layout.add_widget(Text("Test"))
        layout.add_widget(Text("Test2", on_blur=_on_blur, on_focus=_on_focus))
        form.fix()
        form.register_scene(scene)
        form.reset()

        # Reset state for test
        self._did_blur = False
        self._did_focus = False

        # Tab round to move the focus - check it has called the right function.
        self.process_keys(form, [Screen.KEY_TAB])
        self.assertEqual(self._did_blur, False)
        self.assertEqual(self._did_focus, True)

        # Reset the state and Now move the focus away with the mouse.
        self._did_focus = False
        self.process_mouse(form, [(0, 0, MouseEvent.LEFT_CLICK)])
        self.assertEqual(self._did_blur, True)
        self.assertEqual(self._did_focus, False)

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
        mc_list = MultiColumnListBox(
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
            name="mc_list")
        form.add_layout(layout)
        layout.add_widget(mc_list)
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

        # Check that PGUP/PGDN change selection.
        self.process_keys(form, [Screen.KEY_PAGE_DOWN])
        form.save()
        self.assertEqual(form.data, {"mc_list": 5})
        self.process_keys(form, [Screen.KEY_PAGE_UP])
        form.save()
        self.assertEqual(form.data, {"mc_list": 1})

        # Check that the widget is rendered correctly.
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

        # Check that the start_line can be read and set - and enforces good behaviour
        mc_list.start_line = 0
        self.assertEqual(mc_list.start_line, 0)
        mc_list.start_line = len(mc_list.options) - 1
        self.assertEqual(mc_list.start_line, len(mc_list.options) - 1)
        mc_list.start_line = 10000000
        self.assertEqual(mc_list.start_line, len(mc_list.options) - 1)

        # Check that options can be read and set.
        mc_list.options = [(["a", "b", "c", "d", "e", "f"], 0)]
        self.assertEqual(mc_list.options, [(["a", "b", "c", "d", "e", "f"], 0)])
        mc_list.options = []
        self.assertEqual(mc_list.options, [])

        # Check that the form re-renders correctly afterwards.
        form.update(1)
        self.assert_canvas_equals(
            canvas,
            "A  B      C D      E F                  \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n")

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

    def test_cjk_popup(self):
        """
        Check PopUpDialog widgets work with CJK double-width characters.
        """
        # Apologies to anyone who actually speaks this language!  I just need some double-width
        # glyphs so have re-used the ones from the original bug report.
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = PopUpDialog(canvas, u"你確定嗎？ 你確定嗎？ 你確定嗎？", [u"是", u"否"])
        form.register_scene(scene)
        form.reset()

        # Check that the pop-up is rendered correctly.
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "                                        \n" +
            "                                        \n" +
            "       +------------------------+       \n" +
            "       |你你確確定定嗎嗎？？ 你你確確定定嗎嗎？？   |       \n" +
            "       |你你確確定定嗎嗎？？              O       \n" +
            "       |                        |       \n" +
            "       |   < 是是 >      < 否否 >   |       \n" +
            "       +------------------------+       \n" +
            "                                        \n" +
            "                                        \n")

    def test_cjk_forms(self):
        """
        Check form widgets work with CJK characters.
        """
        # Create a dummy screen.
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 10, 40, 0, 0)

        # Create the form we want to test.
        form = Frame(canvas, canvas.height, canvas.width, has_border=False)
        layout = Layout([100], fill_frame=True)
        mc_list = MultiColumnListBox(
            4,
            [3, 5, 0],
            [
                (["1", "2", "3"], 1),
                ([u"你", u"確", u"定"], 2),
            ],
            titles=[u"你確定嗎？", u"你確定嗎？", u"你確定嗎？"])
        text = Text()
        text_box = TextBox(3)
        form.add_layout(layout)
        layout.add_widget(mc_list)
        layout.add_widget(text)
        layout.add_widget(text_box)
        form.fix()
        form.register_scene(scene)
        form.reset()

        # Set some interesting values...
        text.value = u"你確定嗎？ 你確定嗎？ 你確定嗎？"
        text_box.value = [u"你確定嗎", u"？"]

        # Check that the CJK characters render correctly - no really this is correctly aligned!
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            u"你你 你你確確 你你確確定定嗎嗎？？                      \n" +
            u"1  2    3                               \n" +
            u"你你 確確   定定                              \n" +
            u"                                        \n" +
            u"你你確確定定嗎嗎？？ 你你確確定定嗎嗎？？ 你你確確定定嗎嗎？？        \n" +
            u"你你確確定定嗎嗎                                \n" +
            u"？？                                      \n" +
            u"                                        \n" +
            u"                                        \n" +
            u"                                        \n")

        # Check that mouse input takes into account the glyph width
        self.process_mouse(form, [(5, 4, MouseEvent.LEFT_CLICK)])
        self.process_keys(form, ["b"])
        self.process_mouse(form, [(2, 4, MouseEvent.LEFT_CLICK)])
        self.process_keys(form, ["p"])
        form.save()
        self.assertEqual(text.value, u"你p確b定嗎？ 你確定嗎？ 你確定嗎？")

        self.process_mouse(form, [(2, 5, MouseEvent.LEFT_CLICK)])
        self.process_keys(form, ["p"])
        self.process_mouse(form, [(1, 6, MouseEvent.LEFT_CLICK)])
        self.process_keys(form, ["b"])
        form.save()
        self.assertEqual(text_box.value, [u"你p確定嗎", u"b？"])

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

    def test_label_change(self):
        """
        Check Labels can be dynamically updated.
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

        # Check dynamic updates change the rendering.
        form.label.text = "New text here:"
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "| New text here:                       |\n" +
            "| My First                             O\n" +
            "| Box:                                 |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "| Text1:                               |\n" +
            "| Text2:                               |\n" +
            "+--------------------------------------+\n")

    def test_label_height(self):
        """
        Check Labels can be dynamically updated.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas, label_height=2)
        form.reset()

        # Check Label obeys required height
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "| Group 1:                             |\n" +
            "|                                      O\n" +
            "| My First                             |\n" +
            "| Box:                                 |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "| Text1:                               |\n" +
            "+--------------------------------------+\n")

        # Now check wrapping works too...
        form.label.text = "A longer piece of text that should wrap across multiple lines:"
        form.update(1)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "| A longer piece of text that should   |\n" +
            "| wrap across multiple lines:          O\n" +
            "| My First                             |\n" +
            "| Box:                                 |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "| Text1:                               |\n" +
            "+--------------------------------------+\n")

    @patch("os.path.isdir")
    @patch("os.stat")
    @patch("os.listdir")
    def test_file_browser(self, mock_list, mock_stat, mock_path):
        """
        Check FileBrowser widget works as expected.
        """
        # First we need to mock out the file system calls to have a regressible test
        if sys.platform == "win32":
            self.skipTest("File names wrong for windows")

        mock_list.return_value = ["A Directory", "A File"]
        mock_result = MagicMock()
        mock_result.st_mtime = 0
        mock_result.st_size = 10000
        mock_stat.return_value = mock_result
        mock_path.side_effect = lambda x: "File" not in x

        # Now set up the Frame ready for testing
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame4(canvas)
        form.register_scene(scene)
        form.reset()

        # Check we have a default value for our list.
        form.save()
        self.assertIsNone(form.selected)
        self.assertIsNone(form.highlighted)
        self.assertEqual(form.data, {"file_list": None})

        # Check that the listbox is rendered correctly.
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "/                     Size Last modified\n" +
            "|-+ A Directory               1970-01-01\n" +
            "|-- A File              9K    1970-01-01\n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n")

        # Check that mouse inpput changes selection.
        self.process_mouse(form, [(2, 2, MouseEvent.LEFT_CLICK)])
        form.save()
        self.assertEqual(form.data, {"file_list": "/A File"})
        self.assertEqual(form.highlighted, "/A File")
        self.assertIsNone(form.selected)

        # Check that UP/DOWN change selection.
        self.process_keys(form, [Screen.KEY_UP])
        form.save()
        self.assertEqual(form.data, {"file_list": "/A Directory"})
        self.assertEqual(form.highlighted, "/A Directory")
        self.assertIsNone(form.selected)

        # Check that enter key handles correctly on directories.
        self.process_keys(form, [Screen.ctrl("m")])
        self.assertEqual(form.highlighted, "/A Directory/..")
        self.assertIsNone(form.selected)
        form.update(1)
        self.assert_canvas_equals(
            canvas,
            "/A Directory          Size Last modified\n" +
            "|-+ ..                                  \n" +
            "|-+ A Directory               1970-01-01\n" +
            "|-- A File              9K    1970-01-01\n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n")

        # Check that enter key handles correctly on files.
        self.process_keys(form, [Screen.KEY_DOWN, Screen.KEY_DOWN, Screen.ctrl("m")])
        self.assertEqual(form.highlighted, "/A Directory/A File")
        self.assertEqual(form.selected, "/A Directory/A File")

    def test_date_picker(self):
        """
        Check DatePicker widget works as expected.
        """
        # Now set up the Frame ready for testing
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = Scene([], duration=-1)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame5(canvas)
        scene.add_effect(form)
        scene.reset()

        # Check that the listbox is rendered correctly.
        for effect in scene.effects:
            effect.update(0)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "|Date: 02/Jan/2017                     |\n" +
            "|Time: 12:00:59                        O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

        # Check that enter key brings up edit pop-up
        self.process_keys(scene, [Screen.ctrl("m")])
        self.assertFalse(form.changed)
        for effect in scene.effects:
            effect.update(1)
        self.assert_canvas_equals(
            canvas,
            "+-----|01     2016|--------------------+\n" +
            "|Date:|02/Jan/2017|                    |\n" +
            "|Time:|03 Feb 2018|                    O\n" +
            "|     +-----------+                    |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

        # Check that you can't select an invalid date.
        self.process_keys(scene, ["31", "Feb", Screen.ctrl("m")], separator=Screen.KEY_TAB)
        self.assertFalse(form.changed)
        for effect in scene.effects:
            effect.update(2)
        self.assert_canvas_equals(
            canvas,
            "+-----|30 Jan 2016|--------------------+\n" +
            "|Date:|31/Feb/2017|                    |\n" +
            "|Time:|   Mar 2018|                    O\n" +
            "|     +-----------+                    |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

        # Check that a valid date updates the value - wait one second to allow search to reset.
        sleep(1)
        self.process_keys(scene, ["15", "Jun", Screen.ctrl("m")], separator=Screen.KEY_TAB)
        self.assertTrue(form.changed)
        for effect in scene.effects:
            effect.update(2)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "|Date: 15/Jun/2017                     |\n" +
            "|Time: 12:00:59                        O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")
        self.assertEquals(form.date_widget.value, date(2017, 6, 15))

    def test_time_picker(self):
        """
        Check TimePicker widget works as expected.
        """
        # Now set up the Frame ready for testing
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = Scene([], duration=-1)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame5(canvas)
        scene.add_effect(form)
        scene.reset()

        # Check that the listbox is rendered correctly.
        for effect in scene.effects:
            effect.update(0)
        self.assertFalse(form.changed)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "|Date: 02/Jan/2017                     |\n" +
            "|Time: 12:00:59                        O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

        # Check that enter key brings up edit pop-up
        self.process_keys(scene, [Screen.KEY_DOWN, Screen.ctrl("m")])
        for effect in scene.effects:
            effect.update(1)
        self.assertFalse(form.changed)
        self.assert_canvas_equals(
            canvas,
            "+-----+--------+-----------------------+\n" +
            "|Date:|11    58|17                     |\n" +
            "|Time:|12:00:59|                       O\n" +
            "|     |13 01   |                       |\n" +
            "|     +--------+                       |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

        # Check that we can change the time with cursors keys and mouse selection - and click out
        # to exit.
        self.process_mouse(scene, [(7, 1, MouseEvent.LEFT_CLICK)])
        self.process_keys(scene, [Screen.KEY_TAB, Screen.KEY_DOWN, Screen.KEY_TAB, Screen.KEY_UP])
        self.process_mouse(scene, [(10, 10, MouseEvent.LEFT_CLICK)])
        self.assertTrue(form.changed)
        for effect in scene.effects:
            effect.update(2)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "|Date: 02/Jan/2017                     |\n" +
            "|Time: 11:01:58                        O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")
        self.assertEquals(form.time_widget.value, time(11, 1, 58))

    def test_background(self):
        """
        Check Background widget works as expected.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = Background(canvas, bg=7)
        form.register_scene(scene)
        form.reset()

        # Check that the widget is rendered correctly.
        form.update(0)
        for y in range(canvas.height):
            for x in range(canvas.width):
                char, _, _, bg = canvas.get_from(x, y)
                self.assertEquals(char, ord(" "))
                self.assertEquals(bg, 7)

    def test_find_widget(self):
        """
        Check find_widget works as expected.
        """
        # Set up the Frame ready for testing
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = Scene([], duration=-1)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame5(canvas)
        scene.add_effect(form)
        scene.reset()

        # Can't find a non-existent widget
        self.assertIsNone(form.find_widget("ABLAH"))

        # Can find a defined widget
        self.assertEquals(form.find_widget("date"), form.date_widget)

    def test_password(self):
        """
        Check that we can do password input on Text widgets.
        """
        # Create a dummy screen.
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 2, 40, 0, 0)

        # Create the form we want to test.
        form = Frame(canvas, canvas.height, canvas.width, has_border=False)
        layout = Layout([100], fill_frame=True)
        form.add_layout(layout)
        text = Text("Password", hide_char="*")
        layout.add_widget(text)
        form.fix()
        form.register_scene(scene)
        form.reset()

        # Check that input still saves off values as expected
        self.process_keys(form, ["1234"])
        form.save()
        self.assertEqual(text.value, "1234")

        # Check that it is drawn with the obscuring charav=cter, though.
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "Password ****                           \n" +
            "                                        \n")

if __name__ == '__main__':
    unittest.main()
