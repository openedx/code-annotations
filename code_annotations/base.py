"""
Click command to do static annotation searching via Stevedore plugins.
"""
import datetime
import errno
import os
import pprint
import re
from abc import ABCMeta, abstractmethod

import yaml
from stevedore import named

from code_annotations.exceptions import ConfigurationException
from code_annotations.helpers import VerboseEcho


class AnnotationConfig(object):
    """
    Configuration shared among all Code Annotations commands.
    """

    def __init__(self, config_file_path, report_path_override=None, verbosity=1, source_path_override=None):
        """
         Initialize AnnotationConfig.

        Args:
            config_file_path: Path to the configuration file
            report_path_override: Path to write reports to, if overridden on the command line
            verbosity: Verbosity level from the command line
            source_path_override: Path to search if we're static code searching, if overridden on the command line
        """
        self.groups = {}
        self.choices = {}
        self.annotation_tokens = []
        self.annotation_regexes = []
        self.mgr = None

        # Global logger, other objects can hold handles to this
        self.echo = VerboseEcho()

        with open(config_file_path) as config_file:
            raw_config = yaml.safe_load(config_file)

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
        self.report_template_dir = raw_config.get('report_template_dir')
        self.rendered_report_dir = raw_config.get('rendered_report_dir')
        self.rendered_report_file_extension = raw_config.get('rendered_report_file_extension')
        self.rendered_report_source_link_prefix = raw_config.get('rendered_report_source_link_prefix')

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

    def _is_choice_group(self, token_or_group):
        """
        Determine if an annotation is a choice group.

        Args:
            token_or_group: The annotation being checked

        Returns:
            True if the type of the annotation is correct for a choice group, otherwise False
        """
        return isinstance(token_or_group, dict)

    def _is_annotation_token(self, token_or_group):
        """
        Determine if an annotation is a free-form text type.

        Args:
            token_or_group: The annotation being checked

        Returns:
            True if the type of the annotation is correct for a text type, otherwise False
        """
        return token_or_group is None

    def _add_annotation_token(self, token):
        if token in self.annotation_tokens:
            raise ConfigurationException('{} is configured more than once, tokens must be unique.'.format(token))
        self.annotation_tokens.append(token)

    def _configure_coverage(self, coverage_target):
        """
        Set coverage_target to the specified value.

        Args:
            coverage_target:

        Returns:

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

        if not group or len(group) == 1:
            raise ConfigurationException('Group "{}" must have more than one annotation.'.format(group_name))

        for annotation in group:
            for annotation_token in annotation:
                annotation_value = annotation[annotation_token]

                # The annotation comment is a choice group
                if self._is_choice_group(annotation_value):
                    self._configure_choices(annotation_token, annotation_value)

                # Otherwise it should be a text type, if not then error out
                elif not self._is_annotation_token(annotation_value):
                    raise ConfigurationException('{} is an unknown annotation type.'.format(annotation))

                self.groups[group_name].append(annotation_token)
                self._add_annotation_token(annotation_token)
                self.annotation_regexes.append(re.escape(annotation_token))

    def _configure_choices(self, annotation_token, annotation):
        """
        Configure the choices list for an annotation.

        Args:
            annotation_token: The annotation token we are setting choices for
            annotation: The annotation body (list of choices)
        """
        self.choices[annotation_token] = annotation['choices']

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

            elif self._is_choice_group(annotation):
                self._configure_choices(annotation_token_or_group_name, annotation)
                self._add_annotation_token(annotation_token_or_group_name)
                self.annotation_regexes.append(re.escape(annotation_token_or_group_name))

            elif not self._is_annotation_token(annotation):  # pragma: no cover
                raise TypeError(
                    '{} is an unknown type, must be strings or lists.'.format(annotation_token_or_group_name)
                )
            else:
                self._add_annotation_token(annotation_token_or_group_name)
                self.annotation_regexes.append(re.escape(annotation_token_or_group_name))

        self.echo.echo_v("Groups configured: {}".format(self.groups))
        self.echo.echo_v("Choices configured: {}".format(self.choices))
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


class BaseSearch(object, metaclass=ABCMeta):
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

            for annotation in annotations:
                # If this is a "choices" type of annotation, split the comment into a list.
                # Actually checking the choice validity happens later in _check_results_choices.
                if annotation['annotation_token'] in self.config.choices:
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
        # Not a choice type of annotation, nothing to do
        if annotation['annotation_token'] not in self.config.choices:
            return None

        token = annotation['annotation_token']
        found_valid_choices = []

        # If the line begins with an annotation token that should have choices, but has no text after the token,
        # the first split will be empty.
        if annotation['annotation_data'][0] != "":
            for choice in annotation['annotation_data']:
                if choice not in self.config.choices[token]:
                    self._add_annotation_error(
                        annotation,
                        '"{}" is not a valid choice for "{}". Expected one of {}.'.format(
                            choice,
                            token,
                            self.config.choices[token]
                        )
                    )
                elif choice in found_valid_choices:
                    self._add_annotation_error(annotation, '"{}" is already present in this annotation.'.format(choice))
                else:
                    found_valid_choices.append(choice)
        else:
            self._add_annotation_error(
                annotation,
                'No choices found for "{}". Expected one of {}.'.format(token, self.config.choices[token])
            )
        return None

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
        return None

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
                self._check_results_choices(annotation)
                token = annotation['annotation_token']

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

                        if not current_group:  # pragma: no cover
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

        return not self.errors

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

    def report(self, all_results, report_prefix=''):
        """
        Genrates the YAML report of all search results.

        Args:
            all_results: Dict of found annotations, indexed by filename
            report_prefix: Prefix to add to report filename

        Returns:
            Filename of generated report
        """
        self.echo.echo_vv(yaml.dump(all_results, default_flow_style=False))

        now = datetime.datetime.now()
        report_filename = os.path.join(self.config.report_path, '{}{}.yaml'.format(
            report_prefix, now.strftime('%Y-%d-%m-%H-%M-%S')
        ))

        formatted_results = self._format_results_for_report(all_results)

        self.echo("Generating report to {}".format(report_filename))

        try:
            os.makedirs(self.config.report_path)
        except OSError as e:  # pragma: no cover
            if e.errno != errno.EEXIST:
                raise

        with open(report_filename, 'w+') as report_file:
            yaml.safe_dump(formatted_results, report_file, default_flow_style=False)

        return report_filename
