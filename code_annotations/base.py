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

from code_annotations.exceptions import ConfigurationException
from code_annotations.helpers import VerboseEcho, read_configuration


@six.add_metaclass(ABCMeta)
class BaseSearch(object):
    """
    Base class for searchers.
    """

    def __init__(self, config, report_path, verbosity):
        """
        Initialize for StaticSearch.

        Args:
            config: Configuration file path
            report_path: Directory to write the report file to
            verbosity: Integer representing verbosity level (0-3)
        """
        self.config = {}
        self.errors = []
        self.groups = {}
        self.choices = {}

        # Global logger for this script, shared with extensions
        self.echo = VerboseEcho()
        self.configure(config, report_path, verbosity)

    def configure(self, config_file_path, report_path, verbosity):
        """
        Read the configuration file and handle command line overrides.

        Args:
            config_file_path: Location of the configuration file
            report_path: Directory where the report will be generated
            verbosity: Integer indicating the runtime verbosity level

        Returns:
            Configuration dict, updated with overrides
        """
        # TODO: Add include / exclude directories
        self.echo('Reading configuration from {}'.format(config_file_path))

        self.config = read_configuration(config_file_path)

        if 'report_path' not in self.config and not report_path:
            raise ConfigurationException('report_path not given and not in configuration file')

        if report_path:
            self.config['report_path'] = report_path

        self.config['verbosity'] = verbosity
        self.echo.set_verbosity(verbosity)

        self.configure_groups_and_choices()

        self.echo.echo_v("Verbosity level set to {}".format(verbosity))
        self.echo.echo_v("Configuration:")
        self.echo.echo_v(self.config)
        self.echo("Configured for report path: {}".format(self.config['report_path']))

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
        # Not a choice type of annotation, nothing to do
        if annotation['annotation_token'] not in self.choices:
            return

        token = annotation['annotation_token']
        found_valid_choices = []

        # If the line begins with an annotation token that should have choices, but has no text after the token,
        # the first split will be empty.
        if annotation['annotation_data'][0] != "":
            for choice in annotation['annotation_data']:
                if choice not in self.choices[token]:
                    self._add_annotation_error(
                        annotation,
                        '"{}" is not a valid choice for "{}". Expected one of {}.'.format(
                            choice,
                            token,
                            self.choices[token]
                        )
                    )
                elif choice in found_valid_choices:
                    self._add_annotation_error(
                        annotation,
                        '"{}" is already present in this annotation.'.format(
                            choice,
                        )
                    )
                else:
                    found_valid_choices.append(choice)
        else:
            self._add_annotation_error(
                annotation,
                'No choices found for "{}". Expected one of {}.'.format(
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
                            '"{}" is not in the group that starts with "{}". Expecting one of: {}'.format(
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

                        # If we have all members, this group is done
                        if len(found_group_members) == len(self.groups[current_group]):
                            self.echo.echo_vv("Group complete!")
                            current_group = None
                            found_group_members = []
                else:
                    if token in self.groups:
                        self.echo.echo_vv('Starting new group for "{}" line {}'.format(
                            token, annotation['line_number'])
                        )
                        current_group = token
                        found_group_members = []
                    else:
                        if token in group_children:
                            self._add_annotation_error(
                                annotation,
                                '"{}" is a member of a group, but no group is started!'.format(
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
