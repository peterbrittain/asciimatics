#!/usr/bin/env python3

from asciimatics.widgets import Frame, Text, TextBox, Layout, Label, Button, PopUpDialog, Widget
from asciimatics.effects import Background
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication
from asciimatics.utilities import BoxTool


class TopFrame(Frame):
    def __init__(self, screen):
        super(TopFrame, self).__init__(screen,
                                       int(screen.height // 3) - 1,
                                       screen.width // 2,
                                       y=0,
                                       has_border=True,
                                       can_scroll=True,
                                       name="Top Form")
        self.border_box.set_style(BoxTool.DOUBLE_LINE)
        layout = Layout([1, 18, 1])
        self.add_layout(layout)
        layout.add_widget(Label("Scrolling, with border"), 1)
        for i in range(screen.height // 2):
            layout.add_widget(Text(label=f"Text {i}:"), 1)
        self.fix()


class MidFrame(Frame):
    def __init__(self, screen):
        super(MidFrame, self).__init__(screen,
                                       int(screen.height // 3) - 1,
                                       screen.width // 2,
                                       y=int(screen.height // 3),
                                       has_border=False,
                                       can_scroll=True,
                                       name="Mid Form")
        layout = Layout([1, 18, 1])
        self.add_layout(layout)
        layout.add_widget(Label("Scrolling, no border"), 1)
        for i in range(screen.height // 2):
            layout.add_widget(Text(label=f"Text {i}:"), 1)
        self.fix()


class BottomFrame(Frame):
    def __init__(self, screen):
        super(BottomFrame, self).__init__(screen,
                                          int(screen.height // 3),
                                          screen.width // 2,
                                          y=int(screen.height * 2 // 3),
                                          has_border=False,
                                          can_scroll=False,
                                          name="Bottom Form")
        layout = Layout([1, 18, 1])
        self.add_layout(layout)
        layout.add_widget(Label("No scrolling, no border"), 1)
        layout.add_widget(TextBox(Widget.FILL_FRAME, label="Box 3:", name="BOX3"), 1)
        layout.add_widget(Text(label="Text 3:", name="TEXT3"), 1)
        layout.add_widget(Button("Quit", self._quit, label="To exit:"), 1)
        self.fix()

    def _quit(self):
        popup = PopUpDialog(self._screen, "Are you sure?", ["Yes", "No"],
                    has_shadow=True, on_close=self._quit_on_yes)
        self._scene.add_effect(popup)

    @staticmethod
    def _quit_on_yes(selected):
        # Yes is the first button
        if selected == 0:
            raise StopApplication("User requested exit")


def demo(screen, scene):
    scenes = [Scene([
        Background(screen),
        TopFrame(screen),
        MidFrame(screen),
        BottomFrame(screen),
    ], -1)]

    screen.play(scenes, stop_on_resize=True, start_scene=scene, allow_int=True)


last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=False, arguments=[last_scene])
        quit()
    except ResizeScreenError as e:
        last_scene = e.scene
