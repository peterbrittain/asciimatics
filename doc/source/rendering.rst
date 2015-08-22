Advanced Output
===============

Rendering
---------
When you want to create an animation, you typically need a sequence of multi-coloured text images to create the desired effect.  This is where a :py:obj:`.Renderer` object comes into play.

A Renderer is simply an object that will return one or more text strings in a format that is suitable for display using the :py:meth:`.paint` method.  These strings might vary from a single string that does not change through to many frames from an ASCII rendition of a video.

All renderer a must implement the API of the abstract Renderer class, however there are 2 basic variants.

1. The :py:obj:`.StaticRenderer` creates pre-rendered sequences of one or more rendered strings.  They are usually initialized with some static content - e.g. The name of an image file to convert to ASCII, or a text string to be displayed.  For example:

.. code-block:: python

    # Pre-render ASCIIMATICS using the big Figlet font
    renderer = FigletText("ASCIIMATICS", font='big')

2. The :py:obj:`.DynamicRenderer` creates every single rendered string on demand.  They are typically dependent on the state of the machine when rendered.  For example:

.. code-block:: python

    # Render a bar chart with random bars formed of equals signs.
    def fn():
        return randint(0, 40)
    renderer = BarChart(10, 40, [fn, fn], char='=')

Once you have a renderer you can extract the next image to de displayed by calling :py:meth:`.rendered_text`.  This will cycle round the images generated and return a tuple that you can pass to the Screen paint method.  Generally speaking, rather than doing this directly, you will typically want to use an Effect to handle this.

For more examples of each, see the asciimatics samples folder.

Experimental
------------
A Renderer can also return a plain text string representation of the next rendered text image.  This means they can be used outside of a Screen.  For example:

.. code-block:: python

    # Print a bar chart with random bars formed of equals signs.
    def fn():
        return randint(0, 40)
    renderer = BarChart(10, 40, [fn, fn], char='=')
    print(renderer)
