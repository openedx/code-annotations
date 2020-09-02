Change Log
----------

..
   All enhancements and patches to code_annotations will be documented
   in this file.  It adheres to the structure of http://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (http://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

[0.6.0] - 2020-08-27
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Add support for multiline annotations for lines prefixed with single-line comment signs ("#")

[0.5.1] - 2020-08-25
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Add support for warnings in the ``featuretoggles`` Sphinx extension

[0.5.0] - 2020-08-06
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Add ``featuretoggles`` Sphinx extension
* Include ``config_and_tools`` folder in pip-installable package
* Add ADR 0001-config-and-tools.rst for adding a place in this repository for shared annotation configs and supporting tools.

[0.4.0] - 2020-07-22
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Add support for multi-line code annotations

[0.3.4] - 2020-05-06
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Removed support for Django<2.2
* Removed support for Python2.7 and Python3.6
* Added support for Python3.8

[0.3.2] - 2019-06-21
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
_____

* Add RST anchors throughout annotation report docs


[0.3.1] - 2019-03-20
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
_____

* Bump pyyaml to version 5.1 to address unsafe load() CVE.


[0.1.0] - 2018-11-16
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added
_____

* First release on PyPI.
