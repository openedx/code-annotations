Configuration
-------------

Configuring Code Annotations is a pretty simple affair. Here is an example showing all options:

.. code-block:: yaml

    source_path: /path/to/be/searched/
    report_path: /path/to/write/report/to/
    safelist_path: .annotation_safe_list.yml
    coverage_target: 100.0
    annotations:
        ".. annotation_token:":
        ".. annotation_token2:":
        ".. choice_annotation:":
            choices: [choice_1, choice_2, choice_3]
        name_of_annotation_group:
            - ".. first_group_token:":
            - ".. second_group_token:":
                choices: [choice_4, choice_5]
            - ".. third_group_token:":
                choices: [choice_a, choice_b, choice_c, choice_d]
    extensions:
        python:
            - py
            - py3
        javascript:
            - js
    # Options only used for human readable reports
    report_template_dir: /my_custom_templates/report_templates/
    rendered_report_dir: rendered_reports
    rendered_report_format: html
    rendered_report_source_link_prefix: https://github.com/my_org/my_project/blob/master/
    trim_filename_prefixes:
        - /my_org/my_project/
        - /my_project/venv/lib/python3.11/
    third_party_package_location: site-packages

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

``report_template_dir`` (optional)
    When running the ``generate_docs`` comman you can specify a custom template directory here to override the default templates if you would like a different look.

``rendered_report_dir`` (optional)
    When running the ``generate_docs`` command, this option specifies the directory where the rendered report will be written. The default is ``annotation_reports`` in the current working directory.

``rendered_report_format`` (optional)
    When running the ``generate_docs`` command, this option specifies the format of the rendered report. Options are ``html`` and ``rst``. The default is ``rst``.

``rendered_report_source_link_prefix`` (optional)
    When running the ``generate_docs`` command, this option specifies the URL prefix to use when linking to source files in the rendered report. When specified, "local" source files (those not found in site-packages) will be appended to this setting to create hyperlinks to the lines in source files online. For Github links this is the correct format: ``https://github.com/openedx/edx-platform/blob/master/``. The default is an None.

``trim_filename_prefixes`` (optional)
    When running the ``generate_docs`` command, this option specifies a list of prefixes to remove from the beginning of filenames in the rendered report. This is useful for making the report more readable by removing long, repetitive prefixes of the type often found in a Django search. The default is an empty list.

``third_party_package_location`` (optional)
    When running the ``generate_docs`` command, this option specifies the location of third party packages that may have been found in a Django search. This is used to determine if a file is a third party file or not. The default is ``site-packages``.
