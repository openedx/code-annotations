Getting Started
===============

If you have not already done so, create or activate a `virtualenv`_. Unless otherwise stated, assume all terminal code
below is executed within the virtualenv.

.. _virtualenv: https://virtualenvwrapper.readthedocs.org/en/latest/


Install the tool
----------------
.. code-block:: bash

    $ make requirements
    $ pip install -e .


Run the tests
-------------
Make sure everything is working okay:

.. code-block:: bash

    $ make test

or

.. code-block:: bash

    $ tox

or

.. code-block:: bash

    $ tox -e py27


Create a configuration file
---------------------------
Configuration for code-annotations is done via a yaml file, The default filename of which is ``.annotations``. The
following is an example of a minimal configuration file. See ``.annotations_sample`` for a more thorough example and
:doc:`configuration` for more details. In this example the Code Annotations tools will search for the string
``.. annotation_token::`` in the comments of Python and Javascript files using the built-in extensions.

.. code-block:: yaml

    # Path that you wish to static search, can be passed on the command line
    # Directories will be searched recursively, but this can also point to a single file
    source_path: ./

    # Directory to write the report to, can be passed on the command line
    report_path: reports

    # Path to the Django annotation safelist file
    safelist_path: .annotation_safe_list.yml

    # Percentage of Django models which must have annotations in order to pass coverage checking
    coverage_target: 50.0

    # Definitions of the annotations to search for. Notice the trailing colon, this is a mapping type!
    # For more information see "Writing Annotations"
    annotations:
        ".. annotation_token::":

    # Code Annotations extensions to load and the file extensions to map them to
    extensions:
        python:
            - py


Create some annotations
-----------------------
In your ``source_path`` add some comments with annotations in them. Examples:

**Python**

.. code-block:: python

    """
    .. annotation_token:: This comment text will be captured along with the token in our search.
    """

    # .. annotation_token:: This comment will also be captured.

**Javascript**

.. code-block:: javascript

    /*
    .. annotation_token:: So will this.
    */

    // .. annotation_token:: And this!


Run a static annotation search
------------------------------

.. code-block:: bash

    $ code_annotations --config_file /path/to/your/config

If all went well you should see a message telling you the name of the report file that was written out. Take a look in
your favorite text editor to make sure all of your annotations were found. Different verbosity levels are available for
this command, try ``-v``, ``-vv``, and ``-vvv`` to assist in debugging. ``--help`` will provide information on all of
the available options.

By default the static annotation search will perform linting, which makes sure that any found annotations match the
structure listed in configuration. If any issues are found the command will fail with no report written, otherwise a
YAML file containing the results of the search will be written to your ``report_path``. Both linting and reporting
features can be turned off via command line flags.

Add more structure to your annotations
--------------------------------------
Annotations can be more than simple messages. They can enforce the use of choices from a fixed list, and can be grouped
to provide more context-aware information. See :doc:`configuration` and :doc:`writing_annotations` for more information
on how to use those options.
