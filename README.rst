ASCIIMATICS
===========

Asciimatics is a package to help people create full-screen ASCII animations on
any platform.  It is licensed under the Apache Software Foundation License 2.0.

It originated from some work that I did on PiConga to create a retro text
credits roll for the project.  This worked so well, I re-used it for another
project.  At that point I felt it might be fun to share with others.

Why?
----

Why not?  It brings a little joy to anyone who was programming in the 80s...
Oh and it provides a single cross-platform Python class to do all the console
function you could ask for, including:

* Coloured/styled text - including 256 colour terminals
* Cursor positioning
* Keyboard input (without blocking or echoing)
* Mouse input (terminal permitting)
* Detecting and handling when the console resizes
* Screen scraping
* Anti-aliased ASCII line-drawing
* Image to ASCII conversion - including JPEG and GIF formats
* Many animation effects - e.g. sprites, particle systems, banners, etc.

Currently this API has been proven to work on CentOS 6 & 7, Raspbian (i.e.
Debian wheezy), Ubuntu 14.04, Windows 7, 8 & 10 and OSX 10.11, though it should
also work for any other platform that provides a working curses implementation.  

(Please let me know if you successfully verified it on other platforms so
that I can update this list).

Installation
------------

Asciimatics supports Python versions 2 & 3.  For the precise list of tested
versions, refer to `pypi <https://pypi.python.org/pypi/asciimatics>`_.

To install asciimatics, simply install with `pip` as follows:

.. code-block:: bash

    $ pip install asciimatics

This should install all your dependencies for you.  If you don't use pip
or it fails to install them, you can install the dependencies directly 
using the packages listed in `requirements.txt 
<https://github.com/peterbrittain/asciimatics/blob/master/requirements.txt>`_.
Additionally, Windows users will need to install `pypiwin32`.

How to use it?
--------------

Create a Screen, put together a Scene using some Effects and then get the
Screen to play it.

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
                screen.height / 2 - 8),
            Cycle(
                screen,
                FigletText("ROCKS!", font='big'),
                screen.height / 2 + 3),
            Stars(screen, 200)
        ]
        screen.play([Scene(effects, 500)])
    
    Screen.wrapper(demo)

And you should see something like this:

.. image:: https://asciinema.org/a/18756.png
   :alt: asciicast
   :target: https://asciinema.org/a/18756?autoplay=1

Documentation
-------------

Documentation is available at http://asciimatics.readthedocs.org/

More examples
-------------

More examples of what you can do are available in the project samples
directory, hosted on GitHub.  See
https://github.com/peterbrittain/asciimatics/tree/master/samples.

To view them, simply download these files and then simply run them directly
with `python`.  Note that most can run on any platform, apart from:

* `not_curses.py` which is a demo of the deprecated `blessed` support on Linux
* `win_demo.py` which is a demo of the deprecated direct `win32console` support
  on Windows.

Alternatively, you can browse most of the samples in the gallery at
https://github.com/peterbrittain/asciimatics/wiki.

Bugs and enhancements
---------------------

You can report bugs and submit enhancement requests at
https://github.com/peterbrittain/asciimatics/issues.

Contributing to the project
---------------------------

If you'd like to take part in this project (and see your name in the credits!),
check out the guidance at
http://asciimatics.readthedocs.org/en/latest/intro.html#contributing-to-this-project.
