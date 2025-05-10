import unittest
import os
from asciimatics.renderers import AnsiArtPlayer, AsciinemaPlayer


class TestRendererPlayers(unittest.TestCase):
    def test_ansi_art(self):
        """
        Check that ansi art player works.
        """
        with AnsiArtPlayer(os.path.join(os.path.dirname(__file__), "test.ans"),
                           height=5, width=20) as renderer:
            self.assertEqual(
                str(renderer),
                "This is a test file \n" +
                "with ansi codes...  \n" +
                "                    \n" +
                "                    \n" +
                "                    ")
            self.assertEqual(
                str(renderer),
                "This is a test file \n" +
                "with ansi codes...  \n" +
                "Check               \n" +
                "here 2nd            \n" +
                "                    ")
            self.assertEqual(
                str(renderer),
                "This is a test file \n" +
                "            abab c  \n" +
                "dheck               \n" +
                "here 2nd            \n" +
                "cbdeefghab          ")
            self.assertEqual(
                str(renderer),
                "                    \n" +
                "                    \n" +
                "                    \n" +
                "123                 \n" +
                "                    ")

            # Check images just returns one frame.
            self.assertEqual(len(renderer.images), 1)

        # Test line stripping
        with AnsiArtPlayer(os.path.join(os.path.dirname(__file__), "test2.ans"),
                           height=2, width=10, rate=1, strip=True) as renderer:
            self.assertEqual(str(renderer), "One       \n          ")
            self.assertEqual(str(renderer), "OneTwo    \n          ")
            self.assertEqual(str(renderer), "OneTwoThre\neFourFive ")
            self.assertEqual(str(renderer), "eFourFiveS\nix        ")

    def test_asciinema(self):
        """
        Check that asciinema  player works.
        """
        with AsciinemaPlayer(os.path.join(os.path.dirname(__file__), "test.rec"), max_delay=0.1) as renderer:
            self.assertEqual(renderer.max_height, 18)
            self.assertEqual(renderer.max_width, 134)

            # Check can play the file to the end.
            for _ in range(700):
                a = str(renderer)
            self.assertEqual(a,
                "~/asciimatics/samples $ ls                                                                                                            \n" +
                "256colour.py   colour_globe.gif  fireworks.py    images.py        mapscache     plasma.py       rendering.py  test2.rec               \n" +
                "bars.py        contact_list.py   forms.log       interactive.py   noise.py      player.py       simple.py     tests.py                \n" +
                "basics.py      credits.py        forms.py        julia.py         pacman.png    python.png      tab_demo.py   top.py                  \n" +
                "bg_colours.py  experimental.py   globe.gif       kaleidoscope.py  pacman.py     quick_model.py  terminal.py   treeview.py             \n" +
                "cogs.py        fire.py           grumpy_cat.jpg  maps.py          particles.py  ray_casting.py  test.rec      xmas.py                 \n" +
                "~/asciimatics/samples $                                                                                                               \n" +
                "exit                                                                                                                                  \n" +
                "                                                                                                                                      \n" +
                "                                                                                                                                      \n" +
                "                                                                                                                                      \n" +
                "                                                                                                                                      \n" +
                "                                                                                                                                      \n" +
                "                                                                                                                                      \n" +
                "                                                                                                                                      \n" +
                "                                                                                                                                      \n" +
                "                                                                                                                                      \n" +
                "                                                                                                                                      ")

            # Check images just returns one frame.
            self.assertEqual(len(renderer.images), 1)

        # Check for unsupported format
        with self.assertRaises(RuntimeError):
            with AsciinemaPlayer(os.path.join(os.path.dirname(__file__), "test_bad.rec")) as renderer:
                pass


if __name__ == '__main__':
    unittest.main()
