"""
Annotation searcher for static comment searching via Stevedore plugins.
"""

import os

from stevedore import named

from code_annotations.base import BaseSearch
from code_annotations.exceptions import ConfigurationException


class StaticSearch(BaseSearch):
    """
    Handles static code searching for annotations.
    """

    def __init__(self, config, source_path, report_path, verbosity):
        """
        Initialize for StaticSearch.

        Args:
            config: Configuration file path
            source_path: Directory to be searched for annotations
            report_path: Directory to write the report file to
            verbosity: Integer representing verbosity level (0-3)
        """
        super(StaticSearch, self).__init__(config, report_path, verbosity)

        self.mgr = None

        if not source_path and 'source_path' not in self.config:
            raise ConfigurationException('source_path not given and not in configuration file')

        if source_path:
            self.config['source_path'] = source_path

        self.echo("Configured for source path: {}".format(self.config['source_path']))
        self.configure_extensions()

    def configure_extensions(self):
        """
        Configure the Stevedore NamedExtensionManager.

        Raises:
            ConfigurationException
        """
        # These are the names of all of our configured extensions
        configured_extension_names = self.config['extensions'].keys()

        # Load Stevedore extensions that we are configured for (and only those)
        self.mgr = named.NamedExtensionManager(
            names=configured_extension_names,
            namespace='annotation_finder.searchers',
            invoke_on_load=True,
            on_load_failure_callback=self.load_failed_handler,
            invoke_args=(self.config, self.echo),
        )

        # Output extension names listed in configuration
        self.echo.echo_vv("Configured extension names: {}".format(" ".join(configured_extension_names)))

        # Output found extension entry points from setup.py|cfg (whether or not they were loaded)
        self.echo.echo_vv("Stevedore entry points found: {}".format(str(self.mgr.list_entry_points())))

        # Output extensions that were actually able to load
        self.echo.echo_v("Loaded extensions: {}".format(" ".join([x.name for x in self.mgr.extensions])))

        if len(self.mgr.extensions) != len(configured_extension_names):
            raise ConfigurationException('Not all configured extensions could be loaded! Asked for {} got {}.'.format(
                configured_extension_names, self.mgr.extensions
            ))

    def load_failed_handler(self, *args, **kwargs):
        """
        Handle failures to load an extension.

        Dumps the error and raises an exception. By default these
        errors just fail silently.

        Args:
            *args:
            **kwargs:

        Raises:
            ConfigurationException
        """
        self.echo(args)
        self.echo(kwargs)
        raise ConfigurationException('Failed to load a plugin, aborting.')

    def search_extension(self, ext, file_handle, file_extensions_map, filename_extension):
        """
        Execute a search on the given file using the given extension.

        Args:
            ext: Extension to execute the search on
            file_handle: An open file handle search
            file_extensions_map: Dict mapping of extension names to configured filename extensions
            filename_extension: The filename extension of the file being searched

        Returns:
            Tuple of (extension name, list of found annotation dicts)
        """
        # Only search this file if we are configured for its extension
        if filename_extension in file_extensions_map[ext.name]:
            # Reset the read handle to the beginning of the file in case another
            # extension moved it
            file_handle.seek(0)

            ext_results = ext.obj.search(file_handle)

            if ext_results:
                return ext.name, ext_results

        return ext.name, None

    def _search_one_file(self, full_name, known_extensions, file_extensions_map, all_results):
        """
        Perform an annotation search on a single file, using all extensions it is configured for.

        Args:
            full_name: Complete filename
            known_extensions: List of all file name extensions we are configured to work on
            file_extensions_map: Mapping of file name extensions to Stevedore extensions
            all_results: A dict of annotations returned from search()
        """
        filename_extension = os.path.splitext(full_name)[1][1:]

        if filename_extension not in known_extensions:
            self.echo.echo_vvv(
                "{} is not a known extension, skipping ({}).".format(filename_extension, full_name)
            )
            return

        self.echo.echo_vvv(full_name)

        # TODO: This should probably be a generator so we don't have to store all results in memory
        with open(full_name, 'r') as file_handle:
            # Call search_extension on all loaded extensions
            results = self.mgr.map(self.search_extension, file_handle, file_extensions_map, filename_extension)

            # Strip out plugin name, as it's already in the annotation
            results = [r for _, r in results]

            # Format and add the results to our running full set
            self.format_file_results(all_results, results)

    def search(self):
        """
        Walk the source tree, send known file types to extensions.

        Returns:
            Dict of all found annotations keyed by filename
        """
        # Index the results by extension name
        file_extensions_map = {}
        known_extensions = set()
        for extension_name in self.config['extensions']:
            file_extensions_map[extension_name] = self.config['extensions'][extension_name]
            known_extensions.update(self.config['extensions'][extension_name])

        all_results = {}

        if os.path.isfile(self.config['source_path']):
            self._search_one_file(self.config['source_path'], known_extensions, file_extensions_map, all_results)
        else:
            for root, _, files in os.walk(self.config['source_path']):
                for filename in files:
                    full_name = os.path.join(root, filename)
                    self._search_one_file(full_name, known_extensions, file_extensions_map, all_results)

        return all_results
