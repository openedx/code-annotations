"""
Tests for the Javascript static extension
"""
import pytest

from tests.helpers import EXIT_CODE_FAILURE, EXIT_CODE_SUCCESS, call_script


@pytest.mark.parametrize('test_file,expected_exit_code,expected_message', [
    ('simple_success.js', EXIT_CODE_SUCCESS, 'Search found 26 annotations in'),
    ('group_ordering_1.js', EXIT_CODE_SUCCESS, 'Search found 3 annotations in'),
    ('group_ordering_2.js', EXIT_CODE_SUCCESS, 'Search found 9 annotations in'),
    ('group_failures_1.js', EXIT_CODE_FAILURE, 'File finished with an incomplete group'),
    ('group_failures_2.js', EXIT_CODE_FAILURE, 'File finished with an incomplete group'),
    ('group_failures_4.js', EXIT_CODE_FAILURE, '".. no_pii:" is not in the group that starts with'),
    ('group_failures_5.js', EXIT_CODE_FAILURE, '".. pii_types:" is already in the group that starts with'),
    ('choice_failures_1.js', EXIT_CODE_FAILURE, '"doesnotexist" is not a valid choice for ".. ignored:"'),
    ('choice_failures_2.js', EXIT_CODE_FAILURE, '"doesnotexist" is not a valid choice for ".. ignored:"'),
    ('choice_failures_3.js', EXIT_CODE_FAILURE, '"terrible|silly-silly" is not a valid choice for ".. ignored:"'),
    ('choice_failures_4.js', EXIT_CODE_FAILURE, '"terrible" is already present in this annotation'),
    ('choice_failures_5.js', EXIT_CODE_FAILURE, 'No choices found for ".. ignored:"'),
])
def test_grouping_and_choice_failures(test_file, expected_exit_code, expected_message):
    result = call_script((
        'static_find_annotations',
        '--config_file',
        'tests/test_configurations/.annotations_test',
        '--source_path=tests/extensions/javascript_test_files/' + test_file,
        '-vv'
    ))
    assert result.exit_code == expected_exit_code
    assert expected_message in result.output

    if expected_exit_code == EXIT_CODE_FAILURE:
        assert "Search failed due to linting errors!" in result.output
