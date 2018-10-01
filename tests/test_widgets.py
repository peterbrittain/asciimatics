# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from datetime import date, time
from time import sleep
from mock import patch
from builtins import chr
from builtins import str
import unittest
import sys
from mock.mock import MagicMock
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.exceptions import NextScene, StopApplication, InvalidFields
from asciimatics.scene import Scene
from asciimatics.screen import Screen, Canvas
from asciimatics.widgets import Frame, Layout, Button, Label, TextBox, Text, \
    Divider, RadioButtons, CheckBox, PopUpDialog, ListBox, Widget, MultiColumnListBox, \
    FileBrowser, DatePicker, TimePicker, Background, DropdownList, PopupMenu, \
    _find_min_start, VerticalDivider


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
        layout.add_widget(Divider(line_char="#"))
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
    def setUp(self):
        self.maxDiff = None

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
        Check that a Frame with no border works
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

        # Check that page up/down work as expected.
        self.process_keys(form,  [Screen.ctrl("m"), Screen.ctrl("m"), Screen.KEY_PAGE_UP, "O"])
        form.save()
        self.assertEqual(form.data["TA"], ["OABDICEMNFGHJ", "", ""])
        self.process_keys(form,  [Screen.KEY_PAGE_DOWN, "P"])
        form.save()
        self.assertEqual(form.data["TA"], ["OABDICEMNFGHJ", "", "P"])

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


    def test_frame_focus_widget_property(self):
        """
        Check the frame exposes the focussed widget
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # If the Frame loses the focus it must not return a focussed widget.
        form._has_focus = False
        self.assertIsNone(form.focussed_widget)

    def test_frame_focus_widget_property_when_frame_focussed(self):
        """
        check the frame exposes nothing when frame is foccused
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = TestFrame(canvas)
        form.reset()

        # A Frame with a valid focus should return the widget in focus.
        layout = form._layouts[form._focus]
        layout._has_focus = True
        form._has_focus = True
        self.assertEqual(layout._columns[layout._live_col][layout._live_widget],
                         form.focussed_widget)

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
        form = TestFrame2(
            canvas, [("One", 1), ("Two is now quite a bit longer than before", 2)])
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
            "|Two is now quite a bit longer than ...O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|######################################|\n" +
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
            "|Two is now quite a bit longer than ...O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|######################################|\n" +
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
            "|Two is now quite a bit longer than ...O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|######################################|\n" +
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
            "|######################################|\n" +
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
            "|######################################|\n" +
            "| < Add > < Edit > < Delete < Quit >   |\n" +
            "|Selected: None                        |\n" +
            "+--------------------------------------+\n")

        # Note that the actual stored title includes spaces for margins
        self.assertEqual(form.title, " A New Title! ")

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
            "1112      3 4      5 6                  \n" +
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

        # Also check the value is returned as set
        self.assertEqual(text_box.custom_colour, "custom")

    def test_line_flow(self):
        """
        Check TextBox line-flow editing works as expected.
        """
        # Create a dummy screen.
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 10, 40, 0, 0)

        # Create the form we want to test.
        form = Frame(canvas, canvas.height, canvas.width, has_border=False)
        layout = Layout([100], fill_frame=True)
        form.add_layout(layout)
        text_box = TextBox(5, as_string=True, line_wrap=True)
        layout.add_widget(text_box)
        form.fix()
        form.register_scene(scene)
        form.reset()

        # start with some text that will wrap and check display works.
        text_box.value = "A\nSome very long text that will wrap across multiple lines\nB\n"

        # Check that the pop-up is rendered correctly.
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "A                                       \n" +
            "Some very long text that will wrap acros\n" +
            "s multiple lines                        \n" +
            "B                                       \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n")

        # Check keyboard logic still works and display reflows on demand.
        self.process_mouse(form, [(0, 0, MouseEvent.LEFT_CLICK)])
        self.process_keys(form, [Screen.KEY_DOWN, "A", Screen.KEY_END, "B"])
        form.update(1)
        self.assert_canvas_equals(
            canvas,
            "A                                       \n" +
            "ASome very long text that will wrap acro\n" +
            "ss multiple linesB                      \n" +
            "B                                       \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n")
        self.assertEqual(text_box.value,
                         "A\nASome very long text that will wrap across multiple linesB\nB\n")

        # Check mouse logic still works.
        self.process_mouse(form, [(0, 2, MouseEvent.LEFT_CLICK)])
        self.process_keys(form, ["Z"])
        self.process_mouse(form, [(3, 3, MouseEvent.LEFT_CLICK)])
        self.process_keys(form, ["Y"])
        form.update(1)
        self.assertEqual(text_box.value,
                         "A\nASome very long text that will wrap acroZss multiple linesB\nBY\n")

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
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=True)
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
            "       ┌────────────────────────┐       \n" +
            "       │你你確確定定嗎嗎？？ 你你確確定定嗎嗎？？   │       \n" +
            "       │你你確確定定嗎嗎？？              █       \n" +
            "       │                        ░       \n" +
            "       │   < 是是 >      < 否否 >   │       \n" +
            "       └────────────────────────┘       \n" +
            "                                        \n" +
            "                                        \n")

    def test_cjk_forms(self):
        """
        Check form widgets work with CJK characters.
        """
        # Create a dummy screen.
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=True)
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
        self.assertEqual(form.label.text, "New text here:")

        # And check that values are unaffected (and still not set).
        self.assertEqual(form.label.value, None)

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

    def test_label_alignment(self):
        """
        Check Label alignment works.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = Scene([], duration=-1)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = Frame(canvas, canvas.height, canvas.width)
        layout = Layout([1])
        form.add_layout(layout)
        layout.add_widget(Label("Left", align="<"))
        layout.add_widget(Label("Middle", align="^"))
        layout.add_widget(Label("Right", align=">"))
        form.fix()
        form.register_scene(scene)
        scene.add_effect(form)
        scene.reset()

        # Check that the frame is rendered correctly.
        for effect in scene.effects:
            effect.update(0)

        # Check Label obeys required height
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "|Left                                  |\n" +
            "|                Middle                O\n" +
            "|                                 Right|\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

    @patch("os.path.exists")
    @patch("os.path.realpath")
    @patch("os.path.islink")
    @patch("os.path.isdir")
    @patch("os.lstat")
    @patch("os.stat")
    @patch("os.listdir")
    def test_file_browser(self, mock_list, mock_stat, mock_lstat, mock_dir, mock_link, \
                          mock_real_path, mock_exists):
        """
        Check FileBrowser widget works as expected.
        """
        # First we need to mock out the file system calls to have a regressible test
        if sys.platform == "win32":
            self.skipTest("File names wrong for windows")

        mock_list.return_value = ["A Directory", "A File", "A Lnk", str(b"oo\xcc\x88o\xcc\x88O\xcc\x88.txt", 'utf-8')]
        mock_result = MagicMock()
        mock_result.st_mtime = 0
        mock_result.st_size = 10000
        mock_stat.return_value = mock_result
        mock_lstat.return_value = mock_result
        mock_dir.side_effect = lambda x: x.endswith("Directory")
        mock_link.side_effect = lambda x: "Lnk" in x
        mock_real_path.return_value = "A Tgt"
        mock_exists.return_value = True

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

        # Check that the Frame is rendered correctly.
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "/                     Size Last modified\n" +
            "|-+ A Directory         9K    1970-01-01\n" +
            "|-- A File              9K    1970-01-01\n" +
            "|-- A Lnk -> A Tgt      9K    1970-01-01\n" +
            "|-- oööÖ.txt            9K    1970-01-01\n" +
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
        self.assertEqual(form.highlighted, "/")
        self.assertIsNone(form.selected)
        form.update(1)
        self.assert_canvas_equals(
            canvas,
            "/A Directory          Size Last modified\n" +
            "|-+ ..                                  \n" +
            "|-+ A Directory         9K    1970-01-01\n" +
            "|-- A File              9K    1970-01-01\n" +
            "|-- A Lnk -> A Tgt      9K    1970-01-01\n" +
            "|-- oööÖ.txt            9K    1970-01-01\n" +
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

        # Check that the Frame is rendered correctly.
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

        # Check the mouse works too - pass mouse events to top-level effect
        self.process_mouse(scene.effects[-1], [(10, 1, MouseEvent.LEFT_CLICK)])
        for effect in scene.effects:
            effect.update(3)
        self.assert_canvas_equals(
            canvas,
            "+-----|14 May 2016|--------------------+\n" +
            "|Date:|15/Jun/2017|                    |\n" +
            "|Time:|16 Jul 2018|                    O\n" +
            "|     +-----------+                    |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

        self.process_mouse(scene.effects[-1], [(11, 2, MouseEvent.LEFT_CLICK)])
        for effect in scene.effects:
            effect.update(4)
        self.assert_canvas_equals(
            canvas,
            "+-----|14 Jun 2016|--------------------+\n" +
            "|Date:|15/Jul/2017|                    |\n" +
            "|Time:|16 Aug 2018|                    O\n" +
            "|     +-----------+                    |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

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

        # Check that the Frame is rendered correctly.
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

        # Check the mouse works too - pass mouse events to top-level effect
        self.process_mouse(scene.effects[-1], [(7, 2, MouseEvent.LEFT_CLICK)])
        for effect in scene.effects:
            effect.update(3)
        self.assert_canvas_equals(
            canvas,
            "+-----+--------+-----------------------+\n" +
            "|Date:|10 00 57|17                     |\n" +
            "|Time:|11:01:58|                       O\n" +
            "|     |12 02 59|                       |\n" +
            "|     +--------+                       |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

        self.process_mouse(scene.effects[-1], [(7, 1, MouseEvent.LEFT_CLICK)])
        for effect in scene.effects:
            effect.update(4)
        self.assert_canvas_equals(
            canvas,
            "+-----+--------+-----------------------+\n" +
            "|Date:|09 00 57|17                     |\n" +
            "|Time:|10:01:58|                       O\n" +
            "|     |11 02 59|                       |\n" +
            "|     +--------+                       |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

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

    def test_dropdown_list(self):
        """
        Check DropdownList widget works as expected.
        """
        # Now set up the Frame ready for testing
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = Scene([], duration=-1)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = Frame(canvas, canvas.height, canvas.width)
        layout = Layout([100], fill_frame=True)
        form.add_layout(layout)
        layout.add_widget(DropdownList([("Item 1", 1), ("Item 2", 3), ("Item 3", 5)]))
        form.fix()
        form.register_scene(scene)
        scene.add_effect(form)
        scene.reset()

        # Check that the Frame is rendered correctly.
        for effect in scene.effects:
            effect.update(0)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "|[Item 1                              ]|\n" +
            "|                                      O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

        # Check it opens as expected
        self.process_mouse(scene, [(7, 1, MouseEvent.LEFT_CLICK)])
        for effect in scene.effects:
            effect.update(1)
        self.assert_canvas_equals(
            canvas,
            "++------------------------------------++\n" +
            "||Item 1                              ||\n" +
            "||------------------------------------|O\n" +
            "||Item 1                              ||\n" +
            "||Item 2                              ||\n" +
            "||Item 3                              ||\n" +
            "|+------------------------------------+|\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

        # Check ESC works as expected
        self.process_keys(scene, [Screen.KEY_DOWN, Screen.KEY_ESCAPE])
        for effect in scene.effects:
            effect.update(2)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "|[Item 1                              ]|\n" +
            "|                                      O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

        # Check key selection works as expected
        self.process_keys(scene, [" ", Screen.KEY_DOWN])
        for effect in scene.effects:
            effect.update(3)
        self.assert_canvas_equals(
            canvas,
            "++------------------------------------++\n" +
            "||Item 2                              ||\n" +
            "||------------------------------------|O\n" +
            "||Item 1                              ||\n" +
            "||Item 2                              ||\n" +
            "||Item 3                              ||\n" +
            "|+------------------------------------+|\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

        # Check Enter works as expected
        self.process_keys(scene, [Screen.ctrl("m")])
        for effect in scene.effects:
            effect.update(4)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "|[Item 2                              ]|\n" +
            "|                                      O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

    def test_dropdown_list_options(self):
        """
        Check DropdownList widget extra features work.
        """
        # Now set up the Frame ready for testing
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = Scene([], duration=-1)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = Frame(canvas, canvas.height, canvas.width)
        layout = Layout([100], fill_frame=True)
        form.add_layout(layout)
        layout.add_widget(Divider(draw_line=False, height=7))
        layout.add_widget(DropdownList([("Item {}".format(i), i) for i in range(10)]))
        form.fix()
        form.register_scene(scene)
        scene.add_effect(form)
        scene.reset()

        # Check that the Frame is rendered correctly.
        for effect in scene.effects:
            effect.update(0)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "|                                      |\n" +
            "|                                      O\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|[Item 0                              ]|\n" +
            "+--------------------------------------+\n")

        # Check it opens as expected
        self.process_mouse(scene, [(7, 8, MouseEvent.LEFT_CLICK)])
        for effect in scene.effects:
            effect.update(1)
        self.assert_canvas_equals(
            canvas,
            "++------------------------------------++\n" +
            "||Item 0                             O||\n" +
            "||Item 1                             ||O\n" +
            "||Item 2                             |||\n" +
            "||Item 3                             |||\n" +
            "||Item 4                             |||\n" +
            "||Item 5                             |||\n" +
            "||------------------------------------||\n" +
            "||Item 0                              ||\n" +
            "++------------------------------------++\n")

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

        # Check that it is drawn with the obscuring character, though.
        form.update(0)
        self.assert_canvas_equals(
            canvas,
            "Password ****                           \n" +
            "                                        \n")

    def test_change_values(self):
        """
        Check changing Text values resets cursor position.
        """
        # Create a dummy screen.
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = MagicMock(spec=Scene)
        canvas = Canvas(screen, 10, 40, 0, 0)

        # Create the form we want to test.
        form = Frame(canvas, canvas.height, canvas.width, has_border=False)
        layout = Layout([100], fill_frame=True)
        form.add_layout(layout)
        text = Text()
        layout.add_widget(text)
        form.fix()
        form.register_scene(scene)
        form.reset()

        # Check that input is put at the end of the new text
        text.value = "A test"
        self.process_keys(form, ["A"])
        form.save()
        self.assertEqual(text.value, "A testA")

        # Check that growing longer still puts it at the end.
        text.value = "A longer test"
        self.process_keys(form, ["A"])
        form.save()
        self.assertEqual(text.value, "A longer testA")

    def test_popup_meu(self):
        """
        Check PopupMenu widget works as expected.
        """
        # Simple function to test which item is selected.
        def click(x):
            self.clicked = self.clicked or x

        # Now set up the Frame ready for testing
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = Scene([], duration=-1)
        canvas = Canvas(screen, 10, 40, 0, 0)

        # Reset menu for test
        self.clicked = 0
        popup = PopupMenu(canvas,
                          [
                              ("First", lambda: click(1)),
                              ("Second", lambda: click(2)),
                              ("Third", lambda: click(4))
                          ],
                          0, 0)
        popup.register_scene(scene)
        scene.add_effect(popup)
        scene.reset()

        # Check that the menu is rendered correctly.
        for effect in scene.effects:
            effect.update(0)
        self.assert_canvas_equals(
            canvas,
            "First                                   \n" +
            "Second                                  \n" +
            "Third                                   \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n")

        # Check it handles a selection as expected
        self.process_mouse(scene, [(0, 1, MouseEvent.LEFT_CLICK)])
        self.assertEquals(len(scene.effects), 0)
        self.assertEquals(self.clicked, 2)

        # Check choice of location at bottom right
        self.clicked = 0
        canvas.reset()
        popup = PopupMenu(canvas,
                          [
                              ("First", lambda: click(1)),
                              ("Second", lambda: click(2)),
                              ("Third", lambda: click(4))
                          ],
                          39, 9)
        popup.register_scene(scene)
        scene.add_effect(popup)
        scene.reset()

        # Check that the menu is rendered correctly.
        for effect in scene.effects:
            effect.update(0)
        self.assert_canvas_equals(
            canvas,
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                        \n" +
            "                                  First \n" +
            "                                  Second\n" +
            "                                  Third \n")

        # Check it handles a selection as expected
        self.process_mouse(scene, [(39, 7, MouseEvent.LEFT_CLICK)])
        self.assertEquals(len(scene.effects), 0)
        self.assertEquals(self.clicked, 1)

        # Check clicking outside menu dismisses it - wrong X location.
        self.clicked = 0
        canvas.reset()
        popup = PopupMenu(canvas, [("A", lambda: click(1)), ("B", lambda: click(2))], 39, 9)
        popup.register_scene(scene)
        scene.add_effect(popup)
        scene.reset()
        self.process_mouse(scene, [(10, 9, MouseEvent.LEFT_CLICK)])
        self.assertEquals(len(scene.effects), 0)
        self.assertEquals(self.clicked, 0)

        # Check clicking outside menu dismisses it - wrong Y location.
        self.clicked = 0
        canvas.reset()
        popup = PopupMenu(canvas, [("A", lambda: click(1)), ("B", lambda: click(2))], 39, 9)
        popup.register_scene(scene)
        scene.add_effect(popup)
        scene.reset()
        self.process_mouse(scene, [(39, 1, MouseEvent.LEFT_CLICK)])
        self.assertEquals(len(scene.effects), 0)
        self.assertEquals(self.clicked, 0)

        # Check clicking outside menu dismisses it.
        self.clicked = 0
        canvas.reset()
        popup = PopupMenu(canvas, [("A", lambda: click(1)), ("B", lambda: click(2))], 39, 9)
        popup.register_scene(scene)
        scene.add_effect(popup)
        scene.reset()
        self.process_keys(popup, [Screen.KEY_ESCAPE])
        self.assertEquals(len(scene.effects), 0)
        self.assertEquals(self.clicked, 0)

    def test_find_min_start(self):
        """
        Check _find_min_start works as expected.
        """
        # Normal operation will find last <limit> characters.
        self.assertEqual(_find_min_start("ABCDEF", 3), 3)

        # Allow extra space for cursor loses another
        self.assertEqual(_find_min_start("ABCDEF", 3, at_end=True), 4)


    def test_vertical_divider(self):
        """
        Check VerticalDivider widget works as expected.
        """
        # Now set up the Frame ready for testing
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = Scene([], duration=-1)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = Frame(canvas, canvas.height, canvas.width)
        layout = Layout([5, 1, 26, 1, 5])
        form.add_layout(layout)
        layout.add_widget(Label("A"), 1)
        layout.add_widget(VerticalDivider(), 1)
        layout.add_widget(Label("B"), 1)
        layout.add_widget(TextBox(5), 2)
        layout.add_widget(VerticalDivider(), 3)
        layout.add_widget(Label("END"), 4)
        form.fix()
        form.register_scene(scene)
        scene.add_effect(form)
        scene.reset()

        # Check that the frame is rendered correctly.
        for effect in scene.effects:
            effect.update(0)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "|     A                          |END  |\n" +
            "|     |                          |     O\n" +
            "|     |                          |     |\n" +
            "|     |                          |     |\n" +
            "|     B                          |     |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")

    def test_value_defaults(self):
        """
        Check Widgets can set default values from code.
        """
        # Now set up the Frame ready for testing
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = Scene([], duration=-1)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = Frame(canvas, canvas.height, canvas.width)
        layout = Layout([100])
        form.add_layout(layout)

        textbox = TextBox(2, label="TB")
        textbox.value = ["Hello"]
        text = Text(label="B")
        text.value = "World"
        listbox = ListBox(2, [("A", 1), ("B", 2), ("C", 3), ("D", 4)], label="LB")
        listbox.value = 3

        layout.add_widget(textbox)
        layout.add_widget(text)
        layout.add_widget(listbox)
        form.fix()
        form.register_scene(scene)
        scene.add_effect(form)
        scene.reset()

        # Check that the frame is rendered correctly.
        for effect in scene.effects:
            effect.update(0)
        self.assert_canvas_equals(
            canvas,
            "+--------------------------------------+\n" +
            "|TB Hello                              |\n" +
            "|                                      O\n" +
            "|B  World                              |\n" +
            "|LB C                                  |\n" +
            "|   D                                  |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "|                                      |\n" +
            "+--------------------------------------+\n")


    def test_frame_themes(self):
        """
        Check we can set a colour theme for a Frame.
        """
        # Now set up the Frame ready for testing
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=False)
        scene = Scene([], duration=-1)
        canvas = Canvas(screen, 10, 40, 0, 0)
        form = Frame(canvas, canvas.height, canvas.width)

        # Check colour changes work...
        self.assertEqual(
            form.palette["background"],
            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE))
        form.set_theme("monochrome")
        self.assertEqual(
            form.palette["background"],
            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK))

        # Check that a bad theme name has no effect.
        form.set_theme("blah - this doesn't exist")
        self.assertEqual(
            form.palette["background"],
            (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK))


if __name__ == '__main__':
    unittest.main()
