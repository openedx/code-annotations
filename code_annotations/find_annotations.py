"""
Click command to do static annotation searching via Stevedore plugins.
"""
import datetime
import errno
import os

import yaml
from stevedore import named

from code_annotations.exceptions import ConfigurationException
from code_annotations.helpers import VerboseEcho, read_configuration


class StaticSearch(object):
    """
    Handles static code searching for annotations.
    """

    config = {}
    mgr = None

    def __init__(self, config, source_path, report_path, verbosity):
        """
        Initialize for StaticSearch.

        Args:
            config: Configuration file path
            source_path: Directory to be searched for annotations
            report_path: Directory to write the report file to
            verbosity: Integer representing verbosity level (1-3)
        """
        # Global logger for this script, shared with extensions
        self.echo = VerboseEcho()
        self.configure(config, source_path, report_path, verbosity)

    def configure(self, config_file_path, source_path, report_path, verbosity):
        """
        Read the configuration file, and handle command line overrides.

        Args:
            config_file_path: Location of the configuration file
            source_path: Path to the code to be searched
            report_path: Directory where the report will be generated
            verbosity: Integer indicating the runtime verbosity level

        Returns:
            Configuration dict, updated with overrides
        """
        # TODO: Add include / exclude directories
        self.echo.echo('Reading configuration from {}'.format(config_file_path))

        self.config = read_configuration(config_file_path)

        if not source_path and not self.config['source_path']:
            raise ConfigurationException('source_path not given and not in configuration file')

        if not report_path and not self.config['report_path']:
            raise ConfigurationException('report_path not given and not in configuration file')

        if source_path:
            self.config['source_path'] = source_path

        if report_path:
            self.config['report_path'] = report_path

        # This is a runtime option, shouldn't be in the config file
        self.config['verbosity'] = verbosity
        self.echo.set_verbosity(verbosity)

        self.configure_extensions()

        self.echo.echo_v("Verbosity level set to {}".format(self.config['verbosity']))
        self.echo.echo_v("Configuration:")
        self.echo.echo_v(self.config)
        self.echo.echo(
            "Configured for source path: {}, report path: {}".format(
                self.config['source_path'],
                self.config['report_path'])
        )

    def configure_extensions(self):
        """
        Configure the Stevedore NamedExtensionManager.

        Returns:
            None
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

        # Output found extension entry points (whether or not they were loaded)
        self.echo.echo_vv("Stevedore entry points found: {}".format(str(self.mgr.list_entry_points())))

        # Output extensions that were actually able to load
        self.echo.echo_v("Loaded extensions: {}".format(" ".join([x.name for x in self.mgr.extensions])))

    def load_failed_handler(self, *args, **kwargs):
        """
        Handle failures to load an extension.

        Dumps the error and raises an exception. By default these
        errors just fail silently.

        Args:
            *args:
            **kwargs:

        Returns:
            None

        Raises:
            ConfigurationException
        """
        self.echo.echo(args)
        self.echo.echo(kwargs)
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
        # Reset the read handle to the beginning of the file in case another
        # extension already moved it
        file_handle.seek(0)

        # Only search this file if we are configured for its extension
        if filename_extension in file_extensions_map[ext.name]:
            ext_results = ext.obj.search(file_handle)

            if ext_results:
                return ext.name, ext_results

        return ext.name, None

    def format_file_results(self, all_results, results):
        """
        Add all extensions' search results for a file to the overall results.

        Args:
            all_results: Aggregated results to add the results to
            results: Results of search() on a single file

        Returns:
            None, modifies all_results
        """
        # _ here is the extension name, as required by Stevedore map(). Each
        # annotation already has the extension name so we can ignore it here
        for _, annotations in results:
            if annotations is None:
                continue

            # TODO: The file_path should be the same for all of these results
            # so we should be able to optimize getting file_path and making
            # sure it exists in the dict to do this less often.
            file_path = annotations[0]['filename']

            if file_path not in all_results:
                all_results[file_path] = []

            # TODO: add support for multiple extensions in the 'found_by' key
            # and de-dupe results
            all_results[file_path].extend(annotations)

    def search(self):
        """
        Walk the source tree, send known file types to extensions.

        Returns:
            Filename of the generated report
        """
        start_time = datetime.datetime.now()

        # Index the results by extension name
        file_extensions_map = {}
        known_extensions = set()
        for extension_name in self.config['extensions']:
            file_extensions_map[extension_name] = self.config['extensions'][extension_name]
            known_extensions.update(self.config['extensions'][extension_name])

        all_results = {}

        for root, _, files in os.walk(self.config['source_path']):
            for filename in files:
                filename_extension = os.path.splitext(filename)[1][1:]

                if filename_extension not in known_extensions:
                    self.echo.echo_vvv(
                        "{} is not a known extension, skipping ({}).".format(filename_extension, filename)
                    )
                    continue

                full_name = os.path.join(root, filename)

                self.echo.echo_vvv(full_name)

                # TODO: This should probably be a generator so we don't have to store all results in memory
                with open(full_name, 'r') as file_handle:
                    # Call search_extension on all loaded extensions
                    results = self.mgr.map(self.search_extension, file_handle, file_extensions_map, filename_extension)

                    # Format and add the results to our running full set
                    self.format_file_results(all_results, results)

        report_filename = self.report(all_results)
        done = datetime.datetime.now()
        elapsed = done - start_time

        self.echo.echo("Report completed in {}: {}".format(elapsed, report_filename))

    def report(self, all_results):
        """
        Genrates the YAML report of all search results.

        Args:
            all_results: Dict of found annotations, indexed by filename

        Returns:
            Filename of generated report
        """
        self.echo.echo_vv(yaml.dump(all_results, default_flow_style=False))

        now = datetime.datetime.now()
        report_filename = os.path.join(self.config['report_path'], '{}.yaml'.format(now.strftime('%Y-%d-%m-%H-%M-%S')))

        self.echo.echo("Generating report to {}".format(report_filename))

        try:
            os.makedirs(self.config['report_path'])
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        with open(report_filename, 'w+') as report_file:
            yaml.dump(all_results, report_file, default_flow_style=False)

        return report_filename
