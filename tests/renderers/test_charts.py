# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import unittest
from asciimatics.constants import ASCII_LINE, SINGLE_LINE
from asciimatics.renderers import BarChart, VBarChart
from asciimatics.screen import Screen

# Internal test function for rendering
def fn(x):
    return lambda: x


class TestBarChart(unittest.TestCase):
    def test_defaults(self):
        renderer = BarChart(7, 17, [fn(10), fn(5)])
        expected = (
            "╔═══════════════╗\n"
            "║               ║\n"
            "║  │##########  ║\n"
            "║  │            ║\n"
            "║  │#####       ║\n"
            "║               ║\n"
            "╚═══════════════╝")
        self.assertEqual(str(renderer), expected)
        self.assertEqual("\n".join(renderer.images[0]), expected)

    def test_styles(self):
        renderer = BarChart(7, 17, [fn(10), fn(5)])
        renderer.border_style = SINGLE_LINE
        self.assertEqual(str(renderer), 
            "┌───────────────┐\n"
            "│               │\n"
            "│  │##########  │\n"
            "│  │            │\n"
            "│  │#####       │\n"
            "│               │\n"
            "└───────────────┘")

        renderer.border_style = ASCII_LINE
        renderer.axes_style = ASCII_LINE
        self.assertEqual(str(renderer), 
            "+---------------+\n"
            "|               |\n"
            "|  |##########  |\n"
            "|  |            |\n"
            "|  |#####       |\n"
            "|               |\n"
            "+---------------+")

    def test_args_no_scale(self):
        renderer = BarChart(3, 10, [fn(10), fn(5)], char='=', border=False, axes=BarChart.NO_AXIS)
        self.assertEqual(str(renderer), 
                "==========\n" +
                "          \n" +
                "=====     ")

        renderer = BarChart(7, 16, [fn(10), fn(5)], char='=', axes=BarChart.NO_AXIS)
        self.assertEqual(str(renderer), 
            "╔══════════════╗\n"
            "║              ║\n"
            "║  ==========  ║\n"
            "║              ║\n"
            "║  =====       ║\n"
            "║              ║\n"
            "╚══════════════╝")

        renderer = BarChart(7, 17, [fn(10), fn(5)], char='=', axes=BarChart.Y_AXIS)
        self.assertEqual(str(renderer), 
            "╔═══════════════╗\n"
            "║               ║\n"
            "║  │==========  ║\n"
            "║  │            ║\n"
            "║  │=====       ║\n"
            "║               ║\n"
            "╚═══════════════╝")

        renderer = BarChart(8, 17, [fn(10), fn(5)], char='=', axes=BarChart.BOTH)
        self.assertEqual(str(renderer), 
            "╔═══════════════╗\n"
            "║               ║\n"
            "║  │==========  ║\n"
            "║  │            ║\n"
            "║  │=====       ║\n"
            "║  └──────────  ║\n"
            "║               ║\n"
            "╚═══════════════╝")

        renderer = BarChart(8, 21, [fn(10), fn(5)], char='=', axes=BarChart.BOTH, 
            keys=['a', 'bbb'])
        self.assertEqual(str(renderer), 
            "╔═══════════════════╗\n"
            "║                   ║\n"
            "║    a │==========  ║\n"
            "║      │            ║\n"
            "║  bbb │=====       ║\n"
            "║      └──────────  ║\n"
            "║                   ║\n"
            "╚═══════════════════╝")

        renderer = BarChart(9, 21, [fn(10), fn(5)], char='=', axes=BarChart.BOTH, 
            keys=['a', 'bbb'], labels=True)
        self.assertEqual(str(renderer), 
            "╔═══════════════════╗\n"
            "║                   ║\n"
            "║    a │==========  ║\n"
            "║      │            ║\n"
            "║  bbb │=====       ║\n"
            "║      └──────────  ║\n"
            "║       0       10  ║\n"
            "║                   ║\n"
            "╚═══════════════════╝")

        renderer = BarChart(9, 21, [fn(10), fn(4)], char='=', axes=BarChart.BOTH, 
            keys=['a', 'bbb'], labels=True, intervals=5)
        self.assertEqual(str(renderer), 
            "╔═══════════════════╗\n"
            "║                   ║\n"
            "║    a │==========  ║\n"
            "║      │    │       ║\n"
            "║  bbb │====│       ║\n"
            "║      └────┴─────  ║\n"
            "║       0   5   10  ║\n"
            "║                   ║\n"
            "╚═══════════════════╝")

        renderer = BarChart(8, 21, [fn(10), fn(4)], char='=', axes=BarChart.BOTH, 
            keys=['a', 'bbb'], labels=True, intervals=5, gap=0)
        self.assertEqual(str(renderer), 
            "╔═══════════════════╗\n"
            "║                   ║\n"
            "║    a │==========  ║\n"
            "║  bbb │====│       ║\n"
            "║      └────┴─────  ║\n"
            "║       0   5   10  ║\n"
            "║                   ║\n"
            "╚═══════════════════╝")

    def test_scale(self):
        renderer = BarChart(5, 41, [fn(5), fn(10)], scale=10.0, axes=BarChart.BOTH,
                            intervals=2.5, labels=True, border=False)
        self.assertEqual(
            str(renderer),
            # 1234567890123456789!12345678901234567890
            "│####################         │          \n" +
            "│         │         │         │          \n" +
            "│########################################\n" +
            "└─────────┴─────────┴─────────┴──────────\n" +
            " 0       2.5       5.0       7.5     10.0")

    def test_gradients(self):
        gradients = [
            (2, Screen.COLOUR_GREEN, Screen.COLOUR_BLUE),
            (4, Screen.COLOUR_YELLOW),
            (5, Screen.COLOUR_RED),
        ]

        renderer = BarChart(3, 5, [fn(5), fn(3), fn(1)], border=False, axes=BarChart.NO_AXIS,
            gap=0, gradient=gradients)

        self.assertEqual(
            renderer.rendered_text, 
            (    #12345
                ['#####', '###  ', '#    '], 
                [ 
                    [   # First bar colour sets
                        (2, 2, 4),     # 2 ticks of green with blue background
                        (2, 2, 4), 
                        (3, 2, 0),     # 2 ticks of yellow with black background
                        (3, 2, 0), 
                        (1, 2, 0)      # 1 tick of red with black background
                    ], 
                    [   # Second bar colour sets
                        (2, 2, 4),     # 2 ticks of green with blue background
                        (2, 2, 4), 
                        (3, 2, 0),     # 2 ticks of yellow with black background
                        (None, 0, 0),  # 2 ticks empty
                        (None, 0, 0), 
                    ],
                    [   # Third bar colour sets
                        (2, 2, 4),     # 1 tick of green with blue background
                        (None, 0, 0),  # 4 ticks empty
                        (None, 0, 0), 
                        (None, 0, 0), 
                        (None, 0, 0), 
                    ],
                ]
            )
        )


