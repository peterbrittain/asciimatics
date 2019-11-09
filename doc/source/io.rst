Basic Input/Output
==================

Creating a Screen
-----------------
The starting point for any asciimatics program is the :py:obj:`.Screen` object.  It can most easily
be obtained from the :py:meth:`.wrapper` static method.  This will handle all the necessary
initialization for your environment and pass the constructed Screen into the specified function.
For example:

.. code-block:: python

    from asciimatics.screen import Screen
    from time import sleep

    def demo(screen):
        screen.print_at('Hello world!', 0, 0)
        screen.refresh()
        sleep(10)

    Screen.wrapper(demo)

You can also use the :py:obj:`.ManagedScreen` class as a function decorator to achieve the same thing
as the above.  For example:

.. code-block:: python

    from asciimatics.screen import ManagedScreen
    from asciimatics.scene import Scene
    from asciimatics.effects import Cycle, Stars
    from asciimatics.renderers import FigletText

    @ManagedScreen
    def demo(screen=None):
        screen.print_at('Hello world!', 0, 0)
        screen.refresh()
        sleep(10)

    demo()

Or you can also use it as a context manager (i.e. using the `with` keyword).  For example:

.. code-block:: python

    from asciimatics.screen import ManagedScreen
    from asciimatics.scene import Scene
    from asciimatics.effects import Cycle, Stars
    from asciimatics.renderers import FigletText

    def demo():
        with ManagedScreen() as screen:
            screen.print_at('Hello world!', 0, 0)
            screen.refresh()
            sleep(10)

    demo()

If you need more control than this allows, you can fall back to using :py:meth:`.open`, but then
you have to call :py:meth:`.close` before exiting your application to restore the environment.

Output
------
Once you have a Screen, you probably want to ensure that it is clear before you do anything.  To
do this call :py:meth:`~.Screen.clear`.  Now that it's blank, the simplest way to output text is
using the :py:meth:`~.Screen.print_at` method.  This allows you to place a string at a desired
location in a specified colour.  The coordinates are zero-indexed starting at the top left of the
screen and move down and right, so the example above displays `Hello world!` at (0, 0) which is the
top left of the screen.

Colours
^^^^^^^
There is a long history to terminals and this is no more obvious than when it comes to colours.
Original terminals had limited colours, and so used attributes to change the format, using effects
like bold, underline and reverse video.  As time wore on, more colours were added and you can get
full 24 bit colour on some terminals.

For now, asciimatics limits itself to a maximum of the 256 colour palette.  You can find how many
colours your terminal supports by looking at the :py:obj:`~.Screen.colours` property.  These days
most terminals will zupport a minimum of 8 colours.  These are defined by the `COLOUR_xxx` constants
in the Screen class.  The full list is as follows:

.. code-block:: python

    COLOUR_BLACK = 0
    COLOUR_RED = 1
    COLOUR_GREEN = 2
    COLOUR_YELLOW = 3
    COLOUR_BLUE = 4
    COLOUR_MAGENTA = 5
    COLOUR_CYAN = 6
    COLOUR_WHITE = 7

These should always work for you as background and foreground colours (even on Windows).  For many
systems you can also use the attributes (see later) to double the number of foreground colours.

If you have a display capable of handling more than these (e.g. 256 colour xterm) you can use the
indexes of the colours for that display directly instead.  For a full list of the colour indeces,
look `here <https://askubuntu.com/a/821163/1014276>`__.

When creating effects that use these extra colours, it is recommended that you also support a
reduced colour mode, using just the 8 common colours.  For an example of how to do this, see the
:py:obj:`.Rainbow` class.

Attributes
^^^^^^^^^^
Attributes are a way of modifying the displayed text in some basic ways that early hardware
terminals supported before they had colours.  Most systems don't use hardware terminals any more,
but the concept persists in all native console APIs and so is also used here.

Supported attributes are defined by the `A_xxx` constants in the Screen class.  The full list is as
follows:

.. code-block:: python

    A_BOLD = 1
    A_NORMAL = 2
    A_REVERSE = 3
    A_UNDERLINE = 4

