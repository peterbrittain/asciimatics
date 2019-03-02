Introduction
============

Asciimatics is a package to help people create simple ASCII animations on any
platform.  It is licensed under the Apache Software Foundation License 2.0.


Why?
----

Why not?  It brings a little joy to anyone who was programming in the 80s...
Oh and it provides a single cross-platform Python class to do all the low-level
console function you could ask for, including:

* Coloured/styled text - including 256 colour terminals
* Cursor positioning
* Keyboard input (without blocking or echoing)
* Mouse input (terminal permitting)
* Detecting and handling when the console resizes
* Screen scraping

In addition, it provides some simple, high-level APIs to provide more complex
features including:

* Anti-aliased ASCII line-drawing
* Image to ASCII conversion - including JPEG and GIF formats
* Many animation effects - e.g. sprites, particle systems, banners, etc.
* Various widgets for text UIs - e.g. buttons, text boxes, radio buttons, etc.

Currently this API has been proven to work on CentOS 6 & 7, Raspbian (i.e.
Debian wheezy), Ubuntu 14.04, Windows 7, 8 & 10 and OSX 10.11, though it should
also work for any other platform that provides a working curses implementation.


Installation
------------

Asciimatics supports Python versions 2 & 3.  For a list of the precise
list of tested versions, see
`here <https://pypi.python.org/pypi/asciimatics>`__.

To install asciimatics, simply install with `pip`.  You can get it from
`here <http://pip.readthedocs.org/en/stable/installing/>`_ and then just run:

.. code-block:: bash

    $ pip install asciimatics

This should install all your dependencies for you.  If you don't use pip
or it fails to install them, you can install the dependencies directly
using the packages listed in `requirements.txt
<https://github.com/peterbrittain/asciimatics/blob/master/requirements.txt>`_.
Additionally, Windows users will need to install `pypiwin32`.

Quick start guide
-----------------

Once you have installed asciimatics as per the instructions above, simply
create a :py:obj:`.Screen`, put together a :py:obj:`.Scene` using some
:py:obj:`.Effect` objects and then get the Screen to play it.  An Effect
will typically need to display some pre-formatted text.  This is usually
provided by a :py:obj:`.Renderer`.  For example:

.. code-block:: python

    from asciimatics.screen import Screen
    from asciimatics.scene import Scene
    from asciimatics.effects import Cycle, Stars
    from asciimatics.renderers import FigletText

    def demo(screen):
        effects = [
            Cycle(
                screen,
                FigletText("ASCIIMATICS", font='big'),
                screen.height // 2 - 8),
            Cycle(
                screen,
                FigletText("ROCKS!", font='big'),
                screen.height // 2 + 3),
            Stars(screen, (screen.width + screen.height) // 2)
        ]
        screen.play([Scene(effects, 500)])

    Screen.wrapper(demo)

You can also use the :py:obj:`.Scene.session` class in two different ways.

1. Use it as a method decorator. Note that I use `screen=None` in this
example to prevent linting errors:

.. code-block:: python

    from asciimatics.screen import Screen
    from asciimatics.scene import Scene
    from asciimatics.effects import Cycle, Stars
    from asciimatics.renderers import FigletText

    @Screen.session
    def demo(screen=None):
        effects = [
            Cycle(
                screen,
                FigletText("ASCIIMATICS", font='big'),
                screen.height // 2 - 8),
            Cycle(
                screen,
                FigletText("ROCKS!", font='big'),
                screen.height // 2 + 3),
            Stars(screen, (screen.width + screen.height) // 2)
        ]
        screen.play([Scene(effects, 500)])

    demo()

2. Use the `with` keyword:

.. code-block:: python

    from asciimatics.screen import Screen
    from asciimatics.scene import Scene
    from asciimatics.effects import Cycle, Stars
    from asciimatics.renderers import FigletText

    def demo():
        with Screen.session() as screen:
            effects = [
                Cycle(
                    screen,
                    FigletText("ASCIIMATICS", font='big'),
                    screen.height // 2 - 8),
                Cycle(
                    screen,
                    FigletText("ROCKS!", font='big'),
                    screen.height // 2 + 3),
                Stars(screen, (screen.width + screen.height) // 2)
            ]
            screen.play([Scene(effects, 500)])

    demo()
