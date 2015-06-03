Introduction
============

Asciimatics is a package to help people create simple ASCII animations on any
platform.  It is licensed under the Apache Software Foundation License 2.0.

It originated from some work that I did on PiConga to create a retro text
credits roll for the project.  This worked so well, I re-used it for another
project.  At that point I felt it might be fun to share with others.


Why?
----

Why not?  It brings a little joy to anyone who was programming in the 80s...
Oh and it provides a single cross-platform Python class to do all basic console
function, including:

* Coloured/styled text - including 256 colour terminals
* Cursor positioning
* Keyboard input (without blocking or echoing)
* Detecting and handling when the console resizes

Currently this API has been proven to work on CentOS 6 & 7 and Windows 7,
though it should work for any platform that provides a working curses
implementation.

Installation
------------

To install asciimatics, simply:

.. code-block:: bash

    $ pip install asciimatics


How to use it?
--------------

Create a curses window, create a :py:obj:`.Screen`, put together a :py:obj:`.Scene`
using some :py:obj:`.Effect` objects and then get the Screen to play it.  An Effect
will typically need to display some pre-formatted text.  This is usually
provided by a :py:obj:`.Renderer`.  For example:

.. code-block:: python

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

Contributing to this project
----------------------------

So you want to join in?  Great!  There's a few ground rules...

#. Before you do anything else, read up on the design.  You should find all you
   need in the 4 base classes - i.e. Screen, Scene, Effect and Renderer.
#. Make sure you consider why your new Effect can't be handled by a
   combination of a new Renderer and the :py:obj:`.Print` Effect.  For example,
   dynamic Effects such as :py:obj:`.Snow` depend on the current Screen state
   to render each new image.
#. Go the extra yard.  This project started on a whim to share the joy of
   someone starting out programming back in the 1980s.  How do you sustain
   that joy?  Not just by writing code that works, but by writing code that
   other programmers will admire.
#. Make sure that your code is
   `PEP-8 <https://www.python.org/dev/peps/pep-0008/>`_ compliant.  Tools
   such as flake8 or editors like pycharm really help here.

When you've got something you're happy with, please feel free to submit a pull
request at https://github.com/peterbrittain/asciimatics/issues.
