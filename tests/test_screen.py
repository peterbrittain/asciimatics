# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os
from mock import MagicMock
from random import randint
import unittest
import sys
from builtins import str
from builtins import chr
from builtins import bytes
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.exceptions import StopApplication, NextScene
try:
    from asciimatics.screen import _SignalState
except ImportError:
    pass
from asciimatics.scene import Scene
from asciimatics.screen import Screen, Canvas
from tests.mock_objects import MockEffect
if sys.platform == "win32":
    import win32console
    import win32con
else:
    import signal
    import curses


def check_screen_and_canvas(screen, fn):
    """
    Helper function to check that a Screen and Canvas work identically.

    :param screen: The screen object to use for the test.
    :param fn: The function to call for the test.
    """
    for test_object in (screen, Canvas(screen, screen.height, screen.width)):
        fn(test_object)


class TestScreen(unittest.TestCase):
    def setUp(self):
        # Skip for non-Windows if the terminal definition is incomplete.
        # This typically means we're running inside a non-standard terminal.
        # For example, this happens when embedded in PyCharm.
        if sys.platform != "win32":
            curses.initscr()
            if curses.tigetstr("ri") is None:
                self.skipTest("No valid terminal definition")

    def assert_canvas_equals(self, canvas, expected, height=10, width=75):
        """
        Assert output to canvas/screen is as expected.
        """
        # TODO: Merge with widget test function of the same name.
        output = ""
        for y in range(height):
            for x in range(width):
                try:
                    char, _, _, _ = canvas.get_from(x, y)
                except Exception:
                    raise RuntimeError("{} {}".format(x, y))
                output += chr(char)
            output += "\n"
        self.assertEqual(output, expected)

    def test_wrapper(self):
        """
        Check that you can create a blank Screen.
        """
        def internal_checks(screen):
            # Check screen basically exists
            self.assertIsNotNone(screen)
            self.assertGreater(screen.width, 0)
            self.assertGreater(screen.height, 0)
            self.assertGreater(screen.colours, 0)

            # Check that the Screen is cleared ready for use.
            for x in range(screen.width):
                for y in range(screen.height):
                    char, fg, attr, bg = screen.get_from(x, y)
                    self.assertEqual(char, ord(" "))
                    self.assertEqual(fg, Screen.COLOUR_WHITE)
                    self.assertEqual(attr, 0)
                    self.assertEqual(bg, Screen.COLOUR_BLACK)

        Screen.wrapper(internal_checks)

    def test_wrapper_return(self):
        """
        Check that you get the result back from the wrapped function.
        """
        def internal_checks(_):
            return True

        self.assertTrue(Screen.wrapper(internal_checks))

    def test_print_and_get(self):
        """
        Check that basic print_at and get_from work as expected.
        """
        def internal_checks(screen):
            for x in range(screen.width):
                for y in range(15):
                    char = randint(0, 255)
                    fg = randint(0, Screen.COLOUR_WHITE)
                    bg = randint(0, Screen.COLOUR_WHITE)
                    attr = randint(0, Screen.A_UNDERLINE)
                    screen.print_at(chr(char), x, y, fg, attr, bg)
                    char2, fg2, attr2, bg2 = screen.get_from(x, y)
                    self.assertEqual(char, char2)
                    self.assertEqual(fg, fg2)
                    self.assertEqual(attr, attr2)
                    self.assertEqual(bg, bg2)

        Screen.wrapper(
            check_screen_and_canvas, height=15, arguments=[internal_checks])

    def test_highlight(self):
        """
        Check that highlight works as expected.
        """
        def internal_checks(screen):
            for x in range(screen.width):
                for y in range(15):
                    char = randint(0, 255)
                    fg = randint(Screen.COLOUR_RED, Screen.COLOUR_WHITE)
                    bg = randint(Screen.COLOUR_RED, Screen.COLOUR_WHITE)
                    attr = randint(0, Screen.A_UNDERLINE)
                    screen.print_at(chr(char), x, y, fg, attr, bg)

            # Check BG highlight first.
            screen.highlight(-1, -1, screen.width + 2, screen.height + 2, bg=0)
            for x in range(screen.width):
                for y in range(15):
                    _, fg2, _, bg2 = screen.get_from(x, y)
                    self.assertEqual(bg2, 0)
                    self.assertNotEqual(fg2, 0)

            # Now check FG highlighting.
            screen.highlight(-1, -1, screen.width + 2, screen.height + 2, fg=0)
            for x in range(screen.width):
                for y in range(15):
                    _, fg2, _, bg2 = screen.get_from(x, y)
                    self.assertEqual(bg2, 0)
                    self.assertEqual(fg2, 0)

            # Now check blending.
            screen.print_at("*" * screen.width,
                            0, 0,
                            Screen.COLOUR_CYAN,
                            Screen.A_NORMAL,
                            Screen.COLOUR_YELLOW)
            screen.highlight(0, 0, screen.width, 1, fg=0, bg=0, blend=50)
            for x in range(screen.width):
                _, fg2, _, bg2 = screen.get_from(x, 0)
                self.assertEqual(bg2, 0)
                self.assertEqual(fg2, 0)

        Screen.wrapper(
            check_screen_and_canvas, height=15, arguments=[internal_checks])

    def test_visible(self):
        """
        Check that is_visible works as expected.
        """
        def internal_checks(screen):
            # Check some points that must always be visible
            self.assertTrue(screen.is_visible(0, 0))
            self.assertTrue(screen.is_visible(
                screen.width - 1, screen.height - 1))

            # Check some points that cannot be visible
            self.assertFalse(screen.is_visible(-1, -1))
            self.assertFalse(screen.is_visible(
                screen.width, screen.height))

        Screen.wrapper(
            check_screen_and_canvas, height=15, arguments=[internal_checks])

    def test_paint(self):
        """
        Check that paint with colour map works.
        """
        def internal_checks(screen):
            # Put a simple colour map to screen.
            screen.paint(
                "Text", 0, 0,
                colour_map=((1, 0, 4), (2, 0, 3), (3, 0, 2), (4, 0, 1)))

            # Check it is rendered as expected.
            char, fg, _, bg = screen.get_from(0, 0)
            self.assertEqual(fg, 1)
            self.assertEqual(bg, 4)
            char, fg, _, bg = screen.get_from(3, 0)
            self.assertEqual(fg, 4)
            self.assertEqual(bg, 1)

        Screen.wrapper(
            check_screen_and_canvas, height=15, arguments=[internal_checks])

    def test_limits(self):
        """
        Check that get_from and print_at limit checking works.
        """
        def internal_checks(screen):
            # Check we have some canvas dimensions
            self.assertEqual(screen.dimensions[1], screen.width)
            self.assertEqual(screen.dimensions[0], screen.height)

            # Basic limit checking
            self.assertIsNone(screen.get_from(-1, -1))
            self.assertIsNone(screen.get_from(screen.width, screen.height))

            # Printing off-screen should not fail, but do nothing.
            screen.print_at("hello", 0, -1)
            screen.print_at("hello", 0, screen.height)

            # Printing across screen edge should crop.
            screen.print_at("12345", -1, 0)
            char, fg, _, bg = screen.get_from(0, 0)
            self.assertEqual(char, ord("2"))
            self.assertEqual(fg, Screen.COLOUR_WHITE)
            self.assertEqual(bg, Screen.COLOUR_BLACK)

        Screen.wrapper(
            check_screen_and_canvas, height=15, arguments=[internal_checks])

    def test_scroll(self):
        """
        Check that scrolling works as expected.
        """
        def internal_checks(screen):
            # New screen is not scrolled.
            self.assertEqual(screen.start_line, 0)

            # Scroll and check it has moved
            screen.scroll()
            self.assertEqual(screen.start_line, 1)

            # Scroll to specific location and check it has moved
            screen.scroll_to(0)
            self.assertEqual(screen.start_line, 0)

        Screen.wrapper(internal_checks, height=15)

    def test_centre(self):
        """
        Check that centre works as expected.
        """
        def internal_checks(screen):
            screen.centre("1234", 0)
            char, fg, _, bg = screen.get_from((screen.width - 4) // 2, 0)
            self.assertEqual(char, ord("1"))
            self.assertEqual(fg, Screen.COLOUR_WHITE)
            self.assertEqual(bg, Screen.COLOUR_BLACK)

        Screen.wrapper(internal_checks, height=15)

    def test_draw(self):
        """
        Check that line drawing works as expected.
        """
        def internal_checks(screen):
            # Draw thick and thin lines
            for line_type in (True, False):
                # Draw in opposite directions
                for start in range(0, 11, 10):
                    screen.print_at(str(start), 11, 2)
                    # Horizontal line
                    screen.move(start, 0)
                    screen.draw(10 - start, 0, thin=line_type)
                    res = screen.get_from(1, 0)
                    self.assertEqual(res[0], ord("^" if line_type else "#"))

                    # Check clearing works too
                    screen.draw(start, 0, char=" ", thin=line_type)
                    res = screen.get_from(1, 0)
                    self.assertEqual(res[0], ord(" "))

                    # Vertical line
                    screen.move(0, start)
                    screen.draw(0, 10 - start, thin=line_type)
                    res = screen.get_from(0, 1)
                    self.assertEqual(res[0], ord("|" if line_type else "#"))

                    # Check clearing works too
                    screen.draw(0, start, char=" ", thin=line_type)
                    res = screen.get_from(0, 1)
                    self.assertEqual(res[0], ord(" "))

                    # Diagonal line
                    screen.move(0, start)
                    screen.draw(10, 10 - start, thin=line_type)
                    res = screen.get_from(1, 9 if start else 1)
                    if line_type:
                        self.assertEqual(res[0], ord("'" if start else "\\"))
                    else:
                        self.assertEqual(res[0], ord("7" if start else "Y"))

                    # Check clearing works too
                    screen.move(0, start)
                    screen.draw(10, 10 - start, char=" ", thin=line_type)
                    res = screen.get_from(1, 9 if start else 1)
                    self.assertEqual(res[0], ord(" "))

        Screen.wrapper(
            check_screen_and_canvas,
            height=15,
            unicode_aware=False,
            arguments=[internal_checks])

    def test_polygons(self):
        """
        Check that filled polygons work as expected.
        """
        def internal_checks(screen):
            screen.fill_polygon([[(0, 0), (10, 0), (0, 10), (10, 10)]])
            screen.fill_polygon([[(20, 0), (30, 0), (30, 10), (25, 5), (20, 10)]])
            screen.fill_polygon([[(40, 0), (45, 5), (50, 0), (50, 10), (40, 10)]])
            screen.fill_polygon([[(60, 0), (70, 0), (70, 10), (60, 10)],
                                 [(63, 2), (67, 2), (67, 8), (63, 8)]])
            self.maxDiff = None
            self.assert_canvas_equals(
                screen,
                "Y########7          ##########          .        .          ##########     \n" +
                " Y######7           ##########          #.      .#          ##########     \n" +
                "  Y####7            ##########          ##.    .##          ###    ###     \n" +
                "   Y##7             ##########          ###.  .###          ###    ###     \n" +
                "    Y7              ##########          ####..####          ###    ###     \n" +
                "    ..              ####7Y####          ##########          ###    ###     \n" +
                "   .##.             ###7  Y###          ##########          ###    ###     \n" +
                "  .####.            ##7    Y##          ##########          ###    ###     \n" +
                " .######.           #7      Y#          ##########          ##########     \n" +
                ".########.          7        Y          ##########          ##########     \n")

        Screen.wrapper(
            check_screen_and_canvas,
            height=10,
            unicode_aware=False,
            arguments=[internal_checks])

    def test_last_pos(self):
        """
        Check that screen drawing is efficient and unaffected by draw.
        """
        def internal_checks(screen):
            # Should start with no known location.
            screen.reset()
            self.assertEqual(screen._cur_x, None)
            self.assertEqual(screen._cur_y, None)

            # Drawing should not affect latest update.  This was previously
            # bugged - hence this test case!
            screen.move(0, 0)
            screen.draw(10, 10)
            self.assertEqual(screen._cur_x, None)
            self.assertEqual(screen._cur_y, None)

            # Printing should not affect latest update.
            screen.print_at("Hi", 12, 12)
            self.assertEqual(screen._cur_x, None)
            self.assertEqual(screen._cur_y, None)

            # Refresh should update the last drawn character.
            screen.refresh()
            self.assertEqual(screen._cur_x, 14)
            self.assertEqual(screen._cur_y, 12)

        Screen.wrapper(
            internal_checks,
            height=15,
            unicode_aware=False)

    def test_palette(self):
        """
        Check that we have a valid colour palette.
        """
        def internal_checks(screen):
            # Check basic length
            self.assertGreater(screen.colours, 0)
            self.assertEqual(len(screen.palette), 256 * 3)

            # Should always have fundamental console colours
            for i, c in enumerate((0, 0, 0)):
                self.assertEqual(screen.palette[i], c)
            for i, c in enumerate((128, 0, 0)):
                self.assertEqual(screen.palette[i+3], c)
            for i, c in enumerate((0, 128, 0)):
                self.assertEqual(screen.palette[i+6], c)
            for i, c in enumerate((128, 128, 0)):
                self.assertEqual(screen.palette[i+9], c)
            for i, c in enumerate((0, 0, 128)):
                self.assertEqual(screen.palette[i+12], c)
            for i, c in enumerate((128, 0, 128)):
                self.assertEqual(screen.palette[i+15], c)
            for i, c in enumerate((0, 128, 128)):
                self.assertEqual(screen.palette[i+18], c)
            for i, c in enumerate((192, 192, 192)):
                self.assertEqual(screen.palette[i+21], c)

        Screen.wrapper(internal_checks, height=15)

    def test_putch_and_getch(self):
        """
        Check deprecated features still work.
        """
        def internal_checks(screen):
            for x in range(screen.width):
                for y in range(15):
                    char = randint(0, 255)
                    fg = randint(0, Screen.COLOUR_WHITE)
                    bg = randint(0, Screen.COLOUR_WHITE)
                    attr = randint(0, Screen.A_UNDERLINE)
                    screen.putch(chr(char), x, y, fg, attr, bg)
                    char2, fg2, attr2, bg2 = screen.getch(x, y)
                    self.assertEqual(char, char2)
                    self.assertEqual(fg, fg2)
                    self.assertEqual(attr, attr2)
                    self.assertEqual(bg, bg2)

        Screen.wrapper(internal_checks, height=15)

    def test_open_close(self):
        """
        Check Screen.open works.
        """
        def check_screen(local_screen):
            # If we get here there's not much new to test.  Check that we can
            # draw something without hitting an Exception.
            local_screen.print_at("Hello world!",
                                  0, 0,
                                  colour=Screen.COLOUR_CYAN,
                                  attr=Screen.A_BOLD,
                                  bg=Screen.COLOUR_BLUE)
            local_screen.refresh()

        screen = Screen.open()
        check_screen(screen)
        screen.close()

    def test_refresh(self):
        """
        Check that refresh works.
        """
        def internal_checks(screen):
            # Not much we can do here as refresh will draw to a screen we can't
            # query. Check that we don't hit an Exception on refresh().
            screen.print_at("Hello world!",
                            0, 0,
                            colour=Screen.COLOUR_CYAN,
                            attr=Screen.A_BOLD,
                            bg=Screen.COLOUR_BLUE)
            screen.refresh()

        Screen.wrapper(
            check_screen_and_canvas, height=15, arguments=[internal_checks])

    def test_origin(self):
        """
        Check that Canvas origin is correct.
        """
        def internal_checks(screen):
            canvas = Canvas(screen, 5, 5, 1, 2)
            self.assertEqual(canvas.origin, (1, 2))

        Screen.wrapper(internal_checks, height=15)

    def test_play(self):
        """
        Check that we can play a basic Effect in a Scene.
        """
        def internal_checks(screen):
            # Since the Screen draws things, there's not too much we can do
            # to genuinely verify this without verifying all Scene and Effect
            # function too.  Just play a dummy Effect for now.
            test_effect = MockEffect()
            screen.play([Scene([test_effect], 0)])
            self.assertTrue(test_effect.stop_called)
            self.assertTrue(test_effect.reset_called)

            # Now check that the desired duration is used.
            test_effect = MockEffect(count=6)
            screen.play([Scene([test_effect], 15)])
            self.assertFalse(test_effect.stop_called)
            self.assertTrue(test_effect.reset_called)

            # Now check that delete_count works.
            test_effect = MockEffect(count=6)
            test_effect2 = MockEffect(delete_count=3)
            scene = Scene([test_effect, test_effect2], 15)
            self.assertEqual(len(scene.effects), 2)
            screen.play([scene])
            self.assertEqual(len(scene.effects), 1)
            self.assertEqual(scene.effects[0], test_effect)

        Screen.wrapper(internal_checks, height=15)

    def test_next_scene(self):
        """
        Check that we can play multiple Scenes.
        """
        def internal_checks(screen):
            # First check that we can move between screens.
            test_effect1 = MockEffect(stop=False)
            test_effect2 = MockEffect(count=5)
            screen.play([
                Scene([test_effect1], 5),
                Scene([test_effect2], 0)])
            self.assertTrue(test_effect1.update_called)
            self.assertTrue(test_effect2.update_called)

            # Now check that we can start at the second scene.
            test_effect1 = MockEffect(stop=False)
            scene1 = Scene([test_effect1], 5, name="1")
            test_effect2 = MockEffect(count=3)
            scene2 = Scene([test_effect2], 0, name="2")
            screen.play([scene1, scene2], start_scene=scene2)
            self.assertFalse(test_effect1.update_called)
            self.assertTrue(test_effect2.update_called)

            # Now check that we can move to named scenes.
            test_effect1 = MockEffect(stop=False, next_scene="B")
            test_effect2 = MockEffect(count=5)
            screen.play([
                Scene([test_effect1], 15, name="A"),
                Scene([test_effect2], 0, name="B")])
            self.assertTrue(test_effect1.update_called)
            self.assertTrue(test_effect2.update_called)

            # Now check that bad names cause an exception.
            with self.assertRaises(RuntimeError):
                test_effect1 = MockEffect(stop=False, next_scene="C")
                test_effect2 = MockEffect(count=5)
                screen.play([
                    Scene([test_effect1], 15, name="A"),
                    Scene([test_effect2], 0, name="B")])
            self.assertTrue(test_effect1.update_called)
            self.assertFalse(test_effect2.update_called)

            # Now check that play stops at the end when repeat=False
            test_effect1 = MockEffect(stop=False)
            scene1 = Scene([test_effect1], 5, name="1")
            screen.play([scene1], repeat=False)
            self.assertTrue(test_effect1.update_called)

        Screen.wrapper(internal_checks, height=15)

    def test_forced_update(self):
        """
        Check that forcing an update works as expected.
        """
        def internal_checks(screen):
            # First check that Effects are always drawn at Scene start
            test_effect = MockEffect(count=101, stop_frame=101, frame_rate=100)
            screen.set_scenes([Scene([test_effect], 0)])
            screen.draw_next_frame()
            self.assertTrue(test_effect.update_called)

            # Now check that the Screen honours the long frame rate...
            test_effect.update_called = False
            for _ in range(90):
                screen.draw_next_frame()
            self.assertFalse(test_effect.update_called)

            # Now check that the forced update works as expected.
            screen.force_update()
            screen.draw_next_frame()
            self.assertTrue(test_effect.update_called)

        Screen.wrapper(internal_checks, height=15)

    def test_catch_exceptions(self):
        """
        Check that we can catch exceptions (e.g. for ctrl-c).
        """
        def internal_checks(screen):
            # Not much we can do here as refresh will draw to a screen we can't
            # query. Check that we don't hit an Exception on refresh().
            if sys.platform == "win32":
                # Strictly speaking, this doesn't test catching ctrl-c as
                # it isn't possible to trigger the control handler (even if
                # we don't catch interrupts).  Still a good basic check for
                # input, though.
                event = win32console.PyINPUT_RECORDType(win32console.KEY_EVENT)
                event.Char = u"\03"
                event.KeyDown = 1
                event.RepeatCount = 1
                event.ControlKeyState = win32con.LEFT_CTRL_PRESSED
                event.VirtualKeyCode = 67
                event.VirtualScanCode = 46
                screen._stdin.WriteConsoleInput([event])
                event.KeyDown = 0
                screen._stdin.WriteConsoleInput([event])
                ch = screen.get_event()
                self.assertEqual(ch.key_code, 3)
                self.assertIsNone(screen.get_event())
            else:
                # Check Ctrl-c (and no other input)
                os.kill(os.getpid(), signal.SIGINT)
                ch = screen.get_event()
                self.assertEqual(ch.key_code, 3)
                self.assertIsNone(screen.get_event())

                # Check Ctrl-z (and no other input)
                os.kill(os.getpid(), signal.SIGTSTP)
                ch = screen.get_event()
                self.assertEqual(ch.key_code, 26)
                self.assertIsNone(screen.get_event())

        Screen.wrapper(internal_checks, height=15, catch_interrupt=True)

    def test_scroll_redraw(self):
        """
        Check that scrolling works with screen locations.
        """
        def internal_checks(screen):
            # New screen is not scrolled.
            self.assertEqual(screen.start_line, 0)

            # Scroll and check it has not moved
            screen.print_at("Hello", 0, 1)
            screen.scroll()
            screen.refresh()
            for i, c in enumerate("Hello"):
                self.assertEqual(screen.get_from(i, 1)[0], ord(c))

            # Scroll and check drawing off-screen works.
            screen.print_at("World", 0, 0)
            screen.scroll()
            screen.refresh()
            for i, c in enumerate("World"):
                self.assertEqual(screen.get_from(i, 0)[0], ord(c))

        Screen.wrapper(internal_checks)

    @staticmethod
    def _inject_key(screen, char):
        """
        Inject a specified character into the input buffers.
        """
        if sys.platform == "win32":
            event = win32console.PyINPUT_RECORDType(win32console.KEY_EVENT)
            event.RepeatCount = 1
            event.ControlKeyState = 0
            event.VirtualScanCode = 0
            if char >= 0:
                event.Char = chr(char)
                event.VirtualKeyCode = ord(chr(char).upper())
            else:
                # Lookup in mapping dicts
                reverse = dict((v, k) for k, v in
                               screen._EXTRA_KEY_MAP.items())
                if char in reverse:
                    event.VirtualKeyCode = reverse[char]
                else:
                    # Fudge key state required for BACK_TAB if needed.
                    if char == Screen.KEY_BACK_TAB:
                        char = Screen.KEY_TAB
                        event.ControlKeyState = win32con.SHIFT_PRESSED
                    reverse = dict((v, k) for k, v in
                                   screen._KEY_MAP.items())
                    event.VirtualKeyCode = reverse[char]
            event.KeyDown = 1
            screen._stdin.WriteConsoleInput([event])
            event.KeyDown = 0
            screen._stdin.WriteConsoleInput([event])
        else:
            if char > 0:
                # Curses uses a LIFO stack for key injection, so reverse the
                # byte string to be injected.  Note that this still works for
                # ASCII as it is a single char subset of UTF-8.
                for c in reversed(bytes(chr(char).encode("utf-8"))):
                    curses.ungetch(c)
            else:
                reverse = dict((v, k) for k, v in
                               screen._KEY_MAP.items())
                curses.ungetch(reverse[char])

    @staticmethod
    def _inject_mouse(screen, x, y, button):
        """
        Inject a mouse event into the input buffers.
        """
        if sys.platform == "win32":
            event = win32console.PyINPUT_RECORDType(win32console.MOUSE_EVENT)
            event.MousePosition.X = x
            event.MousePosition.Y = y
            if button & MouseEvent.LEFT_CLICK != 0:
                event.ButtonState |= win32con.FROM_LEFT_1ST_BUTTON_PRESSED
            if button & MouseEvent.RIGHT_CLICK != 0:
                event.ButtonState |= win32con.RIGHTMOST_BUTTON_PRESSED
            if button & MouseEvent.DOUBLE_CLICK != 0:
                event.EventFlags |= win32con.DOUBLE_CLICK
            screen._stdin.WriteConsoleInput([event])
        else:
            # Curses doesn't like no value in some cases - use a dummy button
            # click which we don't use instead.
            bstate = curses.BUTTON4_CLICKED
            if button & MouseEvent.LEFT_CLICK != 0:
                bstate |= curses.BUTTON1_CLICKED
            if button & MouseEvent.RIGHT_CLICK != 0:
                bstate |= curses.BUTTON3_CLICKED
            if button & MouseEvent.DOUBLE_CLICK != 0:
                bstate |= curses.BUTTON1_DOUBLE_CLICKED
            curses.ungetmouse(0, x, y, 0, bstate)

    def test_key_input(self):
        """
        Check that keyboard input works.
        """
        def internal_checks(screen):
            # Inject a letter and check it is picked up
            self._inject_key(screen, ord("a"))
            ch = screen.get_event()
            self.assertEqual(ch.key_code, ord("a"))
            self.assertIsNone(screen.get_event())

            # Inject a letter and check it is picked up
            self._inject_key(screen, Screen.KEY_BACK_TAB)
            ch = screen.get_event()
            self.assertEqual(ch.key_code, Screen.KEY_BACK_TAB)
            self.assertIsNone(screen.get_event())

            # Check that get_key also works.
            self._inject_key(screen, ord("b"))
            ch = screen.get_key()
            self.assertEqual(ch, ord("b"))
            self.assertIsNone(screen.get_key())

            # Check that unicode input also works
            self._inject_key(screen, ord(u"├"))
            ch = screen.get_event()
            self.assertEqual(ch.key_code, ord(u"├"))
            self.assertIsNone(screen.get_event())

        Screen.wrapper(internal_checks, height=15, unicode_aware=True)

    def test_mouse_input(self):
        """
        Check that mouse input works.
        """
        def internal_checks(screen):
            # Inject a mouse move and check it is picked up
            self._inject_mouse(screen, 1, 2, 0)
            ev = screen.get_event()
            self.assertEqual(ev.x, 1)
            self.assertEqual(ev.y, 2)
            self.assertEqual(ev.buttons, 0)
            self.assertIsNone(screen.get_event())

            # Check left click
            self._inject_mouse(screen, 2, 3, MouseEvent.LEFT_CLICK)
            ev = screen.get_event()
            self.assertEqual(ev.x, 2)
            self.assertEqual(ev.y, 3)
            self.assertEqual(ev.buttons, MouseEvent.LEFT_CLICK)
            self.assertIsNone(screen.get_event())

            # Check right click
            self._inject_mouse(screen, 0, 0, MouseEvent.RIGHT_CLICK)
            ev = screen.get_event()
            self.assertEqual(ev.x, 0)
            self.assertEqual(ev.y, 0)
            self.assertEqual(ev.buttons, MouseEvent.RIGHT_CLICK)
            self.assertIsNone(screen.get_event())

            # Check double click
            self._inject_mouse(screen, 0, 0, MouseEvent.DOUBLE_CLICK)
            ev = screen.get_event()
            self.assertEqual(ev.x, 0)
            self.assertEqual(ev.y, 0)
            self.assertEqual(ev.buttons, MouseEvent.DOUBLE_CLICK)
            self.assertIsNone(screen.get_event())

        Screen.wrapper(internal_checks, height=15)

    def test_windows_input(self):
        """
        Check that extended keyboard input works on Windows.
        """
        def internal_checks(screen):
            if sys.platform != "win32":
                self.skipTest("Only valid for Windows platforms")

            # Test no mapping by default
            self._inject_key(screen, Screen.KEY_NUMPAD0)
            self.assertIsNone(screen.get_event())

            # Test switching on mapping picks up keys
            screen.map_all_keys(True)
            self._inject_key(screen, Screen.KEY_NUMPAD0)
            ch = screen.get_key()
            self.assertEqual(ch, Screen.KEY_NUMPAD0)
            self.assertIsNone(screen.get_key())

        Screen.wrapper(internal_checks, height=15)

    def test_unhandled_events(self):
        """
        Check that default handling of events works as documented.
        """
        def internal_checks(screen):
            # Check for exit
            for char in ("X", "x", "Q", "q"):
                with self.assertRaises(StopApplication):
                    event = KeyboardEvent(ord(char))
                    screen._unhandled_event_default(event)

            for char in (" ", "\n"):
                with self.assertRaises(NextScene):
                    event = KeyboardEvent(ord(char))
                    screen._unhandled_event_default(event)

        Screen.wrapper(internal_checks, height=15)

    def test_title(self):
        """
        Check that we can change the screen title.
        """
        def internal_checks(screen):
            # It's not possible to read values back, so just check code doesn't
            # crash.
            screen.set_title("Asciimatics test")

        Screen.wrapper(internal_checks, height=15)

    def test_ctrl(self):
        """
        Check that ctrl returns the right values.
        """
        # Check standard alphabetical range
        for i, char in enumerate(range(ord('@'), ord('Z'))):
            self.assertEqual(Screen.ctrl(char), i)
            self.assertEqual(Screen.ctrl(chr(char)), i)
            self.assertEqual(Screen.ctrl(chr(char).lower()), i)

        # Check last few options - which mostly aren't actually returned in
        # Linux and so probably only of limited value, but what the heck!
        for i, char in enumerate(["[", "\\", "]", "^", "_"]):
            self.assertEqual(Screen.ctrl(char), i + 27)

        # Check other things return None - pick boundaries for checks.
        for char in ["?", "`", "\x7f"]:
            self.assertIsNone(Screen.ctrl(char))

    def assert_line_equals(self, canvas, expected, y=0, length=None):
        """
        Assert first line of output to canvas is as expected.
        """
        output = ""
        for x in range(canvas.width):
            char, _, _, _ = canvas.get_from(x, y)
            output += chr(char)
        if length:
            self.assertEqual(output[:length], expected[:length])
        else:
            self.assertEqual(output, expected)

    def test_cjk_glyphs(self):
        """
        Check that CJK languages track double-width glyphs as expected.
        """
        screen = MagicMock(spec=Screen, colours=8, unicode_aware=True)
        canvas = Canvas(screen, 10, 40, 0, 0)

        # Check underflow and overflow work as expected for CJK languages.
        # These languages actually use two characters for some glyphs, so when you query the
        # contents, you will see the value for both characters.  Also, most terminals don't like
        # displaying half glyphs, so asciimatics doesn't even allow it.
        canvas.print_at("ab", -1, 0)
        canvas.print_at("cd", canvas.width - 1, 0)
        self.assert_line_equals(canvas, "b                                      c")

        canvas.reset()
        canvas.print_at("你確", -1, 0)
        canvas.print_at("你確", canvas.width - 1, 0)
        self.assert_line_equals(canvas, u" 確確                                     ")

    def test_cjk_glyphs_overwrite(self):
        """
        Check that CJK languages delete half-glyphs correctly.
        """
        screen = Screen.open(unicode_aware=True)
        screen.print_at("aaaa", 0, 0)
        screen.print_at("你確", 0, 1)
        screen.print_at("bbbb", 0, 2)
        screen.refresh()
        screen.print_at("cccc", 0, 0)
        screen.print_at("你確", 1, 1)
        screen.print_at("dddd", 0, 2)
        screen.refresh()

        # Half-glyph appears as an "x" to show error and then double-width glyphs are returned
        # twice, reflecting their extra width.
        self.assert_line_equals(screen, u"x你你確確 ", y=1, length=6)

    def test_save_signal_state(self):
        """Tests that the signal state class works properly.

        The _SignalState class must set, save, and restore signals
        when needed.
        """
        if sys.platform == "win32":
            self.skipTest("Windows does not have signals.")

        def dummy_handler():
            """Assign dummy handler to an arbitrary signal."""
            pass
        self.assertNotEqual(signal.getsignal(signal.SIGWINCH), dummy_handler)
        signal_state = _SignalState()
        signal_state.set(signal.SIGWINCH, dummy_handler)
        self.assertEqual(signal.getsignal(signal.SIGWINCH), dummy_handler)
        signal_state.restore()
        self.assertNotEqual(signal.getsignal(signal.SIGWINCH), dummy_handler)

    def test_signal(self):
        """
        Check that signals are restored after using _CursesScreen
        """
        if sys.platform == "win32":
            self.skipTest("Windows does not have signals.")

        def dummy_signal_handler():
            """Dummy previous signal handler."""
            pass
        outer_state = _SignalState()
        self.assertNotEqual(signal.getsignal(signal.SIGWINCH), dummy_signal_handler)
        outer_state.set(signal.SIGWINCH, dummy_signal_handler)
        self.assertEqual(signal.getsignal(signal.SIGWINCH), dummy_signal_handler)
        Screen.wrapper(self.signal_check)
        self.assertEqual(signal.getsignal(signal.SIGWINCH), dummy_signal_handler)
        outer_state.restore()
        self.assertNotEqual(signal.getsignal(signal.SIGWINCH), dummy_signal_handler)

    def signal_check(self, screen):
        """Dummy callback for screen wrapper."""
        self.assertEqual(signal.getsignal(signal.SIGWINCH), screen._resize_handler)


if __name__ == '__main__':
    unittest.main()
