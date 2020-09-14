Sphinx extensions
-----------------

This package can be used to document a couple things in your code case. The following Sphinx extensions will help you generate human-readable docs by parsing the source code, instead of importing it. This allows you to document your code base in any language, without having to install all its dependencies.

.. _sphinx_featuretoggles:

``featuretoggles``
==================

Feature toggles are an Open edX mechanism by which features can be individually enabled or disabled. To document these feature toggles,
add the following to your ``conf.py``::

    extensions = ["code_annotations.contrib.sphinx.extensions.featuretoggles"]
    featuretoggles_source_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
    featuretoggles_repo_url = "https://github.com/edx/yourrepo"
    try:
        featuretoggles_repo_version = git.Repo(search_parent_directories=True).head.object.hexsha
    except git.InvalidGitRepositoryError:
        pass

Then, in an ``.rst`` file::

    .. featuretoggles::

.. _sphinx_settings:

``settings``
============

This package also comes with tooling to annotate Django settings. Settings that should be annotated include non-standard Django settings, and settings that do not correspond to feature toggles (in which case feature toggle annotations should be used instead). Similar to feature toggles, Django setting annotations can also be parsed to generate human-readable documentation. Add the following to your ``conf.py``::

    extensions = ["code_annotations.contrib.sphinx.extensions.settings"]

Define the following variables, just like for the :ref:`featuretoggles <sphinx_featuretoggles>` extension::

    settings_source_path = ...
    settings_repo_url = ...

Then, in an ``.rst`` file::

    .. settings::
        :folder_path: path/to/settings.py
