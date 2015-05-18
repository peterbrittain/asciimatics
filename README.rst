ASCIIMATICS
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

Create a curses window, create a Screen, put together a Scene using some
Effects and then get the Screen to play it.

.. code-block:: python

    import curses
    from asciimatics.effects import Cycle, Stars
    from asciimatics.renderers import FigletText
    from asciimatics.scene import Scene
    from asciimatics.screen import Screen
    
    def demo(win):
        screen = Screen.from_curses(win)
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

And you should see something like this:

.. image:: https://asciinema.org/a/18756.png
   :alt: asciicast
   :target: https://asciinema.org/a/18756?autoplay=1

Documentation
-------------

Documentation is available at http://asciimatics.readthedocs.org/en/latest/

More Examples
-------------

More examples of what you can do are available in the project samples directory, hosted on GitHub.  See https://github.com/peterbrittain/asciimatics/tree/master/samples.

Alternatively, you can browse the gallery at https://github.com/peterbrittain/asciimatics/wiki.

Bugs
----

You can report bugs at https://github.com/peterbrittain/asciimatics/issues

Contributing to the project
---------------------------

If you'd like to take part in this project (and see your name in the credits!), check out the guidance at
http://asciimatics.readthedocs.org/en/latest/intro.html#contributing-to-this-project.
