"""
Helpers for code_annotations scripts.
"""
import os
import re
import sys
from io import StringIO
from pprint import pprint

import click


def fail(msg):
    """
    Log the message and exit.

    Args:
        msg: Message to log
    """
    click.secho(msg, fg="red")
    sys.exit(1)


class VerboseEcho:
    """
    Helper to handle verbosity-dependent logging.
    """

    verbosity = 1

    def __call__(self, output, **kwargs):
        """
        Echo the given output regardless of verbosity level.

        This is just a convenience method to avoid lots of `self.echo.echo()`.

        Args:
            output: Text to output
            kwargs: Any additional keyword args to pass to click.echo
        """
        self.echo(output, **kwargs)

    def set_verbosity(self, verbosity):
        """
        Override the default verbosity level.

        Args:
            verbosity: The verbosity level to set to
            kwargs: Any additional keyword args to pass to click.echo
        """
        self.verbosity = verbosity
        self.echo_v(f"Verbosity level set to {verbosity}")

    def echo(self, output, verbosity_level=0, **kwargs):
        """
        Echo the given output, if over the verbosity threshold.

        Args:
            output: Text to output
            verbosity_level: Only output if our verbosity level is >= this.
            kwargs: Any additional keyword args to pass to click.echo
        """
        if verbosity_level <= self.verbosity:
            click.secho(output, **kwargs)

    def echo_v(self, output, **kwargs):
        """
        Echo the given output if verbosity level is >= 1.

        Args:
            output: Text to output
            kwargs: Any additional keyword args to pass to click.echo
        """
        self.echo(output, 1, **kwargs)

    def echo_vv(self, output, **kwargs):
        """
        Echo the given output if verbosity level is >= 2.

        Args:
            output: Text to output
            kwargs: Any additional keyword args to pass to click.echo
        """
        self.echo(output, 2, **kwargs)

    def echo_vvv(self, output, **kwargs):
        """
        Echo the given output if verbosity level is >= 3.

        Args:
            output: Text to output
            kwargs: Any additional keyword args to pass to click.echo
        """
        self.echo(output, 3, **kwargs)

    def pprint(self, data, indent=4, verbosity_level=0):
        """
        Pretty-print some data with the given verbosity level.
        """
        formatted = StringIO()
        pprint(data, indent=indent, stream=formatted)
        formatted.seek(0)
        self.echo(formatted.read(), verbosity_level=verbosity_level)


def clean_abs_path(filename_to_clean, parent_path):
    """
    Safely strips the parent path from the given filename, leaving only the relative path.

    Args:
        filename_to_clean: Input filename
        parent_path: Path to remove from the input

    Returns:
        Updated path
    """
    # If we are operating on only one file we don't know what to strip off here,
    # just return the whole thing.
    if filename_to_clean == parent_path:
        return os.path.basename(filename_to_clean)
    return os.path.relpath(filename_to_clean, parent_path)


def get_annotation_regex(annotation_regexes):
    """
    Return the full regex to search inside comments for configured annotations.

    A successful match against the regex will return two groups of interest: 'token'
    and 'data'.

    This regular expression supports annotation tokens that span multiple lines. To do
    so, prefix each line after the first by at least two leading spaces. E.g:

        .. pii: First line
          second line

    Unfortunately, the indenting spaces will find their way to the content of the "token" group.

    Args:
        annotation_regexes: List of re.escaped annotation tokens to search for.

    Returns:
        Regex ready for searching comments for annotations.
    """
    annotation_regex = r"""
    (?P<space>[\ \t]*)               # Leading empty spaces
    (?P<token>{tokens})              # Python format string that will be replaced with a
                                     # regex, escaped and then or-joined to make a list
                                     # of the annotation tokens we're looking for
                                     # Ex: (\.\.\ pii\:\:|\.\.\ pii\_types\:\:)
    (?P<data>                        # Captured annotation data
        (?:                          # non-capture mode
            .                        # any non-newline character
            |                        # or new line of multi-line annotation data
            (?:                      # non-capture mode
                \n{{1,}}             # at least one newline,
                (?P=space)           # followed by as much space as the prefix,
                (?P<indent>\ {{2,}}) # at least two spaces,
                (?=[^\ ])            # and a non-space character (look-ahead)
                (?!{tokens})         # that does not match any of the token regexes
            )                        #
        )*                           # any number of times
    )
    """
    annotation_regex = annotation_regex.format(tokens='|'.join(annotation_regexes))
    return re.compile(annotation_regex, flags=re.VERBOSE)


def clean_annotation(token, data):
    """
    Clean annotation token and data by stripping all trailing/prefix empty spaces.

    Args:
        token (str)
        data (str)

    Returns:
        (str, str): Tuple of cleaned token, data
    """
    token = token.strip()
    data = data.strip()
    return token, data
