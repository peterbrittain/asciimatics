CHANGE HISTORY
==============

1.3.0
-----
- Added BarChart rendered and demo.
- Split Renderer into StaticRenderer and DynamicRenderer.  Code that used
  Renderer should now use StaticRenderer.
- Added speed option to Print effect.
- Fixed up curses colour detection and .

1.2.0
-----
- Added Windows support, complete with Screen.wrapper() to handle all
  required screen set up.  The old from_XXX class methods are now deprecated.
- Fixed ColourImageFile to do bare minimum rendering on low colour terminals.
- Added formal palette property to Screen for image conversions.
- Verified Python 3.4 support.

1.1.0
-----
- Added the Julia Set and Cog effects.
- Fixed up off-by-one error in line drawing.
- Added support for screen resizing while playing a scene.
- Added support for Python 3.

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
- Moved ${c,a} syntax for inline colouring from Screen to Renderer.
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
