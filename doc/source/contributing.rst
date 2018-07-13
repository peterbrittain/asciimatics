Contributing
============

Building The Documentation
--------------------------

Install the dependencies and build the documentation with:

.. code-block:: bash

    $ pip install -r requirements/dev.txt
    $ cd doc && cp source/conf_orig.py source/conf.py
    $ ./build.sh

You can then view your new shiny documentation in the ``build`` folder.

Running The Tests
------------------

Install the dependencies and run the tests with the following:

.. code-block:: bash

    $ pip install -r requirements/dev.txt
    $ nosetests
