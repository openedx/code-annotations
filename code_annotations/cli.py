"""
Command line interface for code annotation tools.
"""
import collections
import datetime
import traceback

import click
import jinja2
import yaml

from code_annotations.base import AnnotationConfig, ConfigurationException
from code_annotations.find_django import DjangoSearch
from code_annotations.find_static import StaticSearch
from code_annotations.helpers import fail


@click.group()
def entry_point():
    """
    Top level click command for the code annotation tools.
    """
    pass


@entry_point.command('django_find_annotations')
@click.option(
    '--config_file',
    default='.annotations',
    help='Path to the configuration file',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.option(
    '--seed_safelist/--no_safelist',
    default=False,
    show_default=True,
    help='Generate an initial safelist file based on the current Django environment.',
)
@click.option(
    '--list_local_models/--no_list_models',
    default=False,
    show_default=True,
    help='List all locally defined models (in the current repo) that require annotations.',
)
@click.option('--report_path', default=None, help='Location to write the report')
@click.option('-v', '--verbosity', count=True, help='Verbosity level (-v through -vvv)')
@click.option('--lint/--no_lint', help='Enable or disable linting checks', default=False, show_default=True)
@click.option('--report/--no_report', help='Enable or disable writing the report', default=False, show_default=True)
@click.option('--coverage/--no_coverage', help='Enable or disable coverage checks', default=False, show_default=True)
def django_find_annotations(
        config_file,
        seed_safelist,
        list_local_models,
        report_path,
        verbosity,
        lint,
        report,
        coverage
):
    """
    Subcommand for dealing with annotations in Django models.
    """
    try:
        start_time = datetime.datetime.now()
        config = AnnotationConfig(config_file, report_path, verbosity)
        searcher = DjangoSearch(config)

        # Early out if we're trying to do coverage, but a coverage target is not configured
        if coverage and not config.coverage_target:
            raise ConfigurationException("Please add 'coverage_target' to your configuration before running --coverage")

        if seed_safelist:
            searcher.seed_safelist()

        if list_local_models:
            searcher.list_local_models()

        if lint or report or coverage:
            annotated_models = searcher.search()

            if lint:
                click.echo("Performing linting checks...")

                # Check grouping and choices
                if not searcher.check_results(annotated_models):
                    click.secho("\nSearch failed due to linting errors!", fg="red")
                    click.secho("{} errors:".format(len(searcher.errors)), fg="red")
                    click.secho("---------------------------------", fg="red")
                    click.echo("\n".join(searcher.errors))
                    # If there are any errors, do not continue
                    exit(-1)
                click.echo("Linting passed without errors.")

            if coverage:
                if not searcher.check_coverage():
                    # If there are any errors, do not continue
                    exit(-1)

                click.echo("Coverage passed without errors.")

            if report:
                searcher.report(annotated_models)

            annotation_count = 0

            for filename in annotated_models:
                annotation_count += len(annotated_models[filename])

            elapsed = datetime.datetime.now() - start_time
            click.echo("Search found {} annotations in {}.".format(annotation_count, elapsed))

    except Exception as exc:  # pylint: disable=broad-except
        click.echo(traceback.print_exc())
        fail(str(exc))


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
    """
    try:
        start_time = datetime.datetime.now()
        config = AnnotationConfig(config_file, report_path, verbosity, source_path)
        searcher = StaticSearch(config)
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
        click.echo(traceback.print_exc())
        fail(str(exc))


@entry_point.command("generate_docs")
@click.option(
    '--config_file',
    default='.annotations',
    help='Path to the configuration file',
    type=click.Path(exists=True, dir_okay=False, resolve_path=True)
)
@click.argument("report", type=click.File('r'))
@click.argument("output", type=click.File('w'))
def generate_docs(
        config_file,
        report,
        output,
):
    """
    Generate documentation from a code annotations report.
    """
    config = AnnotationConfig(config_file)
    report = yaml.safe_load(report)
    annotations = []
    for anns in report.values():
        annotations.extend(anns)
    groupeds = collections.defaultdict(list)
    for ann in annotations:
        groupeds[ann['report_group_id']].append(ann)

    groups = []
    for anns in groupeds.values():
        group = {}
        anns.sort(key=lambda ann: ann['line_number'])
        group['filename'] = anns[0]['filename']
        group['line_number'] = anns[0]['line_number']
        for ann in anns:
            key = ann['annotation_token'].strip(".: ")
            value = ann['annotation_data']
            group[key] = value
        groups.append(group)

    rst_template = config.rst_template
    if not rst_template:
        raise Exception("No rst_template key in {config_file}".format(config_file=config_file))
    with open(config.rst_template) as ftemplate:
        template = jinja2.Template(ftemplate.read())
    output.write(template.render(groups=groups))
