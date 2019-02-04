Static Search Tool
------------------

code_annotations static_find_annotations::
    Usage: code_annotations static_find_annotations [OPTIONS]

      Subcommand to find annotations via static file analysis.

    Options:
      --config_file FILE      Path to the configuration file
      --source_path PATH      Location of the source code to search
      --report_path TEXT      Location to write the report
      -v, --verbosity         Verbosity level (-v through -vvv)
      --lint                  Enable or disable linting checks  [default: True]
      --report                Enable or disable writing the report file  [default: True]
      --help                  Show this message and exit.

Overview
========
The Static Search Tool, or Static Tool, is written as an extensible way to find annotations in code. The tool performs
static analysis on the files themselves instead of relying on the language's runtime and introspection. It
will optionally write a report file in YAML, and optionally check for annotation validity (linting).

Linting
=======
When passed the ``--lint`` option, each annotation will be checked for the following:

- Choice annotations must have one or more of the configured choices
- Groups must have their annotations occur consecutively, though their order doesn't matter

If any of these checks fails, all errors will be printed and the return code of the command will be non-zero. If the
``--report`` option was also provided no report will be written.

Reporting
=========
The YAML report is the main output of the Static Tool. It is a simple YAML document that contains a list of found
annotations, grouped by file. Each annotation entry has the following keys:

.. code-block:: yaml

    {
        'found_by': 'python',  # The name of the extension which found the annotation
        'filename': 'foo/bar/file.py',  # The filename where the extension was found
        'line_number': 101,  # The line number of the beginning of the comment which contained the annotation
        'annotation_token': '.. no_pii:',  # The annotation token found
        'annotation_data': 'This model contains no PII.',  # The comment, or choices, found with the annotation token
    }

If an annotation is in a group, there will also be a `report_group_id`. This key is unique for each found group,
allowing tools further down the toolchain to keep them together for presentation.

Extensions can also send back some additional data in an ``extra`` key, if desired. The Django Model Search Tool does
this to return the Django app and model name.

Extensions
==========
The Static Tool uses Stevedore named extensions to allow for language-specific functionality. Python and Javascript
extensions are included, many others can be made easily as needed. We will gladly accept pull requests for new languages
or you can release them yourself on PyPI. For more information on extensions, see :doc:`extensions` and
:doc:`configuration`.
