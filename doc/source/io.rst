Basic Input\\Output
==================

Creating a Screen
------------------
The starting point for any asciimatics program is the :py:obj:`.Screen` object.  It can most easily be obtained from the :py:methods:`wrapper` static method.  This will handle all the necessary initialization for your environment and pass the constructed Screen into the specified function.  For example:

.. code-block:: python

    def demo(screen):
        screen.putch('Hello world!', 0, 0)
        sleep(10)

    Screen.wrapper(demo)

If you need more control than this allows, you can fall back to the lower level methods like :py:meth:`from_curses`.  This is deprecated though.

Output
------
Once you have a Screen, the simplest way to output text is using the :py:meth:`putch` method.  This allows you to place a string at a desired location in a specified colour.  The coordinates are zero-indexed starting at the top left of the screen and move down and right, so the example above displays `Hello world!` at (0, 0) which is the top left of the screen.

Common colours are defined by the `COLOUR_xxx` constants in the Screen class.  If you have a display capable of handling more than these (e.g. 256 colour xterm) you can use the indexes of that display directly. 

Attributes are defined by the `A_xxx` constants in the Screen class.  Most systems will support bold (a.k.a bright), normal and reverse attributes.  Others are capable of more, but you will have difficulties using them in a cross-platform manner and so they are deprecated.

.. code-block:: python

    # Bright green text
    screen.putch('Hello world!', 0, 0, COLOUR_GREEN, A_BOLD)

If you want to do something more complex, you can use the :py:`paint` method to specify a colour map for each character to be displayed.  This must be an list of paired colour\attribute values (tuples or lists) that is at least as long as the text to be displayed.  This method is typically used for displaying complex, multi-coloured text from a Renderer.

Refreshing the Screen
---------------------
The Screen maintains a buffer of what is to be displayed and will only actually display it once the :py:meth:`refresh` method is called.  This is done to reduce flicker on the display device as new content is created.  The expectation is that applications re-render everything that needs to be displayed and then call refresh at the end.  When using the :py:meth:`play` method to do animations, this is done automatically at the end of each frame.

Input
-----
To handle user input, use the :py:meth:`get_key` method.  This instantly returns the latest key-press, including auto repeat for keys held down, without waiting for a new line and without echoing it to screen.  The returned key is the ordinal representation of the key (taking into account keyboard state - e.g. caps lock) if possible, or an extended key code (the `KEY_xxx` constants in the Screen class) where not.  If there is no key-press available, this will return `None`.

For example, if you press 'a' normally `get_key` will return 97, which is `ord('a')`.  If you press the same key with caps lock on, you will get 65, which is `ord('A')`.  If you press 'F7' you will get `KEY_F7` instead.

Screen Resizing
---------------
It is not possible to change the Screen size programmatically.  However, the user may resize their terminal or console while your program is running.

You can read the current  size from the :py:obj:`.dimensions` property on the Screen.  Rather than poll this property, you can check if your Screen has resized by calling the :py:meth:`.has_resized` method.  This will tell you if the dimensions have been changed by the user since it was last called.  

In addition, you can tell the Screen to throw an exception if this happens while you are playing a Scene by specifying stop_on_resize=True.

Scraping Text
-------------
Sometimes it is useful to be able to read what is already displayed on the Screen at a given location.  This is often referred to as screen scraping.  You can do this using the :py:meth:`.getch` method.  It will return the displayed character and attributes for any single character location on the Screen.

.. code-block:: python

    # Check we've not already displayed something before updating.
    current_char, attributes = screen.getch(x, y)
    if current_char != 32:
        screen.putch('X', x, y)

Line drawing
------------
The Screen object also provides some anti-aliased line drawing facilities, using ASCII characters to represent the line.  The :py:meth:`move` method will move the drawing cursor to the specified coordinates and then the :py:meth:`draw` method will draw a straight line from the current cursor location to the specified coordinates.

You can override the anti-aliasing with the `char` parameter.  This is most useful when trying to clear what was already drawn.  For example:

.. code-block:: python

    # draw a diagonal line from the top-left of the screen.
    screen.move(0, 0)
    screen.draw(10, 10)

    # Clear the line
    screen.move(0, 0)
    screen.draw(10, 10, char=' ')

If the resulting line is too thick, you can also pick a thinner pen by specifying `thin=True`.  Examples of both styles can be found in the Clock sample code.