class TestVBarChart(unittest.TestCase):
    def test_defaults(self):
        renderer = VBarChart(15, 9, [fn(10), fn(5)])
        expected = (
            "╔═══════╗\n" 
            "║       ║\n" 
            "║  #    ║\n"   # 1
            "║  #    ║\n"   # 2
            "║  #    ║\n"   # 3
            "║  #    ║\n"   # 4
            "║  #    ║\n"   # 5
            "║  # #  ║\n"   # 6
            "║  # #  ║\n"   # 7
            "║  # #  ║\n"   # 8
            "║  # #  ║\n"   # 9
            "║  # #  ║\n"   # 10
            "║  ───  ║\n"
            "║       ║\n"
            "╚═══════╝")
        self.assertEqual(str(renderer), expected)
        self.assertEqual("\n".join(renderer.images[0]), expected)

    def test_args_no_scale(self):
        renderer = VBarChart(10, 3, [fn(10), fn(5)], border=False, axes=BarChart.NO_AXIS)
        self.assertEqual(str(renderer), 
            "#  \n" +      # 1
            "#  \n" +      # 2
            "#  \n" +      # 3
            "#  \n" +      # 4
            "#  \n" +      # 5
            "# #\n" +      # 6
            "# #\n" +      # 7
            "# #\n" +      # 8
            "# #\n" +      # 9
            "# #")         # 10

        renderer = VBarChart(14, 9, [fn(10), fn(5)], char="*", axes=BarChart.NO_AXIS)
        self.assertEqual(str(renderer), 
            "╔═══════╗\n" +
            "║       ║\n" +
            "║  *    ║\n" +   # 1
            "║  *    ║\n" +   # 2
            "║  *    ║\n" +   # 3
            "║  *    ║\n" +   # 4
            "║  *    ║\n" +   # 5
            "║  * *  ║\n" +   # 6
            "║  * *  ║\n" +   # 7
            "║  * *  ║\n" +   # 8
            "║  * *  ║\n" +   # 9
            "║  * *  ║\n" +   # 10
            "║       ║\n"
            "╚═══════╝")

        renderer = VBarChart(15, 9, [fn(10), fn(5)], char="*", axes=BarChart.X_AXIS)
        self.assertEqual(str(renderer), 
            "╔═══════╗\n" +
            "║       ║\n" +
            "║  *    ║\n" +   # 1
            "║  *    ║\n" +   # 2
            "║  *    ║\n" +   # 3
            "║  *    ║\n" +   # 4
            "║  *    ║\n" +   # 5
            "║  * *  ║\n" +   # 6
            "║  * *  ║\n" +   # 7
            "║  * *  ║\n" +   # 8
            "║  * *  ║\n" +   # 9
            "║  * *  ║\n" +   # 10
            "║  ───  ║\n"
            "║       ║\n"
            "╚═══════╝")

        renderer = VBarChart(15, 10, [fn(10), fn(5)], char="*", axes=BarChart.BOTH_AXES)
        self.assertEqual(str(renderer), 
            "╔════════╗\n" +
            "║        ║\n" +
            "║  │*    ║\n" +   # 1
            "║  │*    ║\n" +   # 2
            "║  │*    ║\n" +   # 3
            "║  │*    ║\n" +   # 4
            "║  │*    ║\n" +   # 5
            "║  │* *  ║\n" +   # 6
            "║  │* *  ║\n" +   # 7
            "║  │* *  ║\n" +   # 8
            "║  │* *  ║\n" +   # 9
            "║  │* *  ║\n" +   # 10
            "║  └───  ║\n"
            "║        ║\n"
            "╚════════╝")

        renderer = VBarChart(16, 10, [fn(10), fn(5)], char="*", axes=BarChart.BOTH_AXES, 
            keys=['a', 'b'])
        self.assertEqual(str(renderer), 
            "╔════════╗\n" +
            "║        ║\n" +
            "║  │*    ║\n" +   # 1
            "║  │*    ║\n" +   # 2
            "║  │*    ║\n" +   # 3
            "║  │*    ║\n" +   # 4
            "║  │*    ║\n" +   # 5
            "║  │* *  ║\n" +   # 6
            "║  │* *  ║\n" +   # 7
            "║  │* *  ║\n" +   # 8
            "║  │* *  ║\n" +   # 9
            "║  │* *  ║\n" +   # 10
            "║  └───  ║\n"
            "║   a b  ║\n"
            "║        ║\n"
            "╚════════╝")

        renderer = VBarChart(16, 13, [fn(10), fn(5)], char="*", axes=BarChart.BOTH_AXES, 
            keys=['a', 'b'], labels=True)
        self.assertEqual(str(renderer), 
            "╔═══════════╗\n" +
            "║           ║\n" +
            "║   10│*    ║\n" +   # 1
            "║     │*    ║\n" +   # 2
            "║     │*    ║\n" +   # 3
            "║     │*    ║\n" +   # 4
            "║     │*    ║\n" +   # 5
            "║     │* *  ║\n" +   # 6
            "║     │* *  ║\n" +   # 7
            "║     │* *  ║\n" +   # 8
            "║     │* *  ║\n" +   # 9
            "║    0│* *  ║\n" +   # 10
            "║     └───  ║\n"
            "║      a b  ║\n"
            "║           ║\n"
            "╚═══════════╝")

        renderer = VBarChart(16, 13, [fn(10), fn(4)], char="*", axes=BarChart.BOTH_AXES, 
            keys=['a', 'b'], labels=True, intervals=5)
        self.assertEqual(str(renderer), 
            "╔═══════════╗\n" +
            "║           ║\n" +
            "║   10├*──  ║\n" +   # 1
            "║     │*    ║\n" +   # 2
            "║     │*    ║\n" +   # 3
            "║     │*    ║\n" +   # 4
            "║     │*    ║\n" +   # 5
            "║    5├*──  ║\n" +   # 6
            "║     │* *  ║\n" +   # 7
            "║     │* *  ║\n" +   # 8
            "║     │* *  ║\n" +   # 9
            "║    0│* *  ║\n" +   # 10
            "║     └───  ║\n"
            "║      a b  ║\n"
            "║           ║\n"
            "╚═══════════╝")

        renderer = VBarChart(16, 12, [fn(10), fn(4)], char="*", axes=BarChart.BOTH_AXES, 
            keys=['a', 'b'], labels=True, intervals=5, gap=0)
        self.assertEqual(str(renderer), 
            "╔══════════╗\n" +
            "║          ║\n" +
            "║   10├*─  ║\n" +   # 1
            "║     │*   ║\n" +   # 2
            "║     │*   ║\n" +   # 3
            "║     │*   ║\n" +   # 4
            "║     │*   ║\n" +   # 5
            "║    5├*─  ║\n" +   # 6
            "║     │**  ║\n" +   # 7
            "║     │**  ║\n" +   # 8
            "║     │**  ║\n" +   # 9
            "║    0│**  ║\n" +   # 10
            "║     └──  ║\n"
            "║      ab  ║\n"
            "║          ║\n"
            "╚══════════╝")

    def test_scale(self):
        unittest.util._MAX_LENGTH = 160

        renderer = VBarChart(11, 6, [fn(15), fn(5)], axes=BarChart.BOTH, labels=True, 
            intervals=10, border=False, scale=20, gap=0)
        self.assertEqual(str(renderer), 
            #123456
            " 20├──\n" +   # 10
            "   │  \n" +   # 9
            "   │# \n" +   # 8
            "   │# \n" +   # 7
            "   │# \n" +   # 6
            " 10├#─\n" +   # 5
            "   │# \n" +   # 4
            "   │##\n" +   # 3
            "   │##\n" +   # 2
            "  0│##\n" +   # 1
            "   └──")

        renderer = VBarChart(11, 7, [fn(1.5), fn(0.5)], axes=BarChart.BOTH, labels=True, 
            intervals=0.5, border=False, scale=2.0, gap=0)
        self.assertEqual(str(renderer), 
            #1234567
            ' 2.0├──\n' +  # 10
            '    │  \n' +  # 9
            ' 1.5├#─\n' +  # 8
            '    │# \n' +  # 7
            '    │# \n' +  # 6
            ' 1.0├#─\n' +  # 5
            '    │# \n' +  # 4
            ' 0.5├#─\n' +  # 3
            '    │##\n' +  # 2
            '   0│##\n' +  # 1
            '    └──')

    def test_gradients(self):
        gradients = [
            (2, Screen.COLOUR_GREEN, Screen.COLOUR_BLUE),
            (4, Screen.COLOUR_YELLOW),
            (5, Screen.COLOUR_RED),
        ]

        renderer = VBarChart(5, 3, [fn(5), fn(3), fn(1)], border=False, axes=BarChart.NO_AXIS,
            gap=0, gradient=gradients)

        # Gradient vertical bar chart, 3 bars turns into 5 rows:
        #
        #        R00
        #        Y00
        #        GG0    <- background on Green squares is Blue
        #        GG0
        #        GGG 
        #
        unittest.util._MAX_LENGTH = 160
        self.assertEqual(
            renderer.rendered_text, 
            (
                ['#  ', '#  ', '## ', '## ', '###'], 
                [
                    [
                        (1, 2, 0),
                        (None, 0, 0),
                        (None, 0, 0)
                    ], 
                    [
                        (3, 2, 0),
                        (None, 0, 0),
                        (None, 0, 0)
                    ],
                    [
                        (2, 2, 4),
                        (2, 2, 4),
                        (None, 0, 0)
                    ],
                    [
                        (2, 2, 4),
                        (2, 2, 4),
                        (None, 0, 0)
                    ],
                    [
                        (2, 2, 4),
                        (2, 2, 4),
                        (2, 2, 4)
                    ]
                ]
            )
        )

if __name__ == '__main__':
    unittest.main()
