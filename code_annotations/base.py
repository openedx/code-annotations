"""
Click command to do static annotation searching via Stevedore plugins.
"""
import datetime
import errno
import os
import pprint
import re
from abc import ABCMeta, abstractmethod

import six
import yaml
from stevedore import named

from code_annotations.exceptions import ConfigurationException
from code_annotations.helpers import VerboseEcho


@six.add_metaclass(ABCMeta)
class BaseAnnotation(object):
    """
    Annotations defined in configuration.
    """

    def __init__(self, annotation_token, annotation_definition):
        """
        Initialize Annotation.

        Args:
            annotation_definition: The Python representation of the annotation from config
        """
        self.token = annotation_token
        self.annotation_type = annotation_definition['type']
        self.required = annotation_definition.get('required', False)

    @abstractmethod
    def format_annotation_data(self, data):
        """
        Take a found annotation's data and format it based on the annotation type. Defined in child classes.

        Args:
            data: The found annotation's data

        Returns:
            The formatted data, defined by the Annotation's type

        Raises:
            TypeError if the data will not format correctly
        """
        pass  # pragma: no cover


class IntAnnotation(BaseAnnotation):
    """
    An annotation that enforces integer typing.
    """

    def format_annotation_data(self, data):
        """
        Format the string input from a found annotation into the expected type for this annotation.

        Args:
            data: String of found annotation data

        Returns:
            data converted to an integer
        """
        return int(data)


class FloatAnnotation(BaseAnnotation):
    """
    An annotation that enforces float typing.
    """

    def format_annotation_data(self, data):
        """
        Format the string input from a found annotation into the expected type for this annotation.

        Args:
            data: String of found annotation data

        Returns:
            data converted to a float
        """
        return float(data)


class StringAnnotation(BaseAnnotation):
    """
    An annotation that enforces string typing.
    """

    def format_annotation_data(self, data):
        """
        Format the string input from a found annotation into the expected type for this annotation.

        Args:
            data: String of found annotation data

        Returns:
            data converted to a string appropriate for this version of Python
        """
        return six.text_type(data)


class ChoiceAnnotation(BaseAnnotation):
    """
    An annotation that allows only one choice from the configured list.
    """

    def __init__(self, annotation_token, annotation_definition):
        """
        Initialize ChoiceAnnotation.

        Args:
            annotation_token: The annotation token that identifies this annotation type
            annotation_definition: The Python representation of the annotation from config
        """
        super(ChoiceAnnotation, self).__init__(annotation_token, annotation_definition)

        # Everything we have is coming in as strings, so make sure they are correct for comparison later
        self.choices = [six.text_type(choice) for choice in annotation_definition['choices']]

    def format_annotation_data(self, data):
        """
        Format the string input from a found annotation into the expected type for this annotation.

        Args:
            data: String of found annotation data

        Returns:
            The single choice, if valid

        Raises:
            ValueError if the choice isn't in the configured list
        """
        if not data or data not in self.choices:
            raise ValueError('"{}" is not a valid choice for "{}". Expected one of: {}'.format(
                data,
                self.token,
                self.choices
            ))
        return data


class MultiChoiceAnnotation(ChoiceAnnotation):
    """
    An annotation that allows multiple choices from the configured list.
    """

    def format_annotation_data(self, data):
        """
        Format the string input from a found annotation into the expected type for this annotation.

        Args:
            data: String of found annotation data

        Returns:
            The list of choice, if all choices are valid

        Raises:
            ValueError if any choice isn't in the configured list, or if the same choice appears more than once
        """
        if not data:
            raise ValueError('No choices found for "{}". Expected one of: {}'.format(
                self.token,
                self.choices
            ))

        choices = re.split(r',\s?|\s', data)
        found_choices = []
        for choice in choices:
            if choice not in self.choices:
                raise ValueError('"{}" is not a valid choice for "{}". Expected one of: {}'.format(
                    choice,
                    self.token,
                    self.choices
                ))
            if choice in found_choices:
                raise ValueError('"{}" is already present in this annotation'.format(choice))
            found_choices.append(choice)

        return choices


