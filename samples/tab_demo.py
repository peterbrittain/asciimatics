#!/usr/bin/env python3

from asciimatics.widgets import Frame, Layout, Divider, Button
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, NextScene, StopApplication
import sys


class TabButtons(Layout):
    def __init__(self, frame, active_tab_idx):
        cols = [1, 1, 1, 1, 1]
        super().__init__(cols)
        self._frame = frame
        for i,_ in enumerate(cols):
            self.add_widget(Divider(), i)
        btns = [Button("Btn1", self._on_click_1),
                Button("Btn2", self._on_click_2),
                Button("Btn3", self._on_click_3),
                Button("Btn4", self._on_click_4),
                Button("Quit", self._on_click_Q)]
        for i, btn in enumerate(btns):
            self.add_widget(btn, i)
        btns[active_tab_idx].disabled = True

    def _on_click_1(self):
        raise NextScene("Tab1")

    def _on_click_2(self):
        raise NextScene("Tab2")

    def _on_click_3(self):
        raise NextScene("Tab3")

    def _on_click_4(self):
        raise NextScene("Tab4")

    def _on_click_Q(self):
        raise StopApplication("Quit")


class RootPage(Frame):
    def __init__(self, screen):
        super().__init__(screen,
                         screen.height,
                         screen.width,
                         can_scroll=False,
                         title="Root Page")
        layout1 = Layout([1], fill_frame=True)
        self.add_layout(layout1)
        # add your widgets here

        layout2 = TabButtons(self, 0)
        self.add_layout(layout2)
        self.fix()


class AlphaPage(Frame):
    def __init__(self, screen):
        super().__init__(screen,
                         screen.height,
                         screen.width,
                         can_scroll=False,
                         title="Alpha Page")
        layout1 = Layout([1], fill_frame=True)
        self.add_layout(layout1)
        # add your widgets here

        layout2 = TabButtons(self, 1)
        self.add_layout(layout2)
        self.fix()


class BravoPage(Frame):
    def __init__(self, screen):
        super().__init__(screen,
                         screen.height,
                         screen.width,
                         can_scroll=False,
                         title="Bravo Page")
        layout1 = Layout([1], fill_frame=True)
        self.add_layout(layout1)
        # add your widgets here

        layout2 = TabButtons(self, 2)
        self.add_layout(layout2)
        self.fix()


class CharliePage(Frame):
    def __init__(self, screen):
        super().__init__(screen,
                         screen.height,
                         screen.width,
                         can_scroll=False,
                         title="Charlie Page")
        layout1 = Layout([1], fill_frame=True)
        self.add_layout(layout1)
        # add your widgets here

        layout2 = TabButtons(self, 3)
        self.add_layout(layout2)
        self.fix()


def demo(screen, scene):
    scenes = [
        Scene([RootPage(screen)], -1, name="Tab1"),
        Scene([AlphaPage(screen)], -1, name="Tab2"),
        Scene([BravoPage(screen)], -1, name="Tab3"),
        Scene([CharliePage(screen)], -1, name="Tab4"),
    ]
    screen.play(scenes, stop_on_resize=True, start_scene=scene, allow_int=True)


last_scene = None
while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
