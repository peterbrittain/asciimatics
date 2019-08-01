from asciimatics.widgets import Frame, TextBox, Layout, Label, Divider, Text, \
    CheckBox, RadioButtons, Button, PopUpDialog, TimePicker, DatePicker, Background, DropdownList, \
    PopupMenu
from asciimatics.event import MouseEvent
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication, \
    InvalidFields
from asciimatics.utilities import AsciimaticsParser, AnsiTerminalParser
import sys
import re
import datetime
import logging

# Test data
tree = r"""
       ${3,1}*
${2}      / \
${2}     /${1}o${2}  \
${2}    /_   _\
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
""".split("\n")

terminal = """
[35mこんにちわ[0m[33m[ik][0m[33m、[0m[35mこにちわ[0m[33m[ik][0m[33m、[0m[35mこにちは[0m[33m[ik][0m
[32m1.[0m [33m[int;col] [misspelling of こんにちは][0m [1m[31mhello[0m[33m; [0mgood day (daytime greeting)

[1m[32m※[0m [35mどうも[0m
[32m1.[0m [33m[int;abbr][0m thanks
[32m2.[0m [33m[adv][0m much (thanks)[33m; [0mvery (sorry)[33m; [0mquite (regret)
[32m3.[0m quite[33m; [0mreally[33m; [0mmostly
[32m4.[0m somehow
[32m5.[0m [33m[in positive sense, esp. どうも〜しまう][0m in spite of oneself[33m; [0mno matter how hard one may try (one is unable to) (with negative verb)[33m; [0mno matter how hard one may try not to (one ends up doing) (with positive verb, esp. -shimau)
[32m6.[0m [33m[int][0m greetings[33m; [0m[1m[31mhello[0m[33m; [0mgoodbye

[1m[32m※[0m [35mハロー[0m[33m、[0m[35mハロ[0m
[32m1.[0m [33m[n][0m halo
[32m2.[0m [33m〔ハロー〕[0m [1m[31mhello[0m[33m; [0mhallo[33m; [0mhullo
[32m3.[0m [33m〔ハロー〕[0m harrow

[1m[32m※[0m [36m今日は[0m[33m（[0m[35mこんにちは[0m[33m、[0m[35mこんちは[0m[33m）[0m
[32m1.[0m [33m[int;uk] [こんちは is col.][0m [1m[31mhello[0m[33m; [0mgood day (daytime greeting)

[35mニーハオ[0m
[32m1.[0m [33m[int][0m [1m[31mhello[0m

[35mハイサイ[0m[33m、[0m[35mはいさい[0m
[32m1.[0m [33m[int;rkb][0m [1m[31mhello[0m[33m; [0mhi

[35mほいほい[0m[33m、[0m[35mホイホイ[0m
[32m1.[0m [33m[adv,adv-to,vs;on-mim][0m recklessly[33m; [0mthoughtlessly[33m; [0mcarelessly[33m; [0mreadily[33m; [0mblithely[33m; [0mwillingly[33m; [0measily
[32m2.[0m [33m[on-mim][0m pamperingly[33m; [0mindulgently[33m; [0mcarefully (not angering)
[32m3.[0m [33m[int][0m shoo!
[32m4.[0m heave-ho
[32m5.[0m hallo[33m; [0m[1m[31mhello[0m
[32m6.[0m [33m[n] 〔ホイホイ〕[0m Hui (people)
[32m7.[0m [33m[arch][0m novice[33m; [0mbeginner

[35mアニョハセヨ[0m[33m、[0m[35mアンニョンハセヨ[0m
[32m1.[0m [33m[n][0m [1m[31mhello[0m[33m; [0mhi
[0m[38;5;27masciimatics[0m
[38;5;27masciimatics.old[0m
[38;5;27mbase-setuptools[0m
bug_rep.py
[38;5;27mcaesar[0m
[38;5;27mcode-maat[0m
core.5193
[38;5;27mdata-warehouse-config[0m
dates.csv
[38;5;27mDesktop[0m
[38;5;27mDocuments[0m
[38;5;27mDownloads[0m
editor.py
files.csv
forms.log
git.log
[38;5;27mgoogle-cloud-sdk[0m
[38;5;27mhack[0m
[38;5;27mjira_cli[0m
[38;5;27mjira-export-tool[0m
[38;5;27mjira-to-bigquery[0m
[38;5;27mkivy[0m
[38;5;34mlein[0m
""".split("\n")

# Initial data for the form
form_data = {
    "TA": tree,
    "TB": "alphabet",
    "TC": "123",
    "TD": "a@b.com",
    "Things": 2,
    "CA": False,
    "CB": True,
    "CC": False,
    "DATE": datetime.datetime.now().date(),
    "TIME": datetime.datetime.now().time(),
    "PWD": "",
    "DD": 1
}