class AnnotationConfig(object):
    """
    Configuration shared among all Code Annotations commands.
    """

    def __init__(self, config_file_path, report_path_override, verbosity, source_path_override=None):
        """
         Initialize AnnotationConfig.

        Args:
            config_file_path: Path to the configuration file
            report_path_override: Path to write reports to, if overridden on the command line
            verbosity: Verbosity level from the command line
            source_path_override: Path to search if we're static code searching, if overridden on the command line
        """
        self.groups = {}
        self.annotation_tokens = {}
        self.annotation_regexes = []
        self.mgr = None

        # Global logger, other objects can hold handles to this
        self.echo = VerboseEcho()

        with open(config_file_path) as config_file:
            raw_config = yaml.load(config_file)

        self._check_raw_config_keys(raw_config)

        self.safelist_path = raw_config['safelist_path']
        self.extensions = raw_config['extensions']

        self.verbosity = verbosity
        self.echo.set_verbosity(verbosity)

        self.report_path = report_path_override if report_path_override else raw_config['report_path']
        self.echo("Configured for report path: {}".format(self.report_path))

        self.source_path = source_path_override if source_path_override else raw_config['source_path']
        self.echo("Configured for source path: {}".format(self.source_path))

        self._configure_coverage(raw_config.get('coverage_target', None))
        self._configure_annotations(raw_config)
        self._configure_extensions()

    def _check_raw_config_keys(self, raw_config):
        """
        Validate that all required keys exist in the configuration file.

        Args:
            raw_config: Python representation of the YAML config file

        Raises:
            ConfigurationException on any missing keys
        """
        errors = []
        for k in ('report_path', 'source_path', 'safelist_path', 'annotations', 'extensions'):
            if k not in raw_config:
                errors.append(k)

        if errors:
            raise ConfigurationException(
                'The following required keys are missing from the configuration file: \n{}'.format(
                    '\n'.join(errors)
                )
            )

    def _is_annotation_group(self, token_or_group):
        """
        Determine if an annotation is a group or not.

        Args:
            token_or_group: The annotation being checked

        Returns:
            True if the type of the annotation is correct for a group, otherwise False
        """
        return isinstance(token_or_group, list)

    def _configure_coverage(self, coverage_target):
        """
        Perform coverage setup based on the global configuration.

        Args:
            coverage_target:
        """
        if coverage_target:
            try:
                self.coverage_target = float(coverage_target)
            except (TypeError, ValueError):
                raise ConfigurationException(
                    'Coverage target must be a number between 0 and 100 not "{}".'.format(coverage_target)
                )

            if self.coverage_target < 0.0 or self.coverage_target > 100.0:
                raise ConfigurationException(
                    'Invalid coverage target. {} is not between 0 and 100.'.format(self.coverage_target)
                )
        else:
            self.coverage_target = None

    def _configure_group(self, group_name, group):
        """
        Perform group configuration and add annotations from the group to global configuration.

        Args:
            group_name: The name of the group (the key in the configuration dictionary)
            group: The list of annotations that comprise the group

        Raises:
            TypeError if the group is misconfigured
        """
        self.groups[group_name] = []

        if not group:
            raise ConfigurationException('Group "{}" has no annotations.'.format(group_name))

        for annotation in group:
            for annotation_token in annotation:
                annotation_value = annotation[annotation_token]

                self.groups[group_name].append(annotation_token)
                self._add_configured_annotation(annotation_token, annotation_value)
                self.annotation_regexes.append(re.escape(annotation_token))

    def _create_annotation_from_config(self, annotation_token, annotation_config):
        """
        Create a typed object that inherits from BaseAnnotation and return it.

        Args:
            annotation_config: The Python representation of the annotation definition

        Returns:
            An object that inherits from BaseAnnotation, differing based on the passed in type
        """
        known_types = {
            'string': StringAnnotation,
            'int': IntAnnotation,
            'float': FloatAnnotation,
            'choice': ChoiceAnnotation,
            'multichoice': MultiChoiceAnnotation,
        }

        try:
            return known_types[annotation_config['type']](annotation_token, annotation_config)
        except (KeyError, TypeError):
            raise ConfigurationException("{} is an unknown annotation type.".format(annotation_config))

    def _add_configured_annotation(self, annotation_token, annotation_config):
        """
        Take an annotation from configuration and add it to self.annotation_tokens.

        Args:
            annotation_token: The token that identifies this annotation type
            annotation_config: The Python representation of the configured annotation

        Returns:

        """
        if annotation_token in self.annotation_tokens:
            raise ConfigurationException('{} is configured more than once, tokens must be unique.'.format(
                annotation_token
            ))

        self.annotation_tokens[annotation_token] = self._create_annotation_from_config(
            annotation_token,
            annotation_config
        )

    def _configure_annotations(self, raw_config):
        """
        Transform the configured annotations into more usable pieces and validate.

        Args:
            raw_config: The dictionary form of our configuration file
        Raises:
            TypeError if annotations are misconfigured
        """
        annotation_tokens = raw_config['annotations']

        for annotation_token_or_group_name in annotation_tokens:
            annotation = annotation_tokens[annotation_token_or_group_name]

            if self._is_annotation_group(annotation):
                self._configure_group(annotation_token_or_group_name, annotation)
            else:
                self._add_configured_annotation(annotation_token_or_group_name, annotation)
                self.annotation_regexes.append(re.escape(annotation_token_or_group_name))

        self.echo.echo_v("Groups configured: {}".format(self.groups))
        self.echo.echo_v("Annotation tokens configured: {}".format(self.annotation_tokens))

    def _plugin_load_failed_handler(self, *args, **kwargs):
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
        self.echo(str(args), fg='red')
        self.echo(str(kwargs), fg='red')
        raise ConfigurationException('Failed to load a plugin, aborting.')

    def _configure_extensions(self):
        """
        Configure the Stevedore NamedExtensionManager.

        Raises:
            ConfigurationException
        """
        # These are the names of all of our configured extensions
        configured_extension_names = self.extensions.keys()

        # Load Stevedore extensions that we are configured for (and only those)
        self.mgr = named.NamedExtensionManager(
            names=configured_extension_names,
            namespace='annotation_finder.searchers',
            invoke_on_load=True,
            on_load_failure_callback=self._plugin_load_failed_handler,
            invoke_args=(self, self.echo),
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


@six.add_metaclass(ABCMeta)
class BaseSearch(object):
    """
    Base class for searchers.
    """

    def __init__(self, config):
        """
        Initialize for StaticSearch.

        Args:
            config: Configuration object
        """
        self.config = config
        self.echo = self.config.echo
        self.errors = []

    def format_file_results(self, all_results, results):
        """
        Add all extensions' search results for a file to the overall results.

        Args:
            all_results: Aggregated results to add the results to
            results: Results of search() on a single file

        Returns:
            None, modifies all_results
        """
        for annotations in results:
            if not annotations:
                continue

            # TODO: The file_path should be the same for all of these results
            # so we should be able to optimize getting file_path and making
            # sure it exists in the dict to do this less often.
            file_path = annotations[0]['filename']

            if file_path not in all_results:  # pragma: no cover
                all_results[file_path] = []

            # TODO: De-dupe results? Should only be necessary if more than one
            # Stevedore extension is working on the same file type
            all_results[file_path].extend(annotations)

    def _get_group_children(self):
        """
        Create a list of all annotation tokens that are part of a group.

        Returns:
            List of annotation tokens that are configured to be in groups
        """
        group_children = []

        for group in self.config.groups:
            group_children.extend(self.config.groups[group])

        return group_children

    def _get_group_for_token(self, token):
        """
        Find out which group, if any, an annotation token belongs to.

        Args:
            token: Annotation token to search for

        Returns:
            The group name, or None if it doesn't belong to a group.
        """
        for group in self.config.groups:
            if token in self.config.groups[group]:
                return group

    def check_results(self, all_results):
        """
        Spin through all search results, confirm that they all match configuration.

        If errors are found they are added to self.errors.

        Args:
            all_results: Dict of annotations found in search()

        Returns:
            Boolean indicating whether or not any errors were found
        """
        if self.config.verbosity >= 2:
            pprint.pprint(all_results, indent=3)

        group_children = self._get_group_children()

        # Spin through the search results
        for filename in all_results:
            current_group = None
            found_group_members = []

            for annotation in all_results[filename]:
                token = annotation['annotation_token']

                try:
                    annotation['annotation_data'] = self.config.annotation_tokens[token].format_annotation_data(
                        annotation['annotation_data']
                    )
                except ValueError as exc:
                    self._add_annotation_error(annotation, six.text_type(exc))

                # TODO: Clean this up into reasonable methods
                if current_group:
                    if token not in self.config.groups[current_group]:
                        self._add_annotation_error(
                            annotation,
                            '"{}" is not in the group that starts with "{}". Expecting one of: {}'.format(
                               token,
                               current_group,
                               self.config.groups[current_group]
                            )
                        )
                        current_group = None
                        found_group_members = []
                    elif token in found_group_members:
                        self._add_annotation_error(
                            annotation,
                            '"{}" is already in the group that starts with "{}"'.format(token, current_group)
                        )
                        current_group = None
                        found_group_members = []
                    else:
                        self.echo.echo_vv('Adding "{}", line {} to group {}'.format(
                            token,
                            annotation['line_number'],
                            current_group
                        ))
                        found_group_members.append(token)
                else:
                    if token in group_children:
                        current_group = self._get_group_for_token(token)

                        if current_group is None:  # pragma: no cover
                            # If we get here there is a problem with check_results' group_children not matching up with
                            # our config's groups. That puts us in an unknown state, so we should quit.
                            raise Exception(
                                'group_children is out of sync with config.groups. {} is not in a group!'.format(token)
                            )

                        found_group_members = [token]
                        self.echo.echo_vv('Starting new group for "{}" token "{}", line {}'.format(
                            current_group, token, annotation['line_number'])
                        )

                # If we have all members, this group is done
                if current_group and len(found_group_members) == len(self.config.groups[current_group]):
                    self.echo.echo_vv("Group complete!")
                    current_group = None
                    found_group_members = []

            if current_group:
                self.errors.append('File finished with an incomplete group {}!'.format(current_group))

        return False if self.errors else True

    def _add_annotation_error(self, annotation, message):
        """
        Add an error message to self.errors, formatted nicely.

        Args:
            annotation: A single annotation dict found in search()
            message: Custom error message to be added
        """
        if 'extra' in annotation and 'object_id' in annotation['extra']:
            error = "{}::{}: {}".format(annotation['filename'], annotation['extra']['object_id'], message)
        else:
            error = "{}::{}: {}".format(annotation['filename'], annotation['line_number'], message)
        self.errors.append(error)

    def _add_error(self, message):
        """
        Add an error message to self.errors.

        Args:
            message: Custom error message to be added
        """
        self.errors.append(message)

    @abstractmethod
    def search(self):
        """
        Walk the source tree, send known file types to extensions.

        Returns:
            Dict of {filename: annotations} for all files with found annotations.
        """
        pass  # pragma: no cover

    def _format_results_for_report(self, all_results):
        """
        Format the given results dict for reporting purposes.

        Args:
            all_results: Dict of all results found in a search

        Returns:
            Dict of results arranged for reporting
        """
        group_children = self._get_group_children()
        formatted_results = {}
        current_group_id = 0

        for filename in all_results:
            self.echo.echo_vv("report_format: formatting {}".format(filename))
            formatted_results[filename] = []
            current_group = None

            found_group_members = []

            for annotation in all_results[filename]:
                token = annotation['annotation_token']
                self.echo.echo_vvv("report_format: formatting annotation token {}".format(token))

                if current_group:
                    if token not in self.config.groups[current_group]:
                        self.echo.echo_vv(
                            "report_format: {} is not a group member, finishing group id {}".format(
                                token,
                                current_group_id
                            )
                        )
                        current_group = None
                        found_group_members = []
                        formatted_results[filename].append(annotation)
                    else:
                        self.echo.echo_vv("report_format: Adding {} to group id {}".format(
                            token,
                            current_group_id
                        ))
                        annotation['report_group_id'] = current_group_id
                        formatted_results[filename].append(annotation)
                        found_group_members.append(token)
                else:
                    if token in group_children:
                        current_group = self._get_group_for_token(token)
                        current_group_id += 1
                        found_group_members = [token]
                        annotation['report_group_id'] = current_group_id
                        formatted_results[filename].append(annotation)

                        self.echo.echo_vv('Starting group id {} for "{}" token "{}", line {}'.format(
                            current_group_id, current_group, token, annotation['line_number'])
                        )
                    else:
                        self.echo.echo_vv('Adding single token {}.'.format(token))
                        formatted_results[filename].append(annotation)

                # If we have all members, this group is done
                if current_group and len(found_group_members) == len(self.config.groups[current_group]):
                    self.echo.echo_vv("report_format: Group complete!")
                    current_group = None
                    found_group_members = []

        return formatted_results

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
        report_filename = os.path.join(self.config.report_path, '{}.yaml'.format(now.strftime('%Y-%d-%m-%H-%M-%S')))

        formatted_results = self._format_results_for_report(all_results)

        self.echo("Generating report to {}".format(report_filename))

        try:
            os.makedirs(self.config.report_path)
        except OSError as e:  # pragma: no cover
            if e.errno != errno.EEXIST:
                raise

        with open(report_filename, 'w+') as report_file:
            yaml.dump(formatted_results, report_file, default_flow_style=False)

        return report_filename
