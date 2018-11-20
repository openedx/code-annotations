"""
Command line interface for code annotation tools.
"""
import os
import sys

import click
import yaml

from code_annotations.django_reporting_helpers import get_models_requiring_annotations

DEFAULT_SAFELIST_FILE_PATH = '.pii_safe_list.yaml'


def fail(msg):
    """
    Log the message and exit.
    """
    click.echo(msg)
    sys.exit(1)


@click.group()
@click.option(
    '--config_file', 'config_file_path',
    type=click.Path(exists=True, dir_okay=False),
    help='Config file for all code annotation tools.',
)
@click.pass_context
def cli(ctx, config_file_path):
    """
    Code annotation tools.
    """
    # Code placed in this function runs first, before entering any subcommands.
    ctx.ensure_object(dict)
    with open(config_file_path) as config_file:
        ctx.obj['config'] = yaml.load(config_file)
    # Now, the ctx object will be passed along to subcommands as the first argument.


@cli.command('pii_report_django')
@click.option(
    '--seed_safelist',
    is_flag=True,
    help='Generate an initial safelist file based on the current Django environment.',
)
@click.pass_context
def pii_report_django(ctx, seed_safelist):
    """
    Subcommand for dealing with PII in Django models.
    """
    safelist_file_path = ctx.obj['config'].get('safelist_path', DEFAULT_SAFELIST_FILE_PATH)
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
