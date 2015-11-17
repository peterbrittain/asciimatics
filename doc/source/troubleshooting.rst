Troubleshooting
===============

256 colours
-----------
By default a lot of terminals will only support 8/16 colours.  Windows users
are limited to just these options for a native Windows console.  However other
systems can enable extra colours by picking a terminal that supports the
extended colour palettes.  For details of which terminals support additional
colours and how to enable them see `this Wikipedia article
<https://en.wikipedia.org/wiki/Comparison_of_terminal_emulators>`_.

In most cases, simply selecting a terminal type of `xterm-256color` will usually
do the trick these days.

Mouse support
-------------
Mouse support isn't fully enabled by default on all terminal types.  This will
often require some extra extensions to be enabled as described `here
<http://unix.stackexchange.com/questions/35021/how-to-configure-the-terminal
-so-that-a-mouse-click-will-move-the-cursor-to-the>`_.  In addition, if you
want 256 colours, you will need to mix modes as described `here
<http://stackoverflow.com/questions/29020638/which-term-to-use-to-have-both
-256-colors-and-mouse-move-events-in-python-curse>`_.

Although it is possible to get Linux terminals to report all mouse movement,
the reporting of mouse buttons along with movement appears to be highly
erratic.  The best reporting appears to be using the button event mode - i.e.
mixing `xterm-1002` with `xterm-256color`.

Windows title
-------------
Much like mouse support, the commands to set the window title is not supported
on all terminal types.  Windows should work without any changes.  Other systems
may need to use a similar method as above to mix modes to add status line
support as described `here <https://gist.github.com/KevinGoodsell/744284>`_.