"""This module implements a pop up menu widget"""
from collections import defaultdict
from functools import partial
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.screen import Screen
from asciimatics.widgets.button import Button
from asciimatics.widgets.frame import Frame
from asciimatics.widgets.layout import Layout


class PopupMenu(Frame):
    """
    A widget for displaying a menu.
    """

    palette = defaultdict(lambda: (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_CYAN))
    palette["focus_button"] = (Screen.COLOUR_CYAN, Screen.A_NORMAL, Screen.COLOUR_WHITE)

    def __init__(self, screen, menu_items, x, y, has_border=False):
        """
        :param screen: The Screen being used for this pop-up.
        :param menu_items: a list of items to be displayed in the menu.
        :param x: The X coordinate for the desired pop-up.
        :param y: The Y coordinate for the desired pop-up.
        :param has_border: Whether the menu has a border box. Defaults to False.

        The menu_items parameter is a list of 2-tuples, which define the text to be displayed in
        the menu and the function to call when that menu item is clicked.  For example:

            menu_items = [("Open", file_open), ("Save", file_save), ("Close", file_close)]
        """

        border_adjustment = 0
        if has_border:
            border_adjustment = 2 # We add one character to each side for the border

        # Sort out location based on width of menu text.
        w = max(len(i[0]) for i in menu_items) + border_adjustment
        h = len(menu_items) + border_adjustment
        if x + w >= screen.width:
            x -= w - 1
        if y + h >= screen.height:
            y -= h - 1

        # Construct the Frame
        super().__init__(
            screen, h, w, x=x, y=y, has_border=has_border, can_scroll=False, is_modal=True, hover_focus=True)

        # Build the widget to display the time selection.
        layout = Layout([1], fill_frame=True)
        self.add_layout(layout)
        for item in menu_items:
            func = partial(self._destroy, item[1])
            layout.add_widget(Button(item[0], func, add_box=False), 0)
        self.fix()

    def _destroy(self, callback=None):
        self._scene.remove_effect(self)
        if callback is not None:
            callback()

    def process_event(self, event):
        # Look for events that will close the pop-up - e.g. clicking outside the Frame or ESC key.
        if event is not None:
            if isinstance(event, KeyboardEvent):
                if event.key_code == Screen.KEY_ESCAPE:
                    event = None
            elif isinstance(event, MouseEvent) and event.buttons != 0:
                if self._outside_frame(event):
                    event = None
        if event is None:
            self._destroy()
        return super().process_event(event)
