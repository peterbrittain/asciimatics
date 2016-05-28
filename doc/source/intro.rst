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
#. If writing a new Effect, consider why it can't be handled by a
   combination of a new Renderer and the :py:obj:`.Print` Effect.  For example,
   dynamic Effects such as :py:obj:`.Snow` depend on the current Screen state
   to render each new image.
#. Go the extra yard.  This project started on a whim to share the joy of
   someone starting out programming back in the 1980s.  How do you sustain
   that joy?  Not just by writing code that works, but by writing code that
   other programmers will admire.
#. Make sure that your code is
   `PEP-8 <https://www.python.org/dev/peps/pep-0008/>`_ compliant.  Tools
   such as flake8 and pylint or editors like pycharm really help here.
#. Please run the existing unit tests against your new code to make sure that
   it still works as expected.  I normally use nosetests to do this.  In
   addition, i fyou are adding significant extra function, please write some
   new tests for your code.

When you've got something you're happy with, please feel free to submit a pull
request at https://github.com/peterbrittain/asciimatics/issues.
