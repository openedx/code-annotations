Sphinx extensions
-----------------

``featuretoggles``
==================

This package can be used to document the feature toggles in your code base. To do so,
add the following to your ``conf.py``::

    extensions = ["code_annotations.config_and_tools.sphinx.extensions.featuretoggles"]
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
