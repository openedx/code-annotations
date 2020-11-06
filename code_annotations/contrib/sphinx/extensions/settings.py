"""
Sphinx extension for viewing (non-toggle) setting annotations.
"""
import os

import pkg_resources

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective

from .base import find_annotations, quote_value


def find_settings(source_path):
    """
    Find the Django settings as defined in the configuration file.

    Return:
        settings (dict): Django settings indexed by name.
    """
    config_path = pkg_resources.resource_filename(
        "code_annotations",
        os.path.join("contrib", "config", "setting_annotations.yaml"),
    )
    return find_annotations(source_path, config_path, ".. setting_name:")


class Settings(SphinxDirective):
    """
    Sphinx directive to document Django settings in a single documentation page.

    Use this directive as follows::

        .. settings::
            :folder_path: lms/envs/common.py

    This directive supports the following configuration parameters:

    - ``settings_source_path``: absolute path to the repository file tree. E.g:

        settings_source_path = os.path.join(os.path.dirname(__file__), "..", "..")

    - ``settings_repo_url``: Github repository where the code is hosted. E.g:

        settings_repo_url = "https://github.com/edx/myrepo"

    - ``settings_repo_version``: current version of the git repository. E.g:

        import git
        try:
            repo = git.Repo(search_parent_directories=True)
            settings_repo_version = repo.head.object.hexsha
        except git.InvalidGitRepositoryError:
            settings_repo_version = "master"
    """

    required_arguments = 0
    optional_arguments = 1
    option_spec = {"folder_path": directives.unchanged}

    def run(self):
        """
        Public interface of the Directive class.

        Return:
            nodes (list): nodes to be appended to the resulting document.
        """
        return list(self.iter_nodes())

    def iter_nodes(self):
        """
        Iterate on the docutils nodes generated by this directive.
        """
        folder_path = self.options.get("folder_path", "")
        source_path = os.path.join(self.env.config.settings_source_path, folder_path)
        settings = find_settings(source_path)
        # folder_path can point to a file or directory
        root_folder = folder_path if os.path.isdir(source_path) else os.path.dirname(folder_path)
        for setting_name in sorted(settings):
            setting = settings[setting_name]
            # setting["filename"] is relative to the root_path
            setting_filename = os.path.join(root_folder, setting["filename"])
            setting_default_value = setting.get(".. setting_default:", "Not defined")
            setting_default_node = nodes.literal(
                text=quote_value(setting_default_value)
            )
            setting_section = nodes.section("", ids=["setting-{}".format(setting_name)])
            setting_section += nodes.title(text=setting_name)
            setting_section += nodes.paragraph("", "Default: ", setting_default_node)
            setting_section += nodes.paragraph(
                "",
                "Source: ",
                nodes.reference(
                    text="{} (line {})".format(
                        setting["filename"], setting["line_number"]
                    ),
                    refuri="{}/blob/{}/{}#L{}".format(
                        self.env.config.settings_repo_url,
                        self.env.config.settings_repo_version,
                        setting_filename,
                        setting["line_number"],
                    ),
                ),
            )
            setting_section += nodes.paragraph(
                text=setting.get(".. setting_description:", "")
            )
            if setting.get(".. setting_warning:") not in (None, "None", "n/a", "N/A"):
                setting_section += nodes.warning(
                    "", nodes.paragraph("", setting[".. setting_warning:"])
                )
            yield setting_section


def setup(app):
    """
    Declare the Sphinx extension.
    """
    app.add_config_value(
        "settings_source_path", os.path.abspath(".."), "env",
    )
    app.add_config_value("settings_repo_url", "", "env")
    app.add_config_value("settings_repo_version", "master", "env")
    app.add_directive("settings", Settings)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
