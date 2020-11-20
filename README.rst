code-annotations
=============================

|pypi-badge| |travis-badge| |codecov-badge| |doc-badge| |pyversions-badge|
|license-badge|

Extensible tools for parsing annotations in codebases

Overview
--------

This package provides configurable and extensible tools for parsing and
summarizing annotations in a wide range of codebases. Originally intended for
annotating code which stores personally identifiable information (PII), these
tools are optimized for that use case but can be generalized for other types of
annotations.

Additionally, a logically separate part of this repository will contain specific annotation configurations and supporting tools, such as Sphinx extensions for documenting specific annotation types. See the ``contrib`` folder.

Documentation
-------------

The full documentation is at https://code-annotations.readthedocs.org.

License
-------

The code in this repository is licensed under the AGPL 3.0 unless
otherwise noted.

Please see ``LICENSE.txt`` for details.

How To Contribute
-----------------

Contributions are very welcome.

Please read `How To Contribute <https://github.com/edx/edx-platform/blob/master/CONTRIBUTING.rst>`_ for details.

Even though they were written with ``edx-platform`` in mind, the guidelines
should be followed for Open edX code in general.

PR description template should be automatically applied if you are sending PR from github interface; otherwise you
can find it it at `PULL_REQUEST_TEMPLATE.md <https://github.com/edx/code-annotations/blob/master/.github/PULL_REQUEST_TEMPLATE.md>`_

Issue report template should be automatically applied if you are sending it from github UI as well; otherwise you
can find it at `ISSUE_TEMPLATE.md <https://github.com/edx/code-annotations/blob/master/.github/ISSUE_TEMPLATE.md>`_

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org.

Getting Help
------------

Have a question about this repository, or about Open edX in general?  Please
refer to this `list of resources`_ if you need any assistance.

.. _list of resources: https://open.edx.org/getting-help


.. |pypi-badge| image:: https://img.shields.io/pypi/v/code-annotations.svg
    :target: https://pypi.python.org/pypi/code-annotations/
    :alt: PyPI

.. |travis-badge| image:: https://travis-ci.com/edx/code-annotations.svg?branch=master
    :target: https://travis-ci.com/edx/code-annotations
    :alt: Travis

.. |codecov-badge| image:: http://codecov.io/github/edx/code-annotations/coverage.svg?branch=master
    :target: http://codecov.io/github/edx/code-annotations?branch=master
    :alt: Codecov

.. |doc-badge| image:: https://readthedocs.org/projects/code-annotations/badge/?version=latest
    :target: http://code-annotations.readthedocs.io/en/latest/
    :alt: Documentation

.. |pyversions-badge| image:: https://img.shields.io/pypi/pyversions/code-annotations.svg
    :target: https://pypi.python.org/pypi/code-annotations/
    :alt: Supported Python versions

.. |license-badge| image:: https://img.shields.io/github/license/edx/code-annotations.svg
    :target: https://github.com/edx/code-annotations/blob/master/LICENSE.txt
    :alt: License
