Troubleshooting
===============

256 colours not working
-----------------------
By default a lot of terminals will only support 8/16 colours.  Windows users
are limited to just these options for a native Windows console.  However other
systems can enable extra colours by picking a terminal that supports the
extended colour palettes.  For details of which terminals support additional
colours and how to enable them see `this Wikipedia article
<https://en.wikipedia.org/wiki/Comparison_of_terminal_emulators>`_.

In most cases, simply selecting a terminal type of ``xterm-256color`` will
usually do the trick these days.

.. _mouse-issues-ref:

Mouse support not working
-------------------------
Curses systems
^^^^^^^^^^^^^^
Mouse support isn't fully enabled by default on all terminal types.  This will
often require some extra extensions to be enabled as described `here
<http://unix.stackexchange.com/questions/35021/how-to-configure-the-terminal
-so-that-a-mouse-click-will-move-the-cursor-to-the>`__.  In addition, if you
want 256 colours, you will need to mix modes as described `here
<http://stackoverflow.com/questions/29020638/which-term-to-use-to-have-both
-256-colors-and-mouse-move-events-in-python-curse>`__.

Although it is possible to get Linux terminals to report all mouse movement,
the reporting of mouse buttons along with movement appears to be highly
erratic.  The best reporting appears to be using the button event mode - i.e.
mixing ``xterm-1002`` with ``xterm-256color``.

Windows
^^^^^^^
Asciimatics will reprogram the Windows console to report mouse events on
start-up.  However, it is possible to change this while the application is
running.  In particular, if you switch on QuickEdit mode, Windows will stop
reporting mouse events and process them itself.  It is not possible to have
both, so if you want to use the mouse in yor app, please switch off QuickEdit
mode.

Windows title does not change
-----------------------------
Much like mouse support, the commands to set the window title is not supported
on all terminal types.  Windows should work without any changes.  Other systems
may need to use a similar method as above to mix modes to add status line
support as described `here <https://gist.github.com/KevinGoodsell/744284>`_.

.. _ctrl-s-issues-ref:

Ctrl+S does not work
--------------------
In order to maintain legacy support for real terminal systems, most
terminals/consoles still support software flow control using Ctrl+S/Ctrl+Q.
You can switch this off on Linux by typing ``stty -ixon`` in your shell before
you start asciimatics as explained `here <http://unix.stackexchange.com/
questions/12107/how-to-unfreeze-after-accidentally-pressing-ctrl-s-in-a-
terminal>`__. Sadly, there is nothing that can be done on Windows to
prevent this as it is built in to the operating system, so you will never be
able to detect the Ctrl+S key.  See `here
<http://stackoverflow.com/questions/26436581/is-it-possible-to-disable-system-
console-xoff-xon-flow-control-processing-in-my>`__ for details.

I can't run it inside PyCharm or other IDEs
-------------------------------------------
Depending on which version you're using, you may see pywintypes.error 6
(ERROR_INVALID_HANDLE), or simply nothing (i.e. it looks like the program
has hung).  The reason for this is that the IDE Terminal/Console is not
a true native terminal/console and so the native interfaces used by
asciimatics will not work.  There are 2 workarounds.

1. The simplest is just to run asciimatics inside a real terminal
   or window - i.e. not inside PyCharm/the IDE.

2. If you must run inside PyCharm, the only option I've got working
   so far is the tests but even some of them need to skip where they
   cannot actually run.  To run from the IDE, you must start a real
   console from the Terminal window e.g. using `start cmd /c "python
   <your file name>"`.

.. _unicode-issues-ref:

Unicode characters are not working
----------------------------------
Curses systems
^^^^^^^^^^^^^^
Most modern versions of Linux/OSX come with a good selection of glyphs supported
as standard.  The most likely issue is that you are not using a UTF-8 locale.

To set this up, follow the instructions `here
<http://stackoverflow.com/q/7165108/4994021>`__ for OSX or `here
<http://serverfault.com/q/275403>`__ for Linux.

If that doesn't solve the problem and you are seeing unexpected lines in your
block drawing characters, you are using a Terminal with extra spacing between
your lines.

OSX allows you to edit the spacing as explained `here <http://superuser.com/
questions/350821/how-can-i-change-the-line-height-in-terminal-osx>`__, but 
Linux users will probably need to install a different terminal as explained 
`here <http://askubuntu.com/questions/194264/
how-do-i-change-the-line-spacing-in-terminal>`__.  I have found that 
`rxvt-unicode-256color` is most likely to work.

Windows
^^^^^^^
On Windows systems, there are a couple of potential issues.  The first is that
you might be using the wrong code page.  Windows comes with `many
<https://msdn.microsoft.com/en-us/library/windows/desktop/
dd317756(v=vs.85).asp>`__ code pages.  By default, asciimatics will only enable
unicode features if you are using code page 65001 (the UTF-8 code page).  You
can fix this issue by running::

    chcp 65001

If this does not solve the issue, the next possibility is that you may be using
the Lucida Console or Consolas fonts.  These do not have a full enough range
of glyphs to support all the unicode output that asciimatics can generate.

To fix this issue, you need to download a font with a wider range of glyphs
and then install them as the default for your command prompt.  Details of how
to do that are available `here <http://www.techrepublic.com/blog/
windows-and-office/quick-tip-add-fonts-to-the-command-prompt/>`__.  I recommend
that you use the `DejaVu Mono font <http://dejavu-fonts.org/wiki/Main_Page>`__,
which you can extract from the ZIP file from the `download page
<http://dejavu-fonts.org/wiki/Download>`__ - it is DejaVuSansMono.ttf in the TTF
folder of the ZIP.
