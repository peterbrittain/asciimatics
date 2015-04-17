Introduction
===========

Asciimatics is a package to help people create simple ASCII animations using
curses.  It is licensed under the Apache Software Foundation License 2.0.

It originated from some work that I did on PiConga to create a retro text
credits roll for the project.  This worked so well, I re-used it for another
project.  At that point I felt it might be fun to share with others.


Why?
----

Why not?  It brings a little joy to anyone who was programming in the 80s...


Installation
------------

To install asciimatics, simply:

.. code-block:: bash

    $ pip install asciimatics


How to use it?
--------------

Create a curses window, create a :py:obj:`.Screen`, put together a :py:obj:`.Scene`
using some :py:obj:`.Effect` objects and then get the Screen to play it.  An Effect
Will typically need to display some text.  This is provided by a
:py:obj:`.Renderer`.  For example:

.. code-block:: python

    def demo(win):
        screen = Screen(win)
        effects = [
            Cycle(
                screen,
                FigletText("ASCIIMATICS", font='big'),
                screen.height / 2 - 8),
            Cycle(
                screen,
                FigletText("ROCKS!", font='big'),
                screen.height / 2 + 3),
            Stars(screen, 200)
        ]
        screen.play([Scene(effects, 500)])

    curses.wrapper(demo)
