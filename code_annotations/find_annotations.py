"""
Click command to do static annotation searching via Stevedore plugins.
"""
import datetime
import errno
import os
import pprint
import re

import six
import yaml
from stevedore import named

from code_annotations.exceptions import ConfigurationException
from code_annotations.helpers import VerboseEcho, read_configuration


class StaticSearch(object):
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
        self.config = {}
        self.errors = []
        self.groups = {}
        self.choices = {}
        self.mgr = None

        # Global logger for this script, shared with extensions
        self.echo = VerboseEcho()
        self.configure(config, source_path, report_path, verbosity)

    def configure(self, config_file_path, source_path, report_path, verbosity):
        """
        Read the configuration file and handle command line overrides.

        Args:
            config_file_path: Location of the configuration file
            source_path: Path to the code to be searched
            report_path: Directory where the report will be generated
            verbosity: Integer indicating the runtime verbosity level

        Returns:
            Configuration dict, updated with overrides
        """
        # TODO: Add include / exclude directories
        self.echo('Reading configuration from {}'.format(config_file_path))

        self.config = read_configuration(config_file_path)

        if not source_path and 'source_path' not in self.config:
            raise ConfigurationException('source_path not given and not in configuration file')

        if not report_path and 'report_path' not in self.config:
            raise ConfigurationException('report_path not given and not in configuration file')

        if source_path:
            self.config['source_path'] = source_path

        if report_path:
            self.config['report_path'] = report_path

        self.config['verbosity'] = verbosity
        self.echo.set_verbosity(verbosity)

        self.configure_extensions()
        self.configure_groups_and_choices()

        self.echo.echo_v("Verbosity level set to {}".format(verbosity))
        self.echo.echo_v("Configuration:")
        self.echo.echo_v(self.config)
        self.echo(
            "Configured for source path: {}, report path: {}".format(
                self.config['source_path'],
                self.config['report_path'])
        )

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

    def configure_groups_and_choices(self):
        """
        Transform the configured annotations into more usable pieces and validate.

        TODO: Break this up into sane methods, de-dupe work done in extensions/base.py
        """
        annotation_tokens = self.config['annotations']

        for annotation_or_group in annotation_tokens:
            # If the token is one of these it's a group
            if isinstance(annotation_tokens[annotation_or_group], (list, tuple)):
                first = True
                for annotation in annotation_tokens[annotation_or_group]:
                    # The annotation comment is a simple string
                    if isinstance(annotation, six.string_types):
                        key = annotation
                    # The annotation comment is a choice group
                    elif isinstance(annotation, dict):
                        key = next(iter(annotation))
                        self.choices[key] = annotation[key]['choices']
                    else:  # pragma: no cover
                        raise TypeError(
                            '{} is an unknown type.'.format(annotation)
                        )

                    # We save off the first token from each comment group to use as a marker
                    # when finding new annotation groups.
                    if first:
                        current_group_key = key
                        self.groups[key] = []
                        first = False
                        continue

                    self.groups[current_group_key].append(key)
            # If it is a dict this is an annotation with a choice group
            elif isinstance(annotation_tokens[annotation_or_group], dict):
                token = next(iter(annotation_tokens[annotation_or_group]))
                self.choices[token] = annotation_tokens[annotation_or_group][token]['choices']
            # Otherwise it should be a simple string comment
            elif not isinstance(annotation_tokens[annotation_or_group], six.string_types):  # pragma: no cover
                # If not we don't know what to do with it
                raise TypeError(
                    '{} is an unknown type. Annotations must be strings or list/tuples.'.format(annotation_or_group)
                )

        self.echo.echo_v("Groups configured: {}".format(self.groups))
        self.echo.echo_v("Choices configured: {}".format(self.choices))

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

    def format_file_results(self, all_results, results):
        """
        Add all extensions' search results for a file to the overall results.

        Args:
            all_results: Aggregated results to add the results to
            results: Results of search() on a single file

        Returns:
            None, modifies all_results
        """
        # "_" here is the extension name, as required by Stevedore map(). Each
        # annotation already has the extension name so we can ignore it
        for _, annotations in results:
            if not annotations:
                continue

            # TODO: The file_path should be the same for all of these results
            # so we should be able to optimize getting file_path and making
            # sure it exists in the dict to do this less often.
            file_path = annotations[0]['filename']

            if file_path not in all_results:  # pragma: no cover
                all_results[file_path] = []

            for annotation in annotations:
                # If this is a "choices" type of annotation, split the comment into a list.
                # Actually checking the choice validity happens later in _check_results_choices.
                if annotation['annotation_token'] in self.choices:
                    annotation['annotation_data'] = re.split(r',\s?|\s', annotation['annotation_data'])

            # TODO: De-dupe results? Should only be necessary if more than one
            # Stevedore extension is working on the same file type
            all_results[file_path].extend(annotations)

    def _check_results_choices(self, annotation):
        """
        Check that a search result has appropriate choices.

        If the following errors are found:
            - no choices
            - multiple of the same choice
            - a choice which is not configured

        This function will add the error to self.errors.

        Args:
            annotation: A single search result dict.
        """
        if annotation['annotation_token'] not in self.choices:
            return

        token = annotation['annotation_token']
        found_valid_choices = []

        # If there are no choices on the line, split will return this
        if annotation['annotation_data'][0] != "":
            for choice in annotation['annotation_data']:
                if choice not in self.choices[token]:
                    self._add_annotation_error(
                        annotation,
                        '{} is not a valid choice for {}. Expected one of {}.'.format(
                            choice,
                            token,
                            self.choices[token]
                        )
                    )
                elif choice in found_valid_choices:
                    self._add_annotation_error(
                        annotation,
                        '{} is already present in this annotation.'.format(
                            choice,
                        )
                    )
                else:
                    found_valid_choices.append(choice)
        else:
            self._add_annotation_error(
                annotation,
                'No choices found for {}. Expected one of {}.'.format(
                    token,
                    self.choices[token]
                )
            )

    def check_results(self, all_results):
        """
        Spin through all search results, confirm that they all match configuration.

        If errors are found they are added to self.errors.

        Args:
            all_results: Dict of annotations found in search()
        """
        if self.config['verbosity'] >= 2:
            pprint.pprint(all_results, indent=3)

        # This is used to quickly find out if a token is a member of a group
        group_children = []

        # Build a big list of all tokens that are part of a group
        for group in self.groups:
            group_children.extend(self.groups[group])

        # Spin through the search results
        for filename in all_results:
            current_group = None
            found_group_members = []

            for annotation in all_results[filename]:
                self._check_results_choices(annotation)
                token = annotation['annotation_token']

                # TODO: Clean this up into reasonable methods
                if current_group:
                    if token not in self.groups[current_group]:
                        self._add_annotation_error(
                            annotation,
                            '{} is not in the group that starts with {}. Expecting one of: {}'.format(
                               token,
                               current_group,
                               self.groups[current_group]
                            )
                        )
                        current_group = None
                        found_group_members = []
                    elif token in found_group_members:
                        self._add_annotation_error(
                            annotation,
                            '{} is already in the group that starts with {}'.format(token, current_group)
                        )
                        current_group = None
                        found_group_members = []
                    else:
                        self.echo.echo_vv("Adding {}, line {} to group {}".format(
                            token,
                            annotation['line_number'],
                            current_group
                        ))
                        found_group_members.append(token)

                        # If we have all members, this group is done
                        if len(found_group_members) == len(self.groups[current_group]):
                            self.echo.echo_vv("Group complete!")
                            current_group = None
                            found_group_members = []
                else:
                    if token in self.groups:
                        self.echo.echo_vv("Starting new group for {} line {}".format(token, annotation['line_number']))
                        current_group = token
                        found_group_members = []
                    else:
                        if token in group_children:
                            self._add_annotation_error(
                                annotation,
                                '{} is a member of a group, but no group is not started!'.format(
                                    token
                                )
                            )

            if current_group:
                self.errors.append('File finished with an incomplete group {}!'.format(current_group))

    def _add_annotation_error(self, annotation, message):
        """
        Add an error message to self.errors, formatted nicely.

        Args:
            annotation: A single annotation dict found in search()
            message: Custom error message to be added
        """
        error = "{}::{}: {}".format(annotation['filename'], annotation['line_number'], message)
        self.errors.append(error)

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

            # Format and add the results to our running full set
            self.format_file_results(all_results, results)

    def search(self):
        """
        Walk the source tree, send known file types to extensions.

        Returns:
            Filename of the generated report
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

        self.echo("Generating report to {}".format(report_filename))

        try:
            os.makedirs(self.config['report_path'])
        except OSError as e:  # pragma: no cover
            if e.errno != errno.EEXIST:
                raise

        with open(report_filename, 'w+') as report_file:
            yaml.dump(all_results, report_file, default_flow_style=False)

        return report_filename
