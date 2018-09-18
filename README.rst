
.. image:: https://travis-ci.org/peterbrittain/asciimatics.svg?branch=master
    :target: https://travis-ci.org/peterbrittain/asciimatics
    :alt: Linux build status

.. image:: https://ci.appveyor.com/api/projects/status/n68nk47ku35pafru?svg=true&passingText=Windows%20-%20passing
    :target: https://ci.appveyor.com/project/peterbrittain/asciimatics
    :alt: Windows build status

.. image:: https://api.codacy.com/project/badge/Grade/b79f9a63d15141f3ae5fe8d4eae78874
   :target: https://app.codacy.com/project/pab/asciimatics/dashboard
   :alt: Code Health

.. image:: https://coveralls.io/repos/github/peterbrittain/asciimatics/badge.svg?branch=master
    :target: https://coveralls.io/github/peterbrittain/asciimatics?branch=master
    :alt: Code Coverage

.. image:: https://img.shields.io/pypi/v/asciimatics.svg
    :target: https://pypi.python.org/pypi/asciimatics
    :alt: Latest stable version

.. image:: https://badges.gitter.im/asciimatics/Lobby.svg
   :alt: Join the chat at https://gitter.im/asciimatics/Lobby
   :target: https://gitter.im/asciimatics/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

ASCIIMATICS
===========

Asciimatics is a package to help people create full-screen text UIs (from interactive forms to
ASCII animations) on any platform.  It is licensed under the Apache Software Foundation License 2.0.

Why?
----

Why not?  It brings a little joy to anyone who was programming in the 80s...  Oh and it provides a
single cross-platform Python class to do all the low-level console function you could ask for,
including:

* Coloured/styled text - including 256 colour terminals and unicode characters (even CJK languages)
* Cursor positioning
* Keyboard input (without blocking or echoing) including unicode support
* Mouse input (terminal permitting)
* Detecting and handling when the console resizes
* Screen scraping

In addition, it provides some simple, high-level APIs to provide more complex features including:

* Anti-aliased ASCII line-drawing
* Image to ASCII conversion - including JPEG and GIF formats
* Many animation effects - e.g. sprites, particle systems, banners, etc.
* Various widgets for text UIs - e.g. buttons, text boxes, radio buttons, etc.

Currently this package has been proven to work on CentOS 6 & 7, Raspbian (i.e. Debian wheezy),
Ubuntu 14.04, Windows 7, 8 & 10, OSX 10.11 and Android Marshmallow (courtesy of https://termux.com),
though it should also work for any other platform that provides a working curses implementation.

It should be implementation agnostic and has been successfully tested on the CPython and PyPy2.

(Please let me know if you successfully verified it on other platforms so that I can update this
list).

Installation
------------

Asciimatics supports Python versions 2 & 3.  For the precise list of tested versions,
refer to `pypi <https://pypi.python.org/pypi/asciimatics>`_.

To install asciimatics, simply install with `pip` as follows:

.. code-block:: bash

    $ pip install asciimatics

This should install all your dependencies for you.  If you don't use pip or it fails to install
them, you can install the dependencies directly using the packages listed in `requirements.txt
<https://github.com/peterbrittain/asciimatics/blob/master/requirements.txt>`_.
Additionally, Windows users (who aren't using `pip`) will need to install `pypiwin32`.

How to use it?
--------------
To use the low-level API, simply create a Screen and use it to print coloured text at any location,
or get mouse/keyboard input.  For example, here is a variant on the classic "hello world":

.. code-block:: python

    from random import randint
    from asciimatics.screen import Screen

    def demo(screen):
        while True:
            screen.print_at('Hello world!',
                            randint(0, screen.width), randint(0, screen.height),
                            colour=randint(0, screen.colours - 1),
                            bg=randint(0, screen.colours - 1))
            ev = screen.get_key()
            if ev in (ord('Q'), ord('q')):
                return
            screen.refresh()

    Screen.wrapper(demo)

That same code works on Windows, OSX and Linux and paves the way for all the higher level features.
These still need the Screen, but now you also create a Scene using some Effects and then get the
Screen to play it.  For example, this code:

.. code-block:: python

    from asciimatics.effects import Cycle, Stars
    from asciimatics.renderers import FigletText
    from asciimatics.scene import Scene
    from asciimatics.screen import Screen

    def demo(screen):
        effects = [
            Cycle(
                screen,
                FigletText("ASCIIMATICS", font='big'),
                int(screen.height / 2 - 8)),
            Cycle(
                screen,
                FigletText("ROCKS!", font='big'),
                int(screen.height / 2 + 3)),
            Stars(screen, 200)
        ]
        screen.play([Scene(effects, 500)])

    Screen.wrapper(demo)

should produce something like this:

.. image:: https://asciinema.org/a/18756.png
   :alt: asciicast
   :target: https://asciinema.org/a/18756?autoplay=1

Or maybe you're looking to create a TUI?  In which case this
`simple code <https://github.com/peterbrittain/asciimatics/blob/master/samples/contact_list.py>`__
will give you this:

.. image:: https://asciinema.org/a/45946.png
    :alt: contact list sample
    :target: https://asciinema.org/a/45946?autoplay=1

Documentation
-------------

Full documentation of all the above (and more!) is available at http://asciimatics.readthedocs.org/

More examples
-------------

More examples of what you can do are available in the project samples directory, hosted on GitHub.
See https://github.com/peterbrittain/asciimatics/tree/v1.10/samples.

To view them, simply download these files and then simply run them directly with `python`.
Alternatively, you can browse recordings of many of the samples in the gallery at
https://github.com/peterbrittain/asciimatics/wiki.

Bugs and enhancements
---------------------

If you have a problem, please check out the troubleshooting guide at
http://asciimatics.readthedocs.io/en/latest/troubleshooting.html.  If this doesn't solve your
problem, you can report bugs (or submit enhancement requests) at
https://github.com/peterbrittain/asciimatics/issues.

Alternatively, if you just have some questions, feel free to drop in at
https://gitter.im/asciimatics/Lobby.

Contributing to the project
---------------------------

If you'd like to take part in this project (and see your name in the credits!), check out the
guidance at http://asciimatics.readthedocs.org/en/latest/contributing.html

