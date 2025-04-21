Contributing
============

Getting started
---------------

So you want to join in?  Great!  There's a few ground rules...

#. Before you do anything else, read up on the design.

   * You should find all general background in these 4 classes: :py:obj:`.Screen`,
     :py:obj:`.Scene`, :py:obj:`.Effect` and :py:obj:`~renderers.Renderer`.
   * You will find more details on TUIs in these 3 classes: :py:obj:`.Frame`, :py:obj:`.Layout`
     and :py:obj:`.Widget`.

#. If writing a new Effect, consider why it can't be handled by a combination of a new
   Renderer and the :py:obj:`.Print` Effect.  For example, dynamic Effects such as
   :py:obj:`.Snow` depend on the current Screen state to render each new image.
#. Go the extra yard.  This project started on a whim to share the joy of someone starting out
   programming back in the 1980s.  How do you sustain that joy?  Not just by writing code that
   works, but by writing code that other programmers will admire.
#. Make sure that your code is `PEP-8 <https://www.python.org/dev/peps/pep-0008/>`_ compliant.
   Tools such as flake8 and pylint or editors like pycharm really help here.
#. Please run the existing unit tests against your new code to make sure that it still works
   as expected.  I normally use nosetests to do this.  In addition, if you are adding significant
   extra function, please write some new tests for your code.

If you're not quite sure about something, feel free to join us at
https://gitter.im/asciimatics/Lobby and share your ideas.

When you've got something you're happy with, please feel free to submit a pull request at
https://github.com/peterbrittain/asciimatics/issues.

Building The Documentation
--------------------------

Install the dependencies and build the documentation with:

.. code-block:: bash

    $ pip install -r requirements/dev.txt
    $ cd doc
    $ ./build.sh

You can then view your new shiny documentation in the ``build`` folder.

Running The Tests
------------------

Install the dependencies and run the tests with the following:

.. code-block:: bash

    $ pip install -r requirements/dev.txt
    $ python -m unittest

On most systems this will avoid running tests that require a Linux TTY.  If you are making changes to the
Screen, you must also run the TTY tests.  You can force that on a Linux box using the following:

.. code-block:: bash

    $ FORCE_TTY=Y python -m unittest

The reason for this split is that you only typically get a TTY on a live interactive connection to your
terminal.  This means you should always be able to run the full suite manually.  However, many CI systems
do not provide a valid TTY and so these tests regularly fail on various build servers.  Fortunately, Travis
provides a working TTY and so we enable the full suite of tests on any check-in to master.
