"""
Helper code shared between tests.
"""
import os
import re

from click.testing import CliRunner

from code_annotations.base import BaseSearch, VerboseEcho
from code_annotations.cli import entry_point

EXIT_CODE_SUCCESS = 0
EXIT_CODE_FAILURE = -1
DEFAULT_FAKE_SAFELIST_PATH = 'fake_safelist_path.yaml'

FAKE_CONFIG_FILE = """
safelist_path: {}
report_path: test_reports
source_path: ../
annotations:
    ".. no_pii::":
    ".. ignored::":
        choices: [irrelevant, terrible, silly-silly]
    "pii_group":
        - ".. pii::":
        - ".. pii_types::":
            choices: [id, name, other]
        - ".. pii_retirement::":
            choices: [retained, local_api, consumer_api, third_party]
extensions:
    python:
        - py
""".format(DEFAULT_FAKE_SAFELIST_PATH)


class FakeConfig(object):
    """
    Simple config for testing without reading a config file.
    """

    annotations = {}
    annotation_regexes = []
    annotation_tokens = []
    groups = []
    echo = VerboseEcho()


class FakeSearch(BaseSearch):
    """
    Simple test class for directly testing BaseSearch since it's abstract.
    """

    def search(self):
        """
        Override for abstract base method.
        """
        pass


def call_script(args_list, delete_test_reports=True):
    """
    Call the code_annotations script with the given params and a generic config file.

    Args:
        args_list: Arguments to pass to the script.
        delete_test_reports: Bool, whether to try to delete any created report files. Make this false if you want
            to keep the report around for debugging a test.
    Returns:
        click.testing.Result: Result from the `CliRunner.invoke()` call.
    """
    runner = CliRunner()
    result = runner.invoke(
        entry_point,
        args_list,
        # catch_exceptions=False  # Uncomment this if you need more information on an exception in a test
    )
    print(result)
    print(result.output)

    if delete_test_reports:
        try:
            filelist = [f for f in os.listdir('test_reports') if f.endswith(".yaml")]
            for f in filelist:
                os.remove(os.path.join('test_reports', f))
        except Exception:  # pylint: disable=broad-except
            pass
    return result


def call_script_isolated(
        args_list,
        test_filesystem_cb=None,
        test_filesystem_report_cb=None,
        fake_safelist_data="{}"
):
    """
    Call the code_annotations script with the given params and a generic config file.

    Args:
        args_list: Arguments to pass to the command line call
        test_filesystem_cb: Callback function, called after the command is run, before the temp filesystem is
            cleared. Use this if you need access to non-report files in the temp filesystem.
        test_filesystem_report_cb: Callback function, called after the command is run, before the temp filesystem
            is cleared. Callback is called with the raw text contents of the report file.
        fake_safelist_data: Raw text to write to the safelist file before the command is called.
        safelist_path: File path to write the safelist to. Used when writing a fake safelist, but not automatically
            passed to the command.

    Returns:
        click.testing.Result: Result from the `CliRunner.invoke()` call.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('test_config.yml', 'w') as f:
            f.write(FAKE_CONFIG_FILE)

        if fake_safelist_data:
            with open(DEFAULT_FAKE_SAFELIST_PATH, 'w') as f:
                f.write(fake_safelist_data)

        result = runner.invoke(
            entry_point,
            args_list,
            # catch_exceptions=False
        )
        print(result)
        print(result.output)

        if test_filesystem_cb:
            test_filesystem_cb()

        if test_filesystem_report_cb:
            try:
                report_file = re.search(r'Generating report to (.*)', result.output).groups()[0]
                with open(report_file, 'r') as f:
                    report_contents = f.read()

                test_filesystem_report_cb(report_contents)
            except (AttributeError, IndexError):
                # If there is no file when expected, the test should fail elsewhere. Just skip the callback.
                pass

    return result
