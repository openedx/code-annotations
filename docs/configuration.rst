Configuration
-------------

Configuring Code Annotations is a pretty simple affair. Here is an example showing all options:

.. code-block:: yaml

    source_path: /path/to/be/searched/
    report_path: /path/to/write/report/to/
    safelist_path: .annotation_safe_list.yml
    coverage_target: 100.0
    annotations:
        ".. annotation_token::":
        ".. annotation_token2::":
        ".. choice_annotation::":
            choices: [choice_1, choice_2, choice_3]
        name_of_annotation_group:
            - ".. first_group_token::":
            - ".. second_group_token::":
                choices: [choice_4, choice_5]
            - ".. third_group_token::":
                choices: [choice_a, choice_b, choice_c, choice_d]
    extensions:
        python:
            - py
            - py3
        javascript:
            - js

``source_path``
    The file or directory to be searched for annotations. If a directory, it will be searched recursively. This can be
    overridden with the ``--source_path`` command line option.

``report_path``
    The directory where the YAML report file will be written. If it does not exist, it will be created.

``safelist_path``
    The path to a safelist, used by the Django Search tool to find annotations in models that are defined outside of
    the local source tree. See :doc:`safelist` for more information.

``coverage_target``
    A number from 0 - 100 that represents the percentage of Django models in the project that should have annotations.
    The Django Search tool will fail when run with the ``--coverage`` option if the covered percentage is below this
    number. See :doc:`django_coverage` for more information.

``annotations``
    The definition of annotations to be searched for. There are two types of annotations.

    - Basic, or comment, annotations such as ``annotation_token`` and ``first_group_token`` above, allow for
      free-form text following the annotation itself. Note the colon after the annotation token! In configuration this
      type is a mapping type, mapping to a null value.

      Note: At this time the comment must be all on one line. Multi-line annotation comments are not yet supported.

    - Choice annotations, such as ``choice_annotation``, ``second_group_token`` and ``third_group_token``, limit the
      potential values of the annotation to the ones listed in ``choices``. This can help enforce consistency across the
      code base and make it easier to find or group specific values of annotations. The key "choices" is a keyword for
      Code Annotations and must be included in the configuration.

    In addition to the two types of annotations, it is also possible to group several annotations together into a fixed
    structure. In our example ``name_of_annotation_group`` is a group consisting of 3 annotations. When grouped, all
    of the annotations in the group **must** be present, or linting will fail. The order of the grouping does not
    matter as long as all of them are found before any other annotations. Only one of each annotation is allowed in a
    group. See :doc:`writing_annotations` for more information and examples.

``extensions``
    Code Annotations uses Stevedore extensions to extend the capability of finding new language comments. Language
    extensions are turned on here. The key is the extension name, as given in the ``setup.py`` or ``setup.cfg`` of the
    package that installed the extension. The values are a list of file extensions that, when found, will be passed to
    the extension for annotation searching. See :doc:`extensions` for details.
