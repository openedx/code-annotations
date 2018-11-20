"""
Helpers for code_annotations scripts.
"""
import os

import click


class VerboseEcho(object):
    """
    Helper to handle verbosity-dependent logging.
    """

    verbosity = 1

    def set_verbosity(self, verbosity):
        """
        Override the default verbosity level.

        Args:
            verbosity: The verbosity level to set to

        Returns:
            None
        """
        self.verbosity = verbosity

    def echo(self, output, verbosity_level=0):
        """
        Echo the given output, if over the verbosity threshold.

        Args:
            output: Text to output
            verbosity_level: Only output if our verbosity level is >= this.

        Returns:
            None
        """
        if verbosity_level <= self.verbosity:
            click.echo(output)

    def echo_v(self, output):
        """
        Echo the given output if verbosity level is >= 1.

        Args:
            output: Text to output

        Returns:
            None
        """
        self.echo(output, 1)

    def echo_vv(self, output):
        """
        Echo the given output if verbosity level is >= 2.

        Args:
            output: Text to output

        Returns:
            None
        """
        self.echo(output, 2)

    def echo_vvv(self, output):
        """
        Echo the given output if verbosity level is >= 3.

        Args:
            output: Text to output

        Returns:
            None
        """
        self.echo(output, 3)


def clean_abs_path(filename_to_clean, parent_path):
    """
    Safely strips the parent path from the given filename, leaving only the relative path.

    Args:
        filename_to_clean: Input filename
        parent_path: Path to remove from the input

    Returns:
        Updated path
    """
    return os.path.relpath(filename_to_clean, parent_path)
