"""
Abstract and base classes to support plugins.
"""
import re
from abc import ABCMeta, abstractmethod

import six

from code_annotations.helpers import clean_abs_path, get_annotation_regex


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

    @abstractmethod
    def search(self, file_handle):  # pragma: no cover
        """
        Search for annotations in the given file.
        """
        raise NotImplementedError('search called on base class!')


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
    def __init__(self, config, echo):
        """
        Set up the extension and create the regexes used to do searches.

        Args:
            config: The configuration dict
            echo: VerboseEcho object for logging
        """
        super(SimpleRegexAnnotationExtension, self).__init__(config, echo)

        if self.lang_comment_definition is None:  # pragma: no cover
            raise ValueError('Subclasses of SimpleRegexAnnotationExtension must define lang_comment_definition!')

        # pylint: disable=not-a-mapping
        self.comment_regex = self.comment_regex_fmt.format(**self.lang_comment_definition)

        # Parent class will allow this class to populate self.strings_to_search via
        # calls to _add_annotation_token or _add_annotation_group for each configured
        # annotation.
        self.query = get_annotation_regex(self.config.annotation_regexes)

        self.ECHO.echo_v("{} extension regex query: {}".format(self.extension_name, self.query))

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
        if any(anno in txt for anno in self.config.annotation_tokens):
            fname = clean_abs_path(file_handle.name, self.config.source_path)

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
