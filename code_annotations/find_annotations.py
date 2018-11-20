"""
Click command to do static annotation searching via Stevedore plugins.
"""
import datetime
import errno
import os

import click
import yaml
from stevedore import named

from code_annotations.exceptions import ConfigurationException
from code_annotations.helpers import VerboseEcho

# Global logger for this script, shared with extensions
ECHO = VerboseEcho()


def load_failed_handler(*args, **kwargs):
    """
    Handle failures to load an extension.

    Dumps the error and raises an exception. By default these
    errors just fail silently.

    Args:
        *args:
        **kwargs:

    Returns:
        None

    Raises:
        ConfigurationException
    """
    ECHO.echo(args)
    ECHO.echo(kwargs)
    raise ConfigurationException('Failed to load a plugin, aborting.')


def search_extension(ext, file_handle, file_extensions_map, filename_extension):
    """
    Execute a search on the given file using the given extension.

    Args:
        ext: Extension to execute the search on
        file_handle: An open file handle search
        file_extensions_map: Dict mapping of extension names to configured filename extensions
        filename_extension: The filename extension of the file being searched

    Returns:
        Tuple of (extension name, list of found annotation dicts)
    """
    # Reset the read handle to the beginning of the file in case another
    # extension already moved it
    file_handle.seek(0)

    # Only search this file if we are configured for its extension
    if filename_extension in file_extensions_map[ext.name]:
        ext_results = ext.obj.search(file_handle)

        if ext_results:
            return ext.name, ext_results

    return ext.name, None


def format_file_results(all_results, results):
    """
    Add all extensions' search results for a file to the overall results.

    Args:
        all_results: Aggregated results to add the results to
        results: Results of search() on a single file

    Returns:
        None, modifies all_results
    """
    # _ here is the extension name, as required by Stevedore map(). Each
    # annotation already has the extension name so we can ignore it here
    for _, annotations in results:
        if annotations is None:
            continue

        # TODO: The file_path should be the same for all of these results
        # so we should be able to optimize getting file_path and making
        # sure it exists in the dict to do this less often.
        file_path = annotations[0]['filename']

        if file_path not in all_results:
            all_results[file_path] = []

        # TODO: add support for multiple extensions in the 'found_by' key
        # and de-dupe results
        all_results[file_path].extend(annotations)


def configure(config, source_path, report_path, verbosity):
    """
    Read the configuration file, and handle command line overrides.

    Args:
        config: Location of the configuration file
        source_path: Path to the code to be searched
        report_path: Directory where the report will be generated
        verbosity: Integer indicating the runtime verbosity level

    Returns:
        Configuration dict, updated with overrides
    """
    # TODO: Add include / exclude directories
    ECHO.echo('Reading configuration from {}'.format(config))

    with open(config) as config_file:
        config = yaml.load(config_file)

    if not source_path and not config['source_path']:
        raise ConfigurationException('source_path not given and not in configuration file')

    if not report_path and not config['report_path']:
        raise ConfigurationException('report_path not given and not in configuration file')

    if source_path:
        config['source_path'] = source_path

    if report_path:
        config['report_path'] = report_path

    # This is a runtime option, shouldn't be in the config file
    config['verbosity'] = verbosity

    ECHO.set_verbosity(verbosity)
    ECHO.echo_v("Verbosity level set to {}".format(config['verbosity']))
    ECHO.echo_v("Configuration:")
    ECHO.echo_v(config)

    return config


def search(mgr, config):
    """
    Walk the source tree, send known file types to extensions.

    Args:
        mgr: Stevedore NamedExtensionManager
        config: Configuration dict

    Returns:
        Dict containing all of the search results
    """
    # Index the results by extension name
    file_extensions_map = {}
    known_extensions = set()
    for extension_name in config['extensions']:
        file_extensions_map[extension_name] = config['extensions'][extension_name]
        known_extensions.update(config['extensions'][extension_name])

    all_results = {}

    for root, _, files in os.walk(config['source_path']):
        for filename in files:
            filename_extension = os.path.splitext(filename)[1][1:]

            if filename_extension not in known_extensions:
                ECHO.echo_vvv("{} is not a known extension, skipping ({}).".format(filename_extension, filename))
                continue

            full_name = os.path.join(root, filename)

            ECHO.echo_vvv(full_name)

            # TODO: This should probably be a generator so we don't have to store all results in memory
            with open(full_name, 'r') as file_handle:
                # Call search_extension on all loaded extensions
                results = mgr.map(search_extension, file_handle, file_extensions_map, filename_extension)

                # Format and add the results to our running full set
                format_file_results(all_results, results)

    return all_results


def report(all_results, config):
    """
    Genrates the YAML report of all search results.

    Args:
        all_results: Dict of found annotations, indexed by filename
        config: Configuration dict

    Returns:
        Filename of generated report
    """
    ECHO.echo_vv(yaml.dump(all_results, default_flow_style=False))

    now = datetime.datetime.now()
    report_filename = os.path.join(config['report_path'], '{}.yaml'.format(now.strftime('%Y-%d-%m-%H-%M-%S')))

    ECHO.echo("Generating report to {}".format(report_filename))

    try:
        os.makedirs(config['report_path'])
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    with open(report_filename, 'w+') as report_file:
        yaml.dump(all_results, report_file, default_flow_style=False)

    return report_filename


@click.command('static_find_annotations')
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
    Click command to find annotations via static file analysis.

    Args:
        config_file: Path to the configuration file
        source_path: Location of the source code to search
        report_path: Location to write the report
        verbosity: Verbosity level for output

    Returns:
        None
    """
    now = datetime.datetime.now()

    config = configure(config_file, source_path, report_path, verbosity)

    ECHO.echo("Configured for source path: {}, report path: {}".format(config['source_path'], config['report_path']))

    # These are the names of all of our configured extensions
    configured_extension_names = config['extensions'].keys()

    ECHO.echo_vv("Configured extension names: {}".format(" ".join(configured_extension_names)))

    # Load Stevedore extensions that we are configured for (and only those)
    mgr = named.NamedExtensionManager(
        names=configured_extension_names,
        namespace='annotation_finder.searchers',
        invoke_on_load=True,
        on_load_failure_callback=load_failed_handler,
        invoke_args=(config, ECHO),
    )

    # Output all found extension entry points (whether or not they were loaded)
    ECHO.echo_vv("Stevedore entry points found: {}".format(str(mgr.list_entry_points())))

    # Output all extensions that were actually able to load
    ECHO.echo_v("Loaded extensions: {}".format(" ".join([x.name for x in mgr.extensions])))

    all_results = search(mgr, config)
    report_filename = report(all_results, config)

    done = datetime.datetime.now()
    elapsed = done - now

    ECHO.echo("Report completed in {}: {}".format(elapsed, report_filename))
