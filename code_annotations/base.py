"""
Click command to do static annotation searching via Stevedore plugins.
"""
import datetime
import errno
import os
import re
from abc import ABCMeta, abstractmethod

import yaml
from stevedore import named

from code_annotations.exceptions import ConfigurationException
from code_annotations.helpers import VerboseEcho


class AnnotationConfig:
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
        self.optional_groups = []
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
        self.echo(f"Configured for report path: {self.report_path}")

        self.source_path = source_path_override if source_path_override else raw_config['source_path']
        self.echo(f"Configured for source path: {self.source_path}")

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
        return isinstance(token_or_group, dict) and "choices" in token_or_group

    def _is_optional_group(self, token_or_group):
        """
        Determine if an annotation is an optional group.

        Args:
            token_or_group: The annotation being checked

        Returns:
            True if the annotation is optional, otherwise False.
        """
        return isinstance(token_or_group, dict) and bool(token_or_group.get("optional"))

    def _is_annotation_token(self, token_or_group):
        """
        Determine if an annotation has the right format.

        Args:
            token_or_group: The annotation being checked

        Returns:
            True if the type of the annotation is correct for a text type, otherwise False
        """
        if token_or_group is None:
            return True
        if isinstance(token_or_group, dict):
            # If annotation is a dict, only a few keys are tolerated
            return set(token_or_group.keys()).issubset({"choices", "optional"})
        return False

    def _add_annotation_token(self, token):
        if token in self.annotation_tokens:
            raise ConfigurationException(f'{token} is configured more than once, tokens must be unique.')
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
            except (TypeError, ValueError) as error:
                raise ConfigurationException(
                    f'Coverage target must be a number between 0 and 100 not "{coverage_target}".'
                ) from error

            if self.coverage_target < 0.0 or self.coverage_target > 100.0:
                raise ConfigurationException(
                    f'Invalid coverage target. {self.coverage_target} is not between 0 and 100.'
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
            raise ConfigurationException(f'Group "{group_name}" must have more than one annotation.')

        for annotation in group:
            for annotation_token in annotation:
                annotation_value = annotation[annotation_token]

                # Otherwise it should be a text type, if not then error out
                if not self._is_annotation_token(annotation_value):
                    raise ConfigurationException(f'{annotation} is an unknown annotation type.')
                # The annotation comment is a choice group
                if self._is_choice_group(annotation_value):
                    self._configure_choices(annotation_token, annotation_value)
                # The annotation comment is not mandatory
                if self._is_optional_group(annotation_value):
                    self.optional_groups.append(annotation_token)

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
                    f'{annotation_token_or_group_name} is an unknown type, must be strings or lists.'
                )
            else:
                self._add_annotation_token(annotation_token_or_group_name)
                self.annotation_regexes.append(re.escape(annotation_token_or_group_name))

        self.echo.echo_v(f"Groups configured: {self.groups}")
        self.echo.echo_v(f"Choices configured: {self.choices}")
        self.echo.echo_v(f"Annotation tokens configured: {self.annotation_tokens}")

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


class BaseSearch(metaclass=ABCMeta):
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
                    self._add_annotation_error(annotation, f'"{choice}" is already present in this annotation.')
                else:
                    found_valid_choices.append(choice)
        else:
            self._add_annotation_error(
                annotation,
                'no value found for "{}". Expected one of {}.'.format(token, self.config.choices[token])
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
        self.echo.pprint(all_results, indent=3, verbosity_level=2)

        # Spin through the search results
        for filename in all_results:
            for annotations in self.iter_groups(all_results[filename]):
                self.check_group(annotations)
        return not self.errors

    def iter_groups(self, annotations):
        """
        Iterate on groups of annotations.

        Annotations are considered as a group when they all have the same `line_number`, which should point to the
        beginning of the annotation group.

        Yield:
            annotations (annotation list)
        """
        current_group = []
        current_line_number = None
        for annotation in annotations:
            line_number = annotation["line_number"]
            line_number_changed = line_number != current_line_number
            if line_number_changed:
                if current_group:
                    yield current_group
                current_group.clear()
            current_group.append(annotation)
            current_line_number = line_number

        if current_group:
            yield current_group

    def check_group(self, annotations):
        """
        Perform several linting checks on a group of annotations.

        The following checks are performed:

        - Choice fields should have a valid value
        - Annotation tokens are valid
        - There is no duplicate
        - All non-optional tokens are present
        """
        found_tokens = set()
        group_tokens = []
        group_name = None
        for annotation in annotations:
            token = annotation["annotation_token"]
            if not group_name:
                group_name = self._get_group_for_token(token)
                if group_name:
                    group_tokens = self.config.groups[group_name]

            # Check if choice field
            self._check_results_choices(annotation)

            # Check token belongs to group
            if group_name:
                if token not in group_tokens:
                    self._add_annotation_error(
                        annotation,
                        "'{}' token does not belong to group '{}'. Expected one of: {}".format(
                           token,
                           group_name,
                           group_tokens
                        )
                    )

            # Check for duplicates
            if token in found_tokens:
                self._add_annotation_error(
                    annotation,
                    "found duplicate token '{}'".format(token)
                )
            if group_name:
                found_tokens.add(token)

        # Check for missing tokens
        for token in group_tokens:
            if token not in self.config.optional_groups:
                if token not in found_tokens:
                    self._add_annotation_error(
                        annotations[0],
                        "missing non-optional annotation: '{}'".format(token)
                    )

    def check_annotation(self, annotation, current_group):
        """
        Check an annotation and add annotation errors when necessary.

        Args:
            annotation (dict): in particular, every annotation contains 'annotation_token' and 'annotation_data' keys.
            current_group (str): None or the name of a group (from self.config.groups) to which preceding annotations
                belong.
            found_group_tokens (list): annotation tokens from the same group that were already found. This list is
                cleared in case of error or when creating a new group.

        Return:
            current_group (str or None)
        """
        self._check_results_choices(annotation)
        token = annotation['annotation_token']

        if current_group:
            # Add to existing group
            if token not in self.config.groups[current_group]:
                # Check for token correctness
                self._add_annotation_error(
                    annotation,
                    '"{}" is not in the group that starts with "{}". Expecting one of: {}'.format(
                       token,
                       current_group,
                       self.config.groups[current_group]
                    )
                )
                current_group = None
            else:
                # Token is correct
                self.echo.echo_vv('Adding "{}", line {} to group {}'.format(
                    token,
                    annotation['line_number'],
                    current_group
                ))
        else:
            current_group = self._get_group_for_token(token)
            if current_group:
                # Start a new group
                self.echo.echo_vv('Starting new group for "{}" token "{}", line {}'.format(
                    current_group, token, annotation['line_number'])
                )

        return current_group

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
            self.echo.echo_vv(f"report_format: formatting {filename}")
            formatted_results[filename] = []
            current_group = None

            found_group_members = []

            for annotation in all_results[filename]:
                token = annotation['annotation_token']
                self.echo.echo_vvv(f"report_format: formatting annotation token {token}")

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
                        self.echo.echo_vv(f'Adding single token {token}.')
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

        self.echo(f"Generating report to {report_filename}")

        try:
            os.makedirs(self.config.report_path)
        except OSError as e:  # pragma: no cover
            if e.errno != errno.EEXIST:
                raise

        with open(report_filename, 'w+') as report_file:
            yaml.safe_dump(formatted_results, report_file, default_flow_style=False)

        return report_filename
