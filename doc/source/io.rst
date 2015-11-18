Basic Input/Output
==================

Creating a Screen
-----------------
The starting point for any asciimatics program is the :py:obj:`.Screen` object.
It can most easily be obtained from the :py:meth:`.wrapper` static method.  This
will handle all the necessary initialization for your environment and pass the
constructed Screen into the specified function.  For example:

.. code-block:: python

    def demo(screen):
        screen.print_at('Hello world!', 0, 0)
        screen.refresh()
        sleep(10)

    Screen.wrapper(demo)

If you need more control than this allows, you can fall back to the lower level,
environment-specific methods like :py:meth:`.from_curses`.  This access is
deprecated though and may be removed in future releases.

Output
------
Once you have a Screen, the simplest way to output text is using the
:py:meth:`.print_at` method.  This allows you to place a string at a desired
location in a specified colour.  The coordinates are zero-indexed starting at
the top left of the screen and move down and right, so the example above
displays `Hello world!` at (0, 0) which is the top left of the screen.

Colours
^^^^^^^
Common colours are defined by the `COLOUR_xxx` constants in the Screen class.
The full list is as follows:

.. code-block:: python

    COLOUR_BLACK = 0
    COLOUR_RED = 1
    COLOUR_GREEN = 2
    COLOUR_YELLOW = 3
    COLOUR_BLUE = 4
    COLOUR_MAGENTA = 5
    COLOUR_CYAN = 6
    COLOUR_WHITE = 7

If you have a display capable of handling more than these (e.g. 256 colour
xterm) you can use the indexes of the colours for that display
directly instead.  When creating effects that use these extra colours, it is
recommended that you also support a reduced colour mode, using just the
8 common colours.  For an example of how to do this, see the :py:obj:`.Rainbow`
class.

Attributes
^^^^^^^^^^
Attributes are a way of modifying the displayed text in some basic ways that
early hardware terminals supported before they had colours.  Most
systems don't use hardware terminals any more, but the concept persists in
all native console APIs and so is also used here.

Supported attributes are defined by the `A_xxx` constants in the Screen class.
The full list is as follows:

.. code-block:: python

    A_BOLD = 1
    A_NORMAL = 2
    A_REVERSE = 3
    A_UNDERLINE = 4

Most systems will support bold (a.k.a bright), normal and reverse attributes.
Others are capable of more, but you will have difficulties using them in a
cross-platform manner and so they are deprecated. The attribute is just
another parameter to `print_at`.  For example:

.. code-block:: python

    # Bright green text
    screen.print_at('Hello world!', 0, 0, COLOUR_GREEN, A_BOLD)

Multicoloured strings
^^^^^^^^^^^^^^^^^^^^^
If you want to do something more complex, you can use the :py:meth:`.paint`
method to specify a colour map for each character to be displayed.  This must
be a list of colour/attribute values (tuples or lists) that is at least
as long as the text to be displayed.  This method is typically used for
displaying complex, multi-coloured text from a Renderer.  See
:ref:`animation-ref` for more details.

Refreshing the Screen
---------------------
Just using the above methods to output to screen isn't quite enough.
The Screen maintains a buffer of what is to be displayed and will only actually
display it once the :py:meth:`.refresh` method is called.  This is done to
reduce flicker on the display device as new content is created.  

Applications are required to re-render everything that needs to be
displayed and then call refresh when all the new content is ready.  
Note that the :py:meth:`.play` method will do this for you automatically
at the end of each frame, so you don't need to call it again inside your
animations.

Input
-----
To handle user input, use the :py:meth:`.get_event` method.  This instantly
returns the latest key-press or mouse event, without waiting for a new line and
without echoing it to screen (for keyboard events).  If there is no event
available, it will return `None`.

The exact class returned depends on the event.  It will be either
:py:obj:`.KeyboardEvent` or :py:obj:`.MouseEvent`.  Handling of each is covered
below.

KeyboardEvent
^^^^^^^^^^^^^
This event is triggered for any key-press, including auto repeat when keys are
held down.  ``key_code`` is the ordinal representation of the key (taking
into account keyboard state - e.g. caps lock) if possible,
or an extended key code (the ``KEY_xxx`` constants in the Screen class) where
not.

For example, if you press 'a' normally ``get_key`` will return 97, which is
``ord('a')``.  If you press the same key with caps lock on, you will get 65,
which is ``ord('A')``.  If you press 'F7' you will always get ``KEY_F7``
irrespective of the caps lock.

MouseEvent
^^^^^^^^^^
This event is triggered for any mouse movement or button click.  The current
coordinates of the mouse on the Screen are stored in the ``x`` and ``y``
properties.  If a button was clicked, this is tracked by the ``buttons``
property.  Allowed values for the buttons are ``LEFT_CLICK``, ``RIGHT_CLICK``
and ``DOUBLE_CLICK``.

.. warning::

    In general, Windows will report all of these straight out of the box.
    Linux will only report mouse events if you are using a terminal that
    supports mouse events (e.g. xterm) in the terminfo database.  Even then,
    not all terminals report all events.  For example, the standard xterm
    function is just to report button clicks.  If you need your application
    to handle mouse move events too, you will need to use a terminal that
    supports the additional extensions - e.g. the xterm-1003 terminal type.
    See :ref:`mouse-issues-ref` for more details on how to fix this.

Screen Resizing
---------------
It is not possible to change the Screen size through your program.  However, the
user may resize their terminal or console while your program is running.

You can read the current  size from the :py:obj:`.dimensions` property of the
Screen.  Rather than poll this property for changes, you can check if your
Screen has resized by calling the :py:meth:`.has_resized` method.  This will
tell you if the dimensions have been changed by the user at any time since it
was last called.

In addition, you can tell the Screen to throw an exception if this happens
while you are playing a Scene by specifying ``stop_on_resize=True``.  This
should then allow your program to redefine the Scenes as needed and then pass
the new Scenes to the Screen to play them instead.

Scraping Text
-------------
Sometimes it is useful to be able to read what is already displayed on the
Screen at a given location.  This is often referred to as screen scraping.  You
can do this using the :py:meth:`.get_from` method.  It will return the displayed
character and attributes (as a 4-tuple) for any single character location on
the Screen.

.. code-block:: python

    # Check we've not already displayed something before updating.
    current_char, fg, attr, bg = screen.get_from(x, y)
    if current_char != 32:
        screen.print_at('X', x, y)

Line drawing
------------
The Screen object also provides some anti-aliased line drawing facilities,
using ASCII characters to represent the line.  The :py:meth:`.move` method will
move the drawing cursor to the specified coordinates and then the
:py:meth:`.draw` method will draw a straight line from the current cursor
location to the specified coordinates.

You can override the anti-aliasing with the ``char`` parameter.  This is most
useful when trying to clear what was already drawn.  For example:

.. code-block:: python

    # draw a diagonal line from the top-left of the screen.
    screen.move(0, 0)
    screen.draw(10, 10)

    # Clear the line
    screen.move(0, 0)
    screen.draw(10, 10, char=' ')

If the resulting line is too thick, you can also pick a thinner pen by
specifying ``thin=True``.  Examples of both styles can be found in the Clock
sample code.
