"""
Helper code shared between tests.
"""
import os

from click.testing import CliRunner

from code_annotations.cli import entry_point

EXIT_CODE_SUCCESS = 0
EXIT_CODE_FAILURE = -1


def call_script(args_list, delete_test_reports=True):
    """
    Call the code_annotations script with the given params and a generic config file.

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
