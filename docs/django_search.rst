Django Model Search Tool
------------------------

code_annotations django_find_annotations::
    Usage: code_annotations django_find_annotations [OPTIONS]

    Subcommand for dealing with annotations in Django models.

    --config_file FILE                Path to the configuration file
    --seed_safelist
                                      Generate an initial safelist file based on
                                      the current Django environment.  [default:
                                      False]

    --list_local_models
                                      List all locally defined models (in the
                                      current repo) that require annotations.
                                      [default: False]

    --report_path TEXT              Location to write the report
    -v                              Verbosity level (-v through -vvv)
    --lint                          Enable or disable linting checks  [default:
                                      False]
    --report                        Enable or disable writing the report
                                      [default: False]
    --coverage                      Enable or disable coverage checks  [default:
                                      False]
    --help                          Show this message and exit.


Overview
========
The Django Model Search Tool, or Django Tool, is written to provide more structured searching and validation in a place
where data is often stored. Since all of the models in a package can be enumerated it is possible, though not required,
to use this tool to positively assert that **all** concrete (non-proxy, non-abstract) models in a project are annotated
in some way. If you do not need this functionality and simply want to find annotations and create a report, the static
search tool is much easier to configure and can search all of your code (instead of just model docstrings).

.. important::
    To use the Django tool you must first set the ``DJANGO_SETTINGS_MODULE`` environment variable to point to
    a valid settings file. The tool will initialize Django and use its introspection to find models. The settings file
    should have ``INSTALLED_APPS`` configured for all Django apps that you wish to have annotated. See the
    `Django Docs`_ for details.

.. _Django Docs: https://docs.djangoproject.com/en/dev/topics/settings/#designating-the-settings

The edX use case which prompted the creation of this tool is evident in many of our tests and code samples. It is to
be able to track the storage, use, and retirement of personally identifiable information (PII) across our many projects
and repositories. Since the majority of our information is stored via Django models, this tool helps us make sure that
at least all of those are annotated to assert whether they contain PII or not.

The tool works by actually running your Django app or project in a development-like environment. It then uses Django's
introspection tools to find all installed apps and enumerate their models. Each model further enumerates its inheritance
tree and all model docstrings are checked for annotations. All annotations in all models and their ancestors are
added to the list.

The Safelist
============
In order to assert that **all** concrete models in a project are annotated, it is also necessary to be able to annotate
models that are otherwise installed in the Python virtual environment and are not part of your source tree. Models in
your source tree are called "local models", and ones otherwise installed in the Python environment are "non-local"
models. In order to annotate non-local models, which may come from other repositories or PyPI packages, use the
"safelist" feature.

"Safe" in safelist doesn't mean that the models themselves do not require annotation, but rather it gives developers a
place to annotate those models and put them in a known state. When setting up a repository to use the Django tool, you
should use the ``--seed_safelist`` option to generate an initial safelist template that contains empty entries for all
non-local models. In order for those models to count as "covered", you must add annotations to them in the safelist.

An freshly created safelist:

.. code-block:: yaml

    social_django.Association: {}
    social_django.Code: {}

And one that has been annotated:

.. code-block:: yaml

    social_django.Association:
      ".. no_pii:": "This model has no PII"
    social_django.Code:
      ".. pii:": "Email address"
      ".. pii_types:": other
      ".. pii_retirement:": local_api

.. note::
    Note that each model can only have one annotation for each token type. For example, it would be invalid to add a
    second ``.. no_pii:`` annotation to ``social_django.Association``.

.. important::
    Some types of "local" models are procedurally generated and do not have files in code, e.g. models created by
    django-simple-history. In those unusual circumstances you can choose to annotate them in the safelist to make
    sure they are covered.

Coverage
========
The second unique part of the Django tool is the model coverage report and check. Since we are able to find all models
in a project with a reasonable degree of accuracy we can target a percentage of them that must be annotated. When you
run the tool with the ``--coverage`` option it will compare the percentage of annotated models against the configuration
variable ``coverage_target``. If the ``coverage_target`` is not met the search will fail and a list of the un-annotated
models will be displayed.

Having annotations at any level of a model's inheritance will result in that model being considered "covered".

Lint and Report
===============
This tool supports the same ``--lint`` and ``--report`` options as the :doc:`static_search` tool, and
they are functionally the same. Linting will fail on malformed annotations found in model docstrings, such as bad
choices or incomplete groups. Reporting will write out a report file in the same format as the Static Tool, but with
some additional information in the ``extra`` key such as the ``model_id``, which is a string in the format of
"parentApp.ModelClassName", as Django uses to represent models internally. It also has the full model docstring in
``full_comment``.

If a model inherits from another model that has annotations, those annotations will be included in the report under the
child model's name, as well as any annotations in the model itself.

Local Models
============
Finally, to help find models in the local source tree that still need to be annotated, the tool has a
``--list_local_models`` option. This will output the model id of all models that still need to be annotated.
