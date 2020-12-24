"""
Abstract and base classes to support plugins.
"""
import re
from abc import ABCMeta, abstractmethod

from code_annotations.helpers import clean_abs_path, clean_annotation, get_annotation_regex


class AnnotationExtension(metaclass=ABCMeta):
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


class SimpleRegexAnnotationExtension(AnnotationExtension, metaclass=ABCMeta):
    """
    Abstract base class for languages that have comments which can be reasonably searched using regular expressions.
    """

    # These are the language-specific comment definitions that are defined in the child classes. See the
    # Javascript and Python extensions for examples.
    lang_comment_definition = None

    # This format string/regex finds all comments in the file. The format tokens will be replaced with the
    # language-specific comment definitions defined in the sub-classes.
    #
    # Match groupdict will contain two named subgroups: 'comment' and 'prefixed_comment', of which at most
    # one will be non-None.
    comment_regex_fmt = r"""
        {multi_start}           # start of the language-specific multi-line comment (ex. /*)
        (?P<comment>            # Look for a multiline comment
            [\d\D]*?            # capture all of the characters...
        )
        {multi_end}             # until you find the end of the language-specific multi-line comment (ex. */)
        |                       # If you don't find any of those...
        (?P<prefixed_comment>   # Look for a group of single-line comments
            (?:                 # Non-capture mode
                {single}        # start by finding the single-line comment token (ex. //)
                .*              # and capture all characters until the end of the line
                \n?             # followed by an optional carriage return
                \ *             # and some empty space
            )*                  # multiple times
        )
    """

    def __init__(self, config, echo):
        """
        Set up the extension and create the regexes used to do searches.

        Args:
            config: The configuration dict
            echo: VerboseEcho object for logging
        """
        super().__init__(config, echo)

        if self.lang_comment_definition is None:  # pragma: no cover
            raise ValueError('Subclasses of SimpleRegexAnnotationExtension must define lang_comment_definition!')

        self.comment_regex = re.compile(
            self.comment_regex_fmt.format(**self.lang_comment_definition),
            flags=re.VERBOSE
        )
        self.prefixed_comment_regex = re.compile(
            r"^ *{single}".format(**self.lang_comment_definition),
            flags=re.MULTILINE
        )

        # Parent class will allow this class to populate self.strings_to_search via
        # calls to _add_annotation_token or _add_annotation_group for each configured
        # annotation.
        self.query = get_annotation_regex(self.config.annotation_regexes)

        self.ECHO.echo_v(f"{self.extension_name} extension regex query: {self.query.pattern}")

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

            # Iterate on all comments: both prefixed- and non-prefixed.
            for match in self.comment_regex.finditer(txt):
                # Get the line number by counting newlines + 1 (for the first line).
                # Note that this is the line number of the beginning of the comment, not the
                # annotation token itself.
                line = txt.count('\n', 0, match.start()) + 1

                comment_content = self._find_comment_content(match)
                for inner_match in self.query.finditer(comment_content):
                    try:
                        annotation_token = inner_match.group('token')
                        annotation_data = inner_match.group('data')
                    except IndexError as error:
                        # pragma: no cover
                        raise ValueError('{}::{}: Could not find "data" or "token" groups. Found: {}'.format(
                            fname,
                            line,
                            inner_match.groupdict()
                        )) from error
                    annotation_token, annotation_data = clean_annotation(annotation_token, annotation_data)
                    found_annotations.append({
                        'found_by': self.extension_name,
                        'filename': fname,
                        'line_number': line,
                        'annotation_token': annotation_token,
                        'annotation_data': annotation_data,
                    })

        return found_annotations

    def _find_comment_content(self, match):
        """
        Return the comment content as text.

        Args:
            match (sre.SRE_MATCH): one of the matches of the self.comment_regex regular expression.
        """
        comment_content = match.groupdict()["comment"]
        if comment_content:
            return comment_content

        # Find single-line comments and strip comment tokens
        comment_content = match.groupdict()["prefixed_comment"]
        return self._strip_single_line_comment_tokens(comment_content)

    def _strip_single_line_comment_tokens(self, content):
        """
        Strip the leading single-line comment tokens from a comment text.

        Args:
            content (str): token-prefixed multi-line comment string.
        """
        return self.prefixed_comment_regex.sub("", content)
