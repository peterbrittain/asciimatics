Advanced Output
===============

Rendering
---------
When you want to create an animation, you typically need a sequence of
multi-coloured text images to create the desired effect.  This is where a
:py:obj:`.Renderer` object comes into play.

A Renderer is simply an object that will return one or more text strings and
associated colour maps in a format that is suitable for display using the
:py:meth:`.paint` method.  This collation of text string and colour map is
referred to as the rendered text.  It might vary in complexity from a single,
monochrome string through to many frames from an ASCII rendition
of a colour video or animated GIF.

All renderers must implement the API of the abstract :py:obj:`.Renderer` class,
however there are 2 basic variants.

1. The :py:obj:`.StaticRenderer` creates pre-rendered sequences of rendered
   text.  They are usually initialized with some static content that can be
   calculated entirely in advance.  For example:

.. code-block:: python

    # Pre-render ASCIIMATICS using the big Figlet font
    renderer = FigletText("ASCIIMATICS", font='big')

2. The :py:obj:`.DynamicRenderer` creates the rendered text on demand.  They
   are typically dependent on the state of the program or the Screen when
   rendered.  For example:

.. code-block:: python

    # Render a bar chart with random bars formed of equals signs.
    def fn():
        return randint(0, 40)
    renderer = BarChart(10, 40, [fn, fn], char='=')

Once you have a Renderer you can extract the next text to de displayed by
calling :py:meth:`~asciimatics.renderers.Renderer.rendered_text`.  This will
cycle round the static rendered text sequentially or just create the new
dynamic rendered text and return it (for use in the Screen paint method).
Generally speaking, rather than doing this directly with the Screen, you will
typically want to use an Effect to handle this.  See :ref:`animation-ref` for
more details.

For more examples of Renderers, see the asciimatics samples folder.

Experimental
------------
A Renderer can also return a plain text string representation of the next
rendered text image.  This means they can be used outside of a Screen.  For
example:

.. code-block:: python

    # Print a bar chart with random bars formed of equals signs.
    def fn():
        return randint(0, 40)
    renderer = BarChart(10, 40, [fn, fn], char='=')
    print(renderer)
