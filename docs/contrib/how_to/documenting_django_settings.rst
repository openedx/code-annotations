***********************************
How to: Documenting Django settings
***********************************

.. contents::
   :depth: 1
   :local:

Types of Django Settings
========================

For documentation purposes, in the Open edX codebase there are two types of Django settings:

* Non-boolean Django settings.
* Boolean Django settings, also known as feature toggles.

This how-to is concerned with the non-boolean Django settings. For boolean Django settings, or feature toggles, read :doc:`how-to document feature toggles <edx_toggles:how_to/documenting_new_feature_toggles>` instead.

The documentation of Django settings is a crucial source of information for a very wide audience, including Open edX operators, product owners and developers. The documentation will be available to developers directly in code, and extracted into a human-readable document to be used by all audiences, and especially for Open edX operators.

Please keep all of these audiences in mind when crafting your documentation.

Example Documentation
=====================

Boilerplate template
--------------------

Copy-paste this boilerplate template to document a Django setting::

    # .. setting_name: SOME_SETTING_NAME
    # .. setting_default: Replace this with the default (non-boolean) value of the setting.
    # .. setting_description: Add here a detailed description of the purpose and usage of this setting.
    #   Note that all annotations can be spread over multiple lines by prefixing every line after the first by
    #   at least three spaces (two spaces plus the leading space).
    # .. setting_warning: (Optional) Add here additional instructions that users should be aware of. For instance, dependency
    #   on additional settings or feature toggles should be referenced here. If this field is not needed, simply remove it.
    SOME_SETTING_NAME = ...

If you have a dict of settings, you can use the following example::

    # .. setting_name: SOME_SETTING_DICT_NAME
    # .. setting_default: dict of settings
    # .. setting_description: First provide a general description about all the settings in the dict. Then include a sentence like:
    #   See SOME_SETTING_DICT_NAME[XXX] documentation for details of each setting.
    SOME_SETTING_DICT_NAME = dict(

        # .. setting_name: SOME_SETTING_DICT_NAME['SOME_SETTING_NAME']
        # ...  # See docs above for the other setting annotations.
        SOME_SETTING_NAME = ...,

    )

Additional details
==================

There are a variety of tips in `certain sections of the how-to for documenting feature toggles`_, that are applicable to documenting non-boolean Django settings as well, but are not duplicated in this document. We recommend you get familiar with the applicable subsections of "Additional details" and "Documenting legacy feature toggles" from the feature toggle how-to.

.. _certain sections of the how-to for documenting feature toggles: https://edx.readthedocs.io/projects/edx-toggles/en/latest/how_to/documenting_new_feature_toggles.html#additional-details

Additional resources
====================

The documentation format used to annotate non-boolean Django settings is also available from code-annotations repository: `setting_annotations.yaml <https://github.com/edx/code-annotations/blob/master/code_annotations/contrib/config/setting_annotations.yaml>`__.
