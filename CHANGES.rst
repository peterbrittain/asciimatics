CHANGE HISTORY
==============

1.0.0
-----
- Added Bressenham line drawing algorithm with anti-aliasing.
- Added Random Noise effect.
- Added support for blessed as well as curses - if you want to continue to
  use curses, construct the Screen using the from_curses() class method.
- Fixed up some docs errors.

0.4.0
-----
- Added support for 256 colour terminals.
- Moved ${c,a} syntax for inline colouring from Screen to Renderers
- Created some samples for 256 colour mode and colour images.

0.3.0
-----
- Added support for multi-colour rendering using ${c,a} syntax.
- Added Snow effect.
- Fixed bug when erasing small Sprites.
- Fixed up various documentation niggles.

0.2.0
-----
- Original public release.
