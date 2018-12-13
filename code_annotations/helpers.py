"""
Helpers for code_annotations scripts.
"""
import os
import sys

import click
import yaml


def fail(msg):
    """
    Log the message and exit.
    """
    click.secho(msg, fg="red")
    sys.exit(-1)


class VerboseEcho(object):
    """
    Helper to handle verbosity-dependent logging.
    """

    verbosity = 1

    def __call__(self, output):
        """
        Echo the given output regardless of verbosity level.

        This is just a convenience method to avoid lots of `self.echo.echo()`.

        Args:
            output: Text to output
        """
        self.echo(output)

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
        """
        if verbosity_level <= self.verbosity:
            click.echo(output)

    def echo_v(self, output):
        """
        Echo the given output if verbosity level is >= 1.

        Args:
            output: Text to output
        """
        self.echo(output, 1)

    def echo_vv(self, output):
        """
        Echo the given output if verbosity level is >= 2.

        Args:
            output: Text to output
        """
        self.echo(output, 2)

    def echo_vvv(self, output):
        """
        Echo the given output if verbosity level is >= 3.

        Args:
            output: Text to output
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
    # If we are operating on only one file we don't know what to strip off here,
    # just return the whole thing.
    if filename_to_clean == parent_path:
        return parent_path
    return os.path.relpath(filename_to_clean, parent_path)


def read_configuration(config_file_path):
    """
    Read the given yaml configuration file, return the results.

    Args:
        config_file_path: The path to the configuration file

    Returns:
        Results of yaml.read() on the file
    """
    with open(config_file_path) as config_file:
        return yaml.load(config_file)
