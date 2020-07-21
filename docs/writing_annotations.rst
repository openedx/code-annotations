Writing Annotations
-------------------

Annotations are structured comments that can be used to mark sections of code with distinct meaning, such as TODO's,
deprecation notices, or places where sensitive information is being handled. Code Annotations breaks down these special
comments into two parts- the annotation token, and the annotation data.

- Annotation token
    The annotation token is a unique string that can be easily found and separated from other comment content. The
    convention used in our examples is ``.. <descriptor>:`` where <descriptor> is a slug that says the kind of
    annotation it is. The ``..`` and ``:`` are entirely optional, but do help keep the strings unique and prevent false
    positives.

- Annotation data
    Annotation data can either be a simple free text comment that is on the same line as the token, or a choice list.
    The choices in a choice list are configured in the configuration file and can be separated by spaces or commas when
    used in comments. As such, the choices themselves should not contain spaces or commas.

The information below applies to both the Static Search and Django Model Search tools, with the exception that the
Django Model Search only looks in model docstrings.

**Examples**

Configuration for a "fun fact" annotation type, denoted by the annotation token ``.. fun_fact:``:

.. code-block:: yaml

    annotations:
        ".. fun_fact:":

There are no choices given, so this is a free form comment type of annotation. Note the trailing colon! It would be used
in Python like this:

.. code-block:: python

    """
    This function handles setting the price on an item in the database.

    .. fun_fact: This code is the only remaining piece of our first commit!
    """

When a report is run against this code an entry like this will be generated in the YAML report:

.. code-block:: yaml

    - annotation_data: This code is the only remaining piece of our first commit!
      annotation_token: '.. fun_fact:'
      filename: foo/bar/something.py
      found_by: python
      line_number: 33

*Note that the rest of the comment is ignored in the report.*

Configuration for an "async" annotation type, denoted by the annotation token ``.. async:`` and choices denoting the
types of asynchronous processors hooked up to it:

.. code-block:: yaml

    annotations:
         ".. async:": choices: ['reporting_ingestion', 'published_internally', 'published_externally']

This means that any ``.. async:`` annotation must include one or more of those choices. With these Python comments:

.. code-block:: python

    """
    Push this update onto the marketing site's processing queue

    .. async: published_internally
    """

.. code-block:: python

    """
    Push this to our reporting queue and the partner reporting queue

    .. async: reporting_ingestion, published_externally
    """

.. code-block:: python

    """
    Push to both the wiki RSS feed and our home page

    .. async: published_internally published_externally
    """

This will be generated in the YAML report:

.. code-block:: yaml

    - annotation_data:
        - published_internally
      annotation_token: '.. async:'
      filename: foo/bar/data.py
      found_by: python
      line_number: 12
    - annotation_data:
        - reporting_ingestion
        - published_externally
      annotation_token: '.. async:'
      filename: foo/bar/reporting.py
      found_by: python
      line_number: 13
    - annotation_data:
        - published_internally
        - published_externally
      annotation_token: '.. async:'
      filename: foo/bar/rss.py
      found_by: python
      line_number: 333

If a comment is made that does not include only valid choices, such as:

.. code-block:: python

    """
    Push this to our reporting queue

    .. async: This one only goes to our reporting queue
    """

You will receive a linting error such as:

.. code-block:: bash

    Search failed due to linting errors!
    1 errors:
    ---------------------------------

    foo/bar/data.py::17: "This" is not a valid choice for ".. async:". Expected one of ['reporting_ingestion', 'published_internally', 'published_externally'].

Annotation Groups
=================
In addition to choices, you can combine several annotations into a group. When configured this way you can combine free
form text comments with choices to allow structured and unstructured data to work together. Linting will enforce that
that all group members are consecutive, though ordering does not matter.

**Examples**

With this configuration there is a group of 3 annotations that must occur together. ``.. reporting:`` and
``.. reporting_consumers:`` are free form text types and ``.. reporting_types:`` is a choice type.

.. code-block:: yaml

    annotations:
        reporting:
            - ".. reporting:"
            - ".. reporting_types:":
                choices: [internal, partner]
            - ".. reporting_consumers:"

With this comment:

.. code-block:: python

    """
    Send an event to the reporting engine, for internal events only

    .. reporting: Reporting events for the mobile app
    .. reporting_types: internal
    .. reporting_consumers: Recommendations and email marketing events
    """

You would get this in the report:

.. code-block:: yaml

    openedx/core/djangoapps/user_api/legacy_urls.py:
     - annotation_data: Reporting events for the mobile app
       annotation_token: '.. reporting:'
       filename: foo/bar/events.py
       found_by: python
       line_number: 16
     - annotation_data:
       - internal
       annotation_token: '.. reporting_types:'
       filename: foo/bar/events.py
       found_by: python
       line_number: 16
     - annotation_data: Recommendations and email marketing events
       annotation_token: '.. reporting_consumers:'
       filename: openedx/core/djangoapps/user_api/legacy_urls.py
       found_by: python
       line_number: 18

This comment also works even though the ordering is different:

.. code-block:: python

    """
    Send an event to the reporting engine, for internal events only

    .. reporting_types: internal
    .. reporting: Reporting events for the mobile app
    .. reporting_consumers: Recommendations and email marketing events
    """

