"""
Command line interface for code annotation tools.
"""
import os
import sys

import click
import yaml

from code_annotations.django_reporting_helpers import get_models_requiring_annotations
from code_annotations.find_annotations import StaticSearch
from code_annotations.helpers import read_configuration

DEFAULT_SAFELIST_FILE_PATH = '.pii_safe_list.yaml'


def fail(msg):
    """
    Log the message and exit.
    """
    click.echo(msg)
    sys.exit(1)


@click.group()
def entry_point():
    """
    Top level click command for the code annotation tools.
    """
    pass


@entry_point.command('pii_report_django')
@click.option(
    '--config_file',
    default='.annotations',
    help='Path to the configuration file',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    '--seed_safelist',
    is_flag=True,
    help='Generate an initial safelist file based on the current Django environment.',
)
def pii_report_django(config_file, seed_safelist):
    """
    Subcommand for dealing with PII in Django models.
    """
    config = read_configuration(config_file)

    safelist_file_path = config.get('safelist_path', DEFAULT_SAFELIST_FILE_PATH)
    if seed_safelist:
        if os.path.exists(safelist_file_path):
            fail('{} already exists, not overwriting.'.format(safelist_file_path))
        local_model_ids, non_local_model_ids = get_models_requiring_annotations()
        click.echo(
            'Listing {} local models requiring annotations:'.format(len(local_model_ids))
        )
        for model_id in local_model_ids:
            click.echo('     {}'.format(model_id))
        click.echo(
            'Found {} non-local models requiring annotations. Adding them to safelist.'.format(len(non_local_model_ids))
        )
        click.echo(
            'Found {} local models requiring annotations. NOT adding them to safelist.'.format(len(local_model_ids))
        )
        safelist_data = {model_id: {} for model_id in non_local_model_ids}
        with open(safelist_file_path, 'w') as safelist_file:
            yaml.dump(safelist_data, stream=safelist_file)
        click.echo('Successfully created safelist file "{}".'.format(safelist_file_path))
        click.echo('Now, you need to:')
        click.echo('  1) Make sure that any un-annotated models in the safelist are annotated, and')
        click.echo('  2) Annotate the local models listed above.')
        return  # this was a special function of the pii_report_django subcommand, so terminate the program here.


@entry_point.command('static_find_annotations')
@click.option(
    '--config_file',
    default='.annotations',
    help='Path to the configuration file',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    '--source_path',
    default=None,
    help='Location of the source code to search',
    type=click.Path(exists=True, dir_okay=True, resolve_path=True)
)
@click.option('--report_path', default=None, help='Location to write the report')
@click.option('-v', '--verbosity', count=True, help='Verbosity level (-v through -vvv)')
def static_find_annotations(config_file, source_path, report_path, verbosity):
    """
    Subcommand to find annotations via static file analysis.

    Args:
        config_file: Path to the configuration file
        source_path: Location of the source code to search
        report_path: Location to write the report
        verbosity: Verbosity level for output

    Returns:
        None
    """
    searcher = StaticSearch(config_file, source_path, report_path, verbosity)
    searcher.search()
