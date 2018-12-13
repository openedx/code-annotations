"""
Command line interface for code annotation tools.
"""
import datetime
import os

import click
import yaml

from code_annotations.django_reporting_helpers import get_models_requiring_annotations
from code_annotations.find_annotations import StaticSearch
from code_annotations.helpers import fail, read_configuration

DEFAULT_SAFELIST_FILE_PATH = '.pii_safe_list.yml'


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
@click.option(
    '--list_local_models',
    is_flag=True,
    help='List all locally defined models (in the current repo) that require annotations.',
)
def pii_report_django(config_file, seed_safelist, list_local_models):
    """
    Subcommand for dealing with PII in Django models.
    """
    special_functions = [
        seed_safelist,
        list_local_models
    ]
    if special_functions.count(True) > 1:
        fail('Multiple mutually-exclusive special functions were specified.')

    config = read_configuration(config_file)
    config.setdefault('safelist_path', DEFAULT_SAFELIST_FILE_PATH)

    if seed_safelist:
        if os.path.exists(config['safelist_path']):
            fail('{} already exists, not overwriting.'.format(config['safelist_path']))
        _, non_local_model_ids = get_models_requiring_annotations()
        click.echo(
            'Found {} non-local models requiring annotations. Adding them to safelist.'.format(len(non_local_model_ids))
        )
        safelist_data = {model_id: {} for model_id in non_local_model_ids}
        with open(config['safelist_path'], 'w') as safelist_file:
            yaml.dump(safelist_data, stream=safelist_file)
        click.echo('Successfully created safelist file "{}".'.format(config['safelist_path']))
        click.echo('Now, you need to:')
        click.echo('  1) Make sure that any un-annotated models in the safelist are annotated, and')
        click.echo('  2) Annotate any LOCAL models (see --list_local_models).')
        return  # this was a special function of the pii_report_django subcommand, so terminate the program here.

    if list_local_models:
        local_model_ids, _ = get_models_requiring_annotations()
        if local_model_ids:
            click.echo(
                'Listing {} local models requiring annotations:'.format(len(local_model_ids))
            )
            for model_id in local_model_ids:
                click.echo('     {}'.format(model_id))
        else:
            click.echo('No local models requiring annotations.')
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
    help='Location of the source code to search',
    type=click.Path(exists=True, dir_okay=True, resolve_path=True)
)
@click.option('--report_path', default=None, help='Location to write the report')
@click.option('-v', '--verbosity', count=True, help='Verbosity level (-v through -vvv)')
@click.option('--lint/--no_lint', help='Enable or disable linting checks', default=True, show_default=True)
@click.option('--report/--no_report', help='Enable or disable writing the report file', default=True, show_default=True)
def static_find_annotations(config_file, source_path, report_path, verbosity, lint, report):
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
    try:
        start_time = datetime.datetime.now()
        searcher = StaticSearch(config_file, source_path, report_path, verbosity)
        all_results = searcher.search()

        if lint:
            click.echo("Performing linting checks...")
            # Check grouping and choices
            searcher.check_results(all_results)

            # If there are any errors, do not generate the report
            if searcher.errors:
                click.secho("\nSearch failed due to linting errors!", fg="red")
                click.secho("{} errors:".format(len(searcher.errors)), fg="red")
                click.secho("---------------------------------", fg="red")
                click.echo("\n".join(searcher.errors))
                exit(-1)
            click.echo("Linting passed without errors.")

        if report:
            click.echo("Writing report...")
            report_filename = searcher.report(all_results)
            click.echo("Report written to {}.".format(report_filename))

        elapsed = datetime.datetime.now() - start_time
        annotation_count = 0

        for filename in all_results:
            annotation_count += len(all_results[filename])

        click.echo("Search found {} annotations in {}.".format(annotation_count, elapsed))

    except Exception as exc:  # pylint: disable=broad-except
        fail(str(exc))
