Troubleshooting
===============

256 colours
-----------
By default a lot of terminals will only support 8/16 colours.  Windows users
are limited to just these options for a native Windows console.  However other
systems can enable extra colours by picking a terminal that supports the
extended colour palettes.  For details of which terminals support additional
colours and how to enable them see [this Wikipedia article]
(https://en.wikipedia.org/wiki/Comparison_of_terminal_emulators).

In most cases, simply selecting a terminal type of `xterm-256color` will usually
do the trick these days.

Mouse support
-------------
Mouse support isn't fully enabled by default on all terminal types.  This will
often require some extra extensions to be enabled as described [here]
(http://stackoverflow.com/questions/29020638/which-term-to-use-to-have-both
-256-colors-and-mouse-move-events-in-python-curse).
