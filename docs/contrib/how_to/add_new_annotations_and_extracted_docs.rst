**********************************************
How to: Add new annotations and extracted docs
**********************************************

.. contents::
   :depth: 1
   :local:

Example annotations and automated docs
======================================

Annotations are a great way to keep documentation close to the code, but also be able to extract into documentation to be published on Readthedocs.

As an example, we have added `feature toggle annotations to the edx-platform codebase`_. A `Readthedocs document with the edx-platform feature toggles`_ has been generated from them.

.. _feature toggle annotations to the edx-platform codebase: https://github.com/edx/edx-platform/search?q=toggle_name
.. _Readthedocs document with the edx-platform feature toggles: https://edx.readthedocs.io/projects/edx-platform-technical/en/latest/featuretoggles.html

Add your own annotations and docs
=================================

The following steps need to be performed to document new types of annotations in edx-platform. Adapt the final steps as appropriate for other services.

* Define a `new annotation format in code_annotations/contrib/config`_. See the feature toggle annotations as an example.
* Create a `Sphinx extension to collect these annotations`_. You can base it on the featuretoggles and settings extensions.
* Read and update :doc:`../sphinx_extensions`.
* Add a new documentation page in the `edx-platform technical docs that will use this Sphinx extension`_.  Adapt this step as needed for other services.
* As required, add `custom linting for the new annotations to edx-lint`_. Again, follow the toggle and setting checkers as examples.

.. _new annotation format in code_annotations/contrib/config: https://github.com/edx/code-annotations/tree/master/code_annotations/contrib/config
.. _Sphinx extension to collect these annotations: https://github.com/edx/code-annotations/tree/master/code_annotations/contrib/sphinx/extensions
.. _edx-platform technical docs that will use this Sphinx extension: https://github.com/edx/edx-platform/tree/master/docs/technical
.. _custom linting for the new annotations to edx-lint: https://github.com/edx/edx-lint/blob/master/edx_lint/pylint/annotations_check.py
