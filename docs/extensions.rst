Extensions
----------

Code Annotations uses `Stevedore`_ to allow new lanuages to be statically searched in an easily extensible fashion. All
language searches, even the ones that come by default, are implemented as extensions. A language extension is
responsible for finding all comments in files of the given type. Note that extensions are only used in the Static Search
and not in Django search, as Django models are obviously all written in Python.

.. _Stevedore: https://docs.openstack.org/stevedore/latest/

Many languages can have their comments found by relatively simple regular expressions. In those cases they can simply
inherit from ``SimpleRegexAnnotationExtension`` and override the ``extension_name`` and ``lang_comment_definition`` to
be fully functional. This is how the Javascript and Python extensions work, see those for examples.

If a language has more than one single-line or multi-line comment type you may need to work at the lower level and
inherit from ``AnnotationExtension``. ``SimpleRegexAnnotationExtension`` inherits from ``AnnotationExtension`` and
serves as an example.

When inheriting from ``AnnotationExtension`` you must override:

``extension_name`` - A unique name for your extension, usually the name of the language it supports. This must match the
    name given in ``setup.py`` or ``setup.cfg`` (see below).

``search`` - Called to search for all annotations in a given file. Takes an open file handle, returns a list of dicts.
    Extensions do not need to worry about linting groups or choices, just returning all found annotations in the order
    they were discovered in the file.

    The dicts returned are in the format of:

.. code-block:: python

    {
        'found_by': "name of your extension",
        'filename': name of the file passed in (available from file_handle.name),
        'line_number': line number of the beginning of the comment,
        'annotation_token': the annotation token,
        'annotation_data': the rest of the text after the annotation token (choices do not need to be split out here),
        'extra': a dict containing any additional information your extension would like to include in the report
    }

In order to test your extension you will need to install it into your Python environment or virtualenv. First you must
define it as an entry point in your setup.py (or setup.cfg). The entry point name for Code Annotations extensions is
"annotation_finder.searchers". An example for our own extensions is:

.. code-block:: python

    'annotation_finder.searchers': [
        'javascript = code_annotations.extensions.javascript:JavascriptAnnotationExtension',
        'python = code_annotations.extensions.python:PythonAnnotationExtension',
    ],


Then you can simply ``pip install -e .`` from your project directory. If all goes well you should see your extension
being loaded when you run the static annotation tool with the `-vv` or `-vvv` option. For your extension to work you
will also need to add it to the ``extensions`` section of your configuration file.