logging.basicConfig(filename="forms.log", level=logging.DEBUG)


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
        self._reset_button = Button("Reset", self._reset)
        layout.add_widget(Label("Group 1:"), 1)
        layout.add_widget(TextBox(5,
                                  label="My First Box:",
                                  name="TA",
                                  # parser=AnsiTerminalParser(),
                                  parser=AsciimaticsParser(),
                                  line_wrap=True,
                                  on_change=self._on_change), 1)
        layout.add_widget(
            Text(label="Alpha:",
                 name="TB",
                 on_change=self._on_change,
                 validator="^[a-zA-Z]*$"), 1)
        layout.add_widget(
            Text(label="Number:",
                 name="TC",
                 on_change=self._on_change,
                 validator="^[0-9]*$",
                 max_length=4), 1)
        layout.add_widget(
            Text(label="Email:",
                 name="TD",
                 on_change=self._on_change,
                 validator=self._check_email), 1)
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
        layout.add_widget(DatePicker("Date",
                                     name="DATE",
                                     year_range=range(1999, 2100),
                                     on_change=self._on_change), 1)
        layout.add_widget(
            TimePicker("Time", name="TIME", on_change=self._on_change, seconds=True), 1)
        layout.add_widget(Text("Password", name="PWD", on_change=self._on_change, hide_char="*"), 1)
        layout.add_widget(DropdownList(
            [("Item 1", 1),
             ("Item 2", 2),
             ("Item 3", 3),
             ("Item 3", 4),
             ("Item 3", 5),
             ("Item 3", 6),
             ("Item 3", 7),
             ("Item 3", 8),
             ("Item 3", 9),
             ("Item 3", 10),
             ("Item 3", 11),
             ("Item 3", 12),
             ("Item 3", 13),
             ("Item 3", 14),
             ("Item 3", 15),
             ("Item 3", 16),
             ("Item 4", 17),
             ("Item 5", 18), ],
            label="Dropdown", name="DD", on_change=self._on_change), 1)
        layout.add_widget(Divider(height=3), 1)
        layout2 = Layout([1, 1, 1])
        self.add_layout(layout2)
        layout2.add_widget(self._reset_button, 0)
        layout2.add_widget(Button("View Data", self._view), 1)
        layout2.add_widget(Button("Quit", self._quit), 2)
        self.fix()

    def process_event(self, event):
        # Handle dynamic pop-ups now.
        if (event is not None and isinstance(event, MouseEvent) and
                event.buttons == MouseEvent.DOUBLE_CLICK):
            # By processing the double-click before Frame handling, we have absolute coordinates.
            options = [
                ("Default", self._set_default),
                ("Green", self._set_green),
                ("Monochrome", self._set_mono),
                ("Bright", self._set_bright),
            ]
            if self.screen.colours >= 256:
                options.append(("Red/white", self._set_tlj))
            self._scene.add_effect(PopupMenu(self.screen, options, event.x, event.y))
            event = None

        # Pass any other event on to the Frame and contained widgets.
        return super(DemoFrame, self).process_event(event)

    def _set_default(self):
        self.set_theme("default")

    def _set_green(self):
        self.set_theme("green")

    def _set_mono(self):
        self.set_theme("monochrome")

    def _set_bright(self):
        self.set_theme("bright")

    def _set_tlj(self):
        self.set_theme("tlj256")

    def _on_change(self):
        changed = False
        self.save()
        for key, value in self.data.items():
            if key not in form_data or form_data[key] != value:
                changed = True
                break
        self._reset_button.disabled = not changed

    def _reset(self):
        self.reset()
        raise NextScene()

    def _view(self):
        # Build result of this form and display it.
        try:
            self.save(validate=True)
            message = "Values entered are:\n\n"
            for key, value in self.data.items():
                message += "- {}: {}\n".format(key, value)
        except InvalidFields as exc:
            message = "The following fields are invalid:\n\n"
            for field in exc.fields:
                message += "- {}\n".format(field)
        self._scene.add_effect(
            PopUpDialog(self._screen, message, ["OK"]))

    def _quit(self):
        self._scene.add_effect(
            PopUpDialog(self._screen,
                        "Are you sure?",
                        ["Yes", "No"],
                        has_shadow=True,
                        on_close=self._quit_on_yes))

    @staticmethod
    def _check_email(value):
        m = re.match(r"^[a-zA-Z0-9_\-.]+@[a-zA-Z0-9_\-.]+\.[a-zA-Z0-9_\-.]+$",
                     value)
        return len(value) == 0 or m is not None

    @staticmethod
    def _quit_on_yes(selected):
        # Yes is the first button
        if selected == 0:
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
