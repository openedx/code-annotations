Annotations Config and Tools
****************************

Status
======

Accepted

Context
=======

While working on a particular usage of this general code annotations tool, we found we did not have a good home for some shared configs and tools.

The original usage of this generic tool was for annotating PII in the Open edX platform. The config for `PII annotations`_ is currently duplicated in each repository.

The new instances of annotation configs arose to support documenting Open edX feature toggles and non-toggle settings. Each of these will also have Sphinx extensions to support documentation. To start, the `feature toggles annotation config`_ was added to the ``edx-toggles`` repository, but there was no good home for the non-toggle settings annotation config, nor the documentation tools.

.. _PII annotations: https://github.com/edx/edx-cookiecutters/blob/7cf718093e7cca5c701a29fcbaa84660326b09ed/cookiecutter-django-app/%7B%7Bcookiecutter.repo_name%7D%7D/.pii_annotations.yml
.. _feature toggles annotation config: https://github.com/edx/edx-toggles/blob/0986b10a806944fd4d00847501ff4f7e3904a2cb/feature_toggle_annotations.yaml

Decision
========

The code annotation tool is generic and specific annotation configs are logically separate. At the same time, it was decided that having a single place for annotation configs and there supporting tools would be efficient for our engineers, as well as potentially beneficial for sharing outside of Open edX. Additionally, we decided not to add the overhead of managing a separate repository at this time. Instead, we will add a ``config_and_tools`` directory in this repository to contain any shared annotation config files and supporting tools.

It is acknowledged that this need not be a permanent solution, but is a useful place to begin.

Any affect on how the PII annotations are implemented, or where they are stored, is outside the scope of this decision.

Consequences
============

We will move the new toggles annotations and its supporting tools to the new ``config_and_tools`` directory.
