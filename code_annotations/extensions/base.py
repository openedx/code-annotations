"""
Abstract and base classes to support plugins.
"""
import re
from abc import ABCMeta, abstractmethod

import six

from code_annotations.helpers import clean_abs_path


@six.add_metaclass(ABCMeta)
class AnnotationExtension(object):
    """
    Abstract base class that annotation extensions will inherit from.
    """

    extension_name = None

    def __init__(self, config, echo):
        """
        Initialize this base object, save a handle to configuration.

        Args:
            config: The configuration object
            echo: VerboseEcho object used for logging
        """
        self.config = config
        self.ECHO = echo

        annotation_tokens = config['annotations']

        # Allow sub-classes to configure themselves with the configured annotations
        for annotation_or_group in annotation_tokens:
            if isinstance(annotation_tokens[annotation_or_group], six.string_types):
                self._add_annotation_token(annotation_tokens[annotation_or_group])
            elif isinstance(annotation_tokens[annotation_or_group], (list, tuple)):
                self._add_annotation_group(annotation_tokens[annotation_or_group])
            elif isinstance(annotation_tokens[annotation_or_group], dict):
                self._add_annotation_token(next(iter(annotation_tokens[annotation_or_group])))
            else:
                raise TypeError('{} is an unknown type. Annotations must be strings, list/tuples, or dicts.'.format(
                    annotation_tokens[annotation_or_group])
                )

    @abstractmethod
    def search(self, file_handle):  # pragma: no cover
        """
        Search for annotations in the given file.
        """
        raise NotImplementedError('search called on base class!')

    @abstractmethod
    def _add_annotation_token(self, annotation):  # pragma: no cover
        """
        During initialization this method will be called for each configured annotation.

        Subclasses should use this to perform any necessary setup, such as creating regexes.

        Args:
            annotation: The string annotation to be searched for

        Returns:
            None
        """
        raise NotImplementedError('_add_annotation_token called on base class!')

    @abstractmethod
    def _add_annotation_group(self, annotation_group):  # pragma: no cover
        """
        During initialization this method will be called for each configured annotation group.

        Subclasses should use this to perform any necessary setup, such as creating regexes.

        Args:
            annotation_group: The list of annotations in the group to be searched for.

        Returns:
            None
        """
        raise NotImplementedError('_add_annotation_group called on base class!')


@six.add_metaclass(ABCMeta)
class SimpleRegexAnnotationExtension(AnnotationExtension):
    """
    Abstract base class for languages that have comments which can be reasonably searched using regular expressions.
    """

    # These are the language-specific comment definitions that are defined in the child classes. See the
    # Javascript and Python extensions for examples.
    lang_comment_definition = None

    r"""
    This format string/regex finds all comments in the file. The format tokens will be replaced with the
    language-specific comment definitions defined in the sub-classes.

    {multi_start} - start of the language-specific multi-line comment (ex. /*)
    ([\d\D]*?)    - capture all of the characters...
    {multi_end}   - until you find the end of the language-specific multi-line comment (ex. */)
    |             - If you don't find any of those...
    {single}      - start by finding the single-line comment token (ex. //)
    (.*)          - and capture all characters until the end of the line

    Returns a 2-tuple of:
     - ("Comment text", None) in the case of a multi-line comment OR
     - (None, "Comment text") in the case of a single-line comment

    TODO: Make this handle multi-line annotation comments again.
    """
    comment_regex_fmt = r'{multi_start}([\d\D]*?){multi_end}|{single}(.*)'

    r"""
    This format string/regex finds our annotation token and choices / comments inside a comment:

    [\s\S]*? - Strip out any characters between the start of the comment and the annotation
    ({})     - {} is a Python format string that will be replaced with a regex escaped and
               then or-joined to make a list of the annotation tokens we're looking for
               Ex: (\.\.\ pii\:\:|\.\.\ pii\_types\:\:)
    (.*)     - and capture all characters until the end of the line

    Returns a 2-tuple of found annotation token and annotation comment

    TODO: Make multi line annotation comments work again.
    """
    annotation_regex = r'[\s\S]*?({})(.*)'

    def __init__(self, config, echo):
        """
        Set up the extension and create the regexes used to do searches.

        Args:
            config: The configuration dict
            echo: VerboseEcho object for logging
        """
        # These must be set before the parent config is called since callbacks happen
        # on parent __init__ to _add_annotation_token / _add_annotation_group.
        self.annotation_tokens = []
        self.annotation_regexes = []

        super(SimpleRegexAnnotationExtension, self).__init__(config, echo)

        if self.lang_comment_definition is None:  # pragma: no cover
            raise ValueError('Subclasses of SimpleRegexAnnotationExtension must define lang_comment_definition!')

        # pylint: disable=not-a-mapping
        self.comment_regex = self.comment_regex_fmt.format(**self.lang_comment_definition)

        # Parent class will allow this class to populate self.strings_to_search via
        # calls to _add_annotation_token or _add_annotation_group for each configured
        # annotation.
        self.query = self.annotation_regex.format('|'.join(self.annotation_regexes))

        self.ECHO.echo_v("{} extension regex query: {}".format(self.extension_name, self.query))

    def _add_annotation_token(self, annotation):
        """
        Add annotations to our local lists during configuration.

        Args:
            annotation: An annotation token (ex. ".. pii::")

        Raises:
            TypeError
        """
        self.annotation_tokens.append(annotation)
        self.annotation_regexes.append(re.escape(annotation))

    def _add_annotation_group(self, annotation_group):
        """
        Add an annotation group to our local lists during configuration.

        Args:
            annotation_group: An annotation group from the configuration file.

        Raises:
            TypeError
        """
        for annotation in annotation_group:
            if isinstance(annotation, six.string_types):
                self._add_annotation_token(annotation)
            elif isinstance(annotation, dict):
                annotation_name = next(iter(annotation))
                self._add_annotation_token(annotation_name)
            else:
                raise TypeError(
                    '{} is an unknown type. Annotation groups must be strings or dicts.'.format(annotation_group)
                )

    def search(self, file_handle):
        """
        Search for annotations in the given file.

        Args:
            file_handle: Handle for the file to validate

        Returns:
            List of dicts describing found annotations, or an empty list
        """
        txt = file_handle.read()

        found_annotations = []

        # Fast out if no annotations exist in the file
        if any(anno in txt for anno in self.annotation_tokens):
            fname = clean_abs_path(file_handle.name, self.config['source_path'])

            for match in re.finditer(self.comment_regex, txt):
                # Should only be one match
                comment_content = [item for item in match.groups() if item is not None][0]
                for inner_match in re.finditer(self.query, comment_content):
                    # Get the line number by counting newlines + 1 (for the first line).
                    # Note that this is the line number of the beginning of the comment, not the
                    # annotation token itself.
                    line = txt.count('\n', 0, match.start()) + 1

                    # No matter how long the regex is, there should only be 2 non-None items,
                    # with the first being the annotation token and the 2nd being the comment.
                    cleaned_groups = [item for item in inner_match.groups() if item is not None]

                    if len(cleaned_groups) != 2:  # pragma: no cover
                        raise Exception('{}::{}: Number of found items in the list is not 2. Found: {}'.format(
                            fname,
                            line,
                            cleaned_groups
                        ))

                    annotation, comment = cleaned_groups

                    found_annotations.append({
                        'found_by': self.extension_name,
                        'filename': fname,
                        'line_number': line,
                        'annotation_token': annotation.strip(),
                        'annotation_data': comment.strip()
                    })

        return found_annotations