Most systems will support bold (a.k.a bright), normal and reverse attributes.  Others are capable
of more, but you will have difficulties using them in a cross-platform manner and so they are
deprecated. The attribute is just another parameter to `print_at`.  For example:

.. code-block:: python

    # Bright green text
    screen.print_at('Hello world!', 0, 0, COLOUR_GREEN, A_BOLD)

Multicoloured strings
^^^^^^^^^^^^^^^^^^^^^
If you want to do something more complex, you can use the :py:meth:`~.Screen.paint` method to
specify a colour map for each character to be displayed.  This must be a list of colour/attribute
values (tuples or lists) that is at least as long as the text to be displayed.  This method is
typically used for displaying complex, multi-coloured text from a Renderer.  See
:ref:`animation-ref` for more details.

Unicode support
^^^^^^^^^^^^^^^
As of V1.7, asciimatics is officially misleadingly named!  It has support for unicode input and
output.  Just use a unicode literal where you would previously have used a string.  For example:

.. code-block:: python

    # Should have a telephone at the start...
    screen.print_at(u'☎ Call me!', 0, 0, COLOUR_GREEN, A_BOLD)

If your system is configured to support unicode, this should be output correctly.  However, not all
systems will work straight out of the box.  See :ref:`unicode-issues-ref` for more details on how
to fix this.

Refreshing the Screen
---------------------
Just using the above methods to output to screen isn't quite enough.  The Screen maintains a buffer
of what is to be displayed and will only actually display it once the :py:meth:`~.Screen.refresh`
method is called.  This is done to reduce flicker on the display device as new content is created.

Applications are required to re-render everything that needs to be displayed and then call refresh
when all the new content is ready.  Note that the :py:meth:`.play` and :py:meth:`.draw_next_frame`
methods will do this for you automatically at the end of each frame, so you don't need to call it
again inside your animations.

Input
-----
To handle user input, use the :py:meth:`.get_event` method.  This instantly returns the latest
key-press or mouse event, without waiting for a new line and without echoing it to screen (for
keyboard events).  If there is no event available, it will return `None`.

The exact class returned depends on the event.  It will be either :py:obj:`.KeyboardEvent` or
:py:obj:`.MouseEvent`.  Handling of each is covered below.

If you wish to wait until some input is available, you can use the :py:meth:`.wait_for_input` method
to block execution and then call :py:meth:`.get_event` to retrieve the input.

KeyboardEvent
^^^^^^^^^^^^^
This event is triggered for any key-press, including auto repeat when keys are held down.
``key_code`` is the ordinal representation of the key (taking into account keyboard state - e.g.
caps lock) if possible, or an extended key code (the ``KEY_xxx`` constants in the Screen class)
where not.

For example, if you press 'a' normally :py:meth:`.get_event` will return a KeyboardEvent with
``key_code`` 97, which is ``ord('a')``.  If you press the same key with caps lock on, you will get
65, which is ``ord('A')``.  If you press 'F7' you will always get ``KEY_F7`` irrespective of the
caps lock.

The control key (CTRL) on a keyboard returns control codes (the first 31 codes in the ASCII table).
You can calculate the control code for any key using the :py:meth:`.ctrl` method.  Note that not
all systems will return control codes for all keys, so this function can return None if asciimatics
doesn't believe the key will work.  For best system compatibility, stick to the control codes for
alphabetical characters - i.e. "A" to "Z".

As of V1.7, you can also get keyboard events for Unicode characters outside the ASCII character
set.  These will also return the ordinal representation of the unicode character, just like the
previous support for ASCII characters.

If you are seeing random garbage instead, your system is probably not correctly configured for
unicode.  See :ref:`unicode-issues-ref` for how to fix this.

MouseEvent
^^^^^^^^^^
This event is triggered for any mouse movement or button click.  The current coordinates of the
mouse on the Screen are stored in the ``x`` and ``y`` properties.  If a button was clicked, this is
tracked by the ``buttons`` property.  Allowed values for the buttons are ``LEFT_CLICK``,
``RIGHT_CLICK`` and ``DOUBLE_CLICK``.

