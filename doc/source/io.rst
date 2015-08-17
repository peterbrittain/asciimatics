Basic Input\Output
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

If you want to do something more complex, you can use the :py:`paint` method to specify a colour map for each character to be displayed.  This must be an list of paired colour\attribute values (tuples or lists) that is at least as long as the text to be displayed.

Input
-----
To handle user input, use the :py:meth:`get_key` method.  This instantly returns the latest key-press, including auto repeat for keys held down, without waiting for a new line and without echoing it to screen.  The returned key is the ordinal representation of the key (taking into account keyboard state - e.g. caps lock) if possible, or an extended key code (the `KEY_xxx` constants in the Screen class) where not.  If there is no key-press available, this will return `None`.

For example, if you press 'a' normally `get_key` will return 97, which is `ord('a')`.  If you press the same key with caps lock on, you will get 65, which is `ord('A')`.  If you press 'F7' you will get `KEY_F7` instead.
