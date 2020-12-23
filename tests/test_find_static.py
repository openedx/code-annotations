"""
Tests for the `find_annotations` sub-command.
"""
from unittest.mock import patch

from tests.helpers import EXIT_CODE_FAILURE, EXIT_CODE_SUCCESS, call_script


def test_missing_extension():
    result = call_script((
        'static_find_annotations',
        '--config_file',
        'tests/test_configurations/.annotations_test_missing_extension',
        '--source_path=tests/extensions/javascript_test_files/simple_success.js',
        '-vv'
    ))
    assert result.exit_code == EXIT_CODE_FAILURE
    assert 'Not all configured extensions could be loaded!' in result.output


def test_bad_extension():
    with patch('code_annotations.extensions.javascript.JavascriptAnnotationExtension.__init__') as js_init:
        js_init.side_effect = Exception('Fake failed to load javascript extension')
        result = call_script((
            'static_find_annotations',
            '--config_file',
            'tests/test_configurations/.annotations_test',
            '--source_path=tests/extensions/javascript_test_files/simple_success.js',
            '-vv'
        ))
    assert result.exit_code == EXIT_CODE_FAILURE
    assert 'Failed to load a plugin, aborting.' in result.output


def test_unknown_file_extension():
    result = call_script((
        'static_find_annotations',
        '--config_file',
        'tests/test_configurations/.annotations_test',
        '--source_path=tests/simple_success.nothing',
        '-vvv'
    ))
    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'nothing is not a known extension, skipping' in result.output
    assert 'Search found 0 annotations' in result.output


def test_file_walking():
    result = call_script((
        'static_find_annotations',
        '--config_file',
        'tests/test_configurations/.annotations_test',
        '--source_path=tests/extensions/javascript_test_files',
        '-v'
    ))
    assert result.exit_code == EXIT_CODE_FAILURE

    # Just making sure that multiple files are being walked since other tests point to only one file.
    assert 'group_failures_4' in result.output
    assert 'choice_failures_1' in result.output


def test_source_path_from_file():
    result = call_script((
        'static_find_annotations',
        '--config_file',
        'tests/test_configurations/.annotations_test',
        '-v',

    ))
    assert result.exit_code == EXIT_CODE_FAILURE
    assert "Configured for source path: tests/extensions/javascript_test_files/" in result.output


def test_report_path_from_command():
    result = call_script((
        'static_find_annotations',
        '--config_file',
        'tests/test_configurations/.annotations_test',
        '--report_path=test_reports_2'
        '-v',
    ))
    assert result.exit_code == EXIT_CODE_FAILURE
    assert "report path: test_reports_2" in result.output


def test_no_extension_results():
    result = call_script((
        'static_find_annotations',
        '--config_file',
        'tests/test_configurations/.annotations_test_python_only',
        '--source_path=tests/extensions/python_test_files/no_annotations.pyt',
        '-v',
    ))
    assert result.exit_code == EXIT_CODE_SUCCESS
    assert "Search found 0 annotations" in result.output


def test_no_report():
    result = call_script((
        'static_find_annotations',
        '--config_file',
        'tests/test_configurations/.annotations_test_python_only',
        '--source_path=tests/extensions/python_test_files/simple_success.pyt',
        '--no_report',
        '-v',
    ))
    assert result.exit_code == EXIT_CODE_SUCCESS
    assert "Search found 20 annotations" in result.output
    assert "Writing report..." not in result.output
    assert "Linting passed without errors." in result.output


def test_no_lint():
    result = call_script((
        'static_find_annotations',
        '--config_file',
        'tests/test_configurations/.annotations_test_python_only',
        '--source_path=tests/extensions/python_test_files/simple_success.pyt',
        '--no_lint',
        '-v',
    ))
    assert result.exit_code == EXIT_CODE_SUCCESS
    assert "Search found 20 annotations" in result.output
    assert "Linting passed without errors." not in result.output
    assert "Writing report..." in result.output