.. warning::

    In general, Windows will report all of these straight out of the box.  Linux will only report
    mouse events if you are using a terminal that supports mouse events (e.g. xterm) in the
    terminfo database.  Even then, not all terminals report all events.  For example, the standard
    xterm function is just to report button clicks.  If you need your application to handle mouse
    move events too, you will need to use a terminal that supports the additional extensions - e.g.
    the xterm-1003 terminal type.  See :ref:`mouse-issues-ref` for more details on how to fix this.

Screen Resizing
---------------
It is not possible to change the Screen size through your program.  However, the user may resize
their terminal or console while your program is running.  Asciimatics will continue to run as best
as it can within its original dimensions, or you can tell it to re-create the Screen to the new
size if desired.

In a little more detail, you can read the Screen size (at the time of creation) from the
:py:obj:`~.Screen.dimensions` property.  If the user changes the size at any point, you can detect
this by calling the :py:meth:`.has_resized` method.  In addition, you can tell the Screen to throw
an exception if this happens while you are playing a Scene by specifying ``stop_on_resize=True``.

Once you have detetected that the screen size has changed using one of the options above, you can
either decide to carry on with the current Screen or throw it away and create a new one (by simply
creating a new Screen object). If you do the latter, you will typically need to recreate your
associated Scenes and Effects to run inside the new boundaries.  See the bars.py demo as a sample
of how to handle this.

Scraping Text
-------------
Sometimes it is useful to be able to read what is already displayed on the Screen at a given
location.  This is often referred to as screen scraping.  You can do this using the
:py:meth:`~.Screen.get_from` method.  It will return the displayed character and attributes (as a
4-tuple) for any single character location on the Screen.

.. code-block:: python

    # Check we've not already displayed something before updating.
    current_char, fg, attr, bg = screen.get_from(x, y)
    if current_char != 32:
        screen.print_at('X', x, y)

.. warning::

    Some languages use double-width glyphs.  When scraping text for such glyphs, you will find that
    ``get_from`` returns the character for both of the 2 locations containing the glyph.  For
    example, if you printed ``是`` at ``(0, 0)``, you would find that asciimatics returns this value
    for both ``(0, 0)`` and ``(0, 1)``.  For more details on which languages (and hence unicode
    characters) are affected by this see, `here
    <https://en.wikipedia.org/wiki/Halfwidth_and_fullwidth_forms>`__ and `here
    <http://denisbider.blogspot.co.uk/2015/09/when-monospace-fonts-arent-unicode.html>`__.

Drawing shapes
--------------
The Screen object also provides some anti-aliased line drawing facilities, using ASCII characters
to represent the line.  The :py:meth:`~.Screen.move` method will move the drawing cursor to the
specified coordinates and then the :py:meth:`~.Screen.draw` method will draw a straight line from
the current cursor location to the specified coordinates.

You can override the anti-aliasing with the ``char`` parameter.  This is most useful when trying to
clear what was already drawn.  For example:

.. code-block:: python

    # Draw a diagonal line from the top-left of the screen.
    screen.move(0, 0)
    screen.draw(10, 10)

    # Clear the line
    screen.move(0, 0)
    screen.draw(10, 10, char=' ')

If the resulting line is too thick, you can also pick a thinner pen by specifying ``thin=True``.
Examples of both styles can be found in the Clock sample code.

In addition, there is the :py:meth:`~.Screen.fill_polygon` method which will draw a filled
polygon in the specified colour using a set of points passed in to define the required shape.  This
uses the scan-line algorithm, so you can cut holes inside the shape by defining one polygon inside
another.  For example:

.. code-block:: python

    # Draw a large with a smaller rectangle hole in the middle.
    screen.fill_polygon([[(60, 0), (70, 0), (70, 10), (60, 10)],
                         [(63, 2), (67, 2), (67, 8), (63, 8)]])


Unicode drawing
---------------
The drawing methods covered above are unicode aware and will default to the correct character
set for your terminal, using unicode block characters where possible and falling back to pure
ASCII text if not.
