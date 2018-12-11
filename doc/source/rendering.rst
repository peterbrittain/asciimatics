Advanced Output
===============

Rendering
---------
When you want to create an animation, you typically need a sequence of multi-coloured text images to create
the desired effect.  This is where a :py:obj:`.Renderer` object comes into play.

A Renderer is simply an object that will return one or more text strings and associated colour maps in a
format that is suitable for display using the :py:meth:`~Screen.paint` method.  This collation of text string
and colour map is referred to as the rendered text.  It might vary in complexity from a single, monochrome
string through to many frames from an ASCII rendition of a colour video or animated GIF.

All renderers must implement the API of the abstract :py:obj:`.Renderer` class, however there are 2 basic
variants.

1. The :py:obj:`.StaticRenderer` creates pre-rendered sequences of rendered text.  They are usually
   initialized with some static content that can be calculated entirely in advance.  For example:

.. code-block:: python

    # Pre-render ASCIIMATICS using the big Figlet font
    renderer = FigletText("ASCIIMATICS", font='big')

2. The :py:obj:`.DynamicRenderer` creates the rendered text on demand.  They are typically dependent on the
   state of the program or the Screen when rendered.  For example:

.. code-block:: python

    # Render a bar chart with random bars formed of equals signs.
    def fn():
        return randint(0, 40)
    renderer = BarChart(10, 40, [fn, fn], char='=')

Once you have a Renderer you can extract the next text to de displayed by calling
:py:meth:`~asciimatics.renderers.Renderer.rendered_text`.  This will cycle round the static rendered text
sequentially or just create the new dynamic rendered text and return it (for use in the Screen paint method).
Generally speaking, rather than doing this directly with the Screen, you will typically want to use an Effect
to handle this.  See :ref:`animation-ref` for more details.

There are many built-in renderers provided by asciimatics.  The following section gives you a quick run
through of each one by area.  For more examples of Renderers, see the asciimatics samples folder.

Image to ASCII
~~~~~~~~~~~~~~
Asciimatics provides 2 ways to convert image files (e.g. JPEGs, GIFs, etc) into a text equivalent:

* :py:obj:`.ImageFile` - converts the image to grey-scale text.
* :py:obj:`.ColourImageFile` - converts the image to full colour text (using all the screen's palette).

Both support animated GIFs and will cycle through each image when drawn.

Animated objects
~~~~~~~~~~~~~~~~
Asciimatics provides the following renderers for more complex animation effects.

* :py:obj:`.BarChart` - draws a horizontal bar chart for a set of data (that may be dynamic in nature).
* :py:obj:`.Fire` - simulates a burning fire.
* :py:obj:`.Plasma` - simulates an animated "plasma" (think lava lamp in 2-D).
* :py:obj:`.Kaleidoscope` - simulates a 2 mirror kaleidoscope.

Text/colour manipulation
~~~~~~~~~~~~~~~~~~~~~~~~
The following renderers provide some simple text and colour manipulation.

* :py:obj:`.FigletText` - draws large FIGlet text
* :py:obj:`.Rainbow` - recolours the specified Renderer in as a Rainbow
* :py:obj:`.RotatedDuplicate` - creates a rotated duplicate of the specified Renderer.

Boxes
~~~~~
The following renderers provide some simple boxes and boxed text.

* :py:obj:`.Box` - draws a simple box.
* :py:obj:`.SpeechBubble` - draws a speech bubble around some specified text.

Static colour codes
-------------------
When creating static rendered output, it can be helpful to define your colours inline with the rest of your
text.  The :py:obj:`.StaticRenderer` class supports this through the ${n1,n2,n3} escape sequence, where `n*`
are digits.

Formally this sequence is defined an escape sequence ${c,a,b} which changes the current colour tuple to be
foreground colour 'c', attribute 'a' and background colour 'b' (using the values of the Screen COLOUR and ATTR
constants).  The attribute and background fields are optional.

These tuples create a colour map (for input into :py:meth:`~Screen.paint`) and so the colours will reset to
the defaults passed into `paint()` at the start of each line.  For example, this code will produce a simple
Xmas tree with coloured baubles when rendered (using green as the default colour).

.. code-block:: python

    StaticRenderer(images=[r"""
           ${3,1}*
          / \
         /${1}o${2}  \
        /_   _\
         /   \${4}b
        /     \
       /   ${1}o${2}   \
      /__     __\
      ${1}d${2} / ${4}o${2}   \
       /       \
      / ${4}o     ${1}o${2}.\
     /___________\
          ${3}|||
          ${3}|||
    """])

Experimental
------------
A Renderer can also return a plain text string representation of the next rendered text image.  This means
they can be used outside of a Screen.  For example:

.. code-block:: python

    # Print a bar chart with random bars formed of equals signs.
    def fn():
        return randint(0, 40)
    renderer = BarChart(10, 40, [fn, fn], char='=')
    print(renderer)
