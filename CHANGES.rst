CHANGE HISTORY
==============

1.10.0
------
- Added 'Frame.focussed_widget' to access current focussed widget of the frame.
- Added `PopupMenu` for dynamic contextual menus.
- Added `DropdownList` widget.
- Added `VerticalDivider` widget.
- Added optional scroll bar to Listboxes.
- Added `line_wrap` option to TextBoxes.
- Added `line_char` option to Dividers.
- Added `align` option to Labels.
- Added `width` property to widgets.
- Added `set_theme` to Frames and provided some new colour schemes.
- Fixed `Screen.wrapper()` to return result from wrapped function.
- Fixed list box truncation when lines are too long.
- Fixed issue with background colour when scrolling GNOME terminal.
- Fixed Text validator to support instance methods.
- Fixed exception raised by getdefaultlocale on some curses systems.
- Performance tweaks for non-unicode widgets.
- Relaxed restriction on static function callbacks for pop-up dialogs.
- Fixed bug where `Listbox.reset()` overrode current selected value.
- Fixed handling of decomposed unicode file names in `FileBrowser` for MacOS
- Fixed CJK issues with `Screen.paint()` and `SpeechBubble`.
- Fixed issue with dynamically added Frames so that they are reset before displayed for the first time.

1.9.0
-----
- Added FileBrowser, DatePicker and TimePicker widgets.

  - Made `screen` a mandatory positional parameter to all Effects in the process.
  - NOTE: Any custom Effects you have created will now need to pass the screen down to the parent
    class.

- Added `fill_polygon()` to Screen and Canvas.
- Added the Kaleidoscope and RotatedDuplicate renderers.
- Created Maps demo - which renders vector tiles and satellite images from Mapbox.
- Added optional `is_modal` parameter to Frame constructor.
- Added `on_blur` and `on_focus` parameters to all interactive Widgets.
- Added `colour` property to Cogs Effect.
- Added `title` property to Frame.
- Added `text` property to Label.
- Added `hide_char` parameter to Text constructor to hide any entered text - e.g. for passwords.
- Added optional `height` parameter to Label constructor.
- Allowed programs to set "default" values for Widgets - which means you need to reset each field
  in a Frame explicitly rather than relying on reset to blank out uninitialized fields.
- Fixed up signal handling to re-instate old handlers on Screen.close().
- Fixed missing on_select handler for ListBox.

1.8.0
-----
- Added MultiColumnListBox for displaying tabular data in widgets.
- Improved efficiency of screen refresh on curses systems.
- Improved start-up time by avoiding use of deepcopy()
- Added unicode characters to ColourFileImage to increase rendering resolution.
- Added support for validated free-form text to Text widgets.
- Added force_update() to allow background refresh of the Screen.
- Added custom_colour property to widgets.
- Added support for DELETE key to text widgets.
- Fixed ZeroDivisionError in Frames.
- Fixed issues with double-width glyphs as used by CJK languages.
- Tweaked widget navigation using cursor keys to be more like web forms.

1.7.0
-----
- Added unicode support for input and output.
- Reworked Screen construction.

  - Added open() and close() methods to Screen.
  - Retired from_windows(), from_curses() and from_blessed() methods.
  - Retired Blessed support.

- Added set_scenes() and draw_next_frame() to allow asynchronous frameworks to
  use Screen.
- Added Plasma renderer and sample code to use it.
- Added background colour support to ColourImageFile.
- Added support for multi-colour rendering using ${c,a,b} syntax.
- Added highlight() method to Screen and Canvas.
- Added UT framework for testing and CI configurations to run the tests.
- Added shadows to Frames.
- Fixed bug in restoring console colours on Exit for Windows.
- Fixed up logic for handling Ctrl keys and documented OS restrictions.
- Fixed refresh timer in play() when handling intensive computational load.
- Added repeat flag to play() to allow termination of the animation instead of
  infinite looping.
- Improved CPU usage for Widgets-based UIs.
- General docs and test tidy up.

1.6.0
-----
- Added `widgets` sub-package, providing a Frame effect for encapsulating a User
  Interface, a Layout to organise the content and the following widgets:

  - Button
  - CheckBox
  - Divider
  - Label
  - ListBox
  - RadioButtons
  - Text
  - TextBox

- Added PopUpDialog for simple alerting in a UI.
- Added `attr` option to Print Effect.
- Added `keys` option to BarChart Renderer.

1.5.0
-----
- Created the ParticleEffect and associated classes.
- Implemented the StarFirework, RingFirework, SerpentFirework, PalmFirework,
  Explosion, DropScreen, ShootScreen and Rain effects.
- Added background colour options to BarChart renderer.
- Added set_title() method to set title for window that owns the Screen.

1.4.2
-----
- Fix for Python 3 support on Linux variants.

1.4.1
-----
- Minor fixes to setup.py to correct packaging meta-data.

1.4.0
-----
- Added Fire renderer and demo.
- Added Mouse support.  This had 2 major impacts:

  1. It meant that blessed support is now completely deprecated as it doesn't
     support mouse input.
  2. All references to processing keys is now deprecated.  You must now use the
     `get_event()` equivalent API instead.

- Added support for dynamic addition/removal of Effects from a Scene, using
  `add_effect()` and `remove_effect()`.
- Converted all effects to use `**kwargs` to pass through to base Effect class
  so that future common frame related features were instantly available.  These
  parameters must now always be specified as keyword arguments as a result.
- Added support for background colours.
- Renamed `getch()` and `putch()` to `get_from()` and `print_at()`.  Old
  functions are still present, but deprecated.
- Fixed up `get_from()` so that it is consistent across all platforms and
  includes all character attributes.

1.3.0
-----
- Added BarChart renderer and demo.
- Added support for extended key codes on Windows and Linux.
- Added support for dynamic paths using keyboard input.  Created interactive
  demo sample to show how this works.
- Split Renderer into StaticRenderer and DynamicRenderer.  Code that used
  Renderer should now use StaticRenderer.
- Added speed option to Print effect.
- Fixed up curses colour detection and Unicode bug in python2 on Windows.

1.2.0
-----
- Added Windows support, complete with `Screen.wrapper()` to handle all
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
  use curses, construct the Screen using the `from_curses()` class method.
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
