"""
Tests for the `generate_docs` sub-command.
"""
import os
import re

import yaml

from tests.helpers import (
    EXIT_CODE_FAILURE,
    EXIT_CODE_SUCCESS,
    call_script,
    delete_report_files,
    get_report_filename_from_output
)


def test_generate_report_simple():
    find_result = call_script(
        (
            'static_find_annotations',
            '--config_file',
            'tests/test_configurations/.annotations_test_python_only',
            '--source_path=tests/extensions/python_test_files/simple_success.pyt',
            '--no_lint',
        ),
        delete_test_reports=False)

    assert find_result.exit_code == EXIT_CODE_SUCCESS
    assert "Writing report..." in find_result.output
    report_file = get_report_filename_from_output(find_result.output)

    report_result = call_script(
        (
            'generate_docs',
            report_file,
            '--config_file',
            'tests/test_configurations/.annotations_test_success_with_report_docs',
            '-vv'
        ),
        delete_test_docs=False
    )

    assert find_result.exit_code == EXIT_CODE_SUCCESS
    assert "Report rendered in" in report_result.output

    # All file types are created
    for created_doc in ('test_reports/index.rst', 'test_reports/choice-id.rst', 'test_reports/annotation-pii.rst'):
        assert os.path.exists(created_doc)


def _do_find(source_path, new_report_path):
    """
    Do a static annotation search with report, rename the report to a distinct name.

    Args:
        source_path: Path to the test file to run the report on
    """
    find_result_1 = call_script((
        'static_find_annotations',
        '--config_file',
        'tests/test_configurations/.annotations_test_python_only',
        f'--source_path={source_path}',
        '--no_lint',
    ), False)

    assert find_result_1.exit_code == EXIT_CODE_SUCCESS
    assert "Writing report..." in find_result_1.output

    # These will usually all run within 1 second and end up with the same filename, so rename them to something
    # distinct before they get overwritten
    original_report_filename = get_report_filename_from_output(find_result_1.output)
    os.rename(original_report_filename, new_report_path)


def test_generate_report_multiple_files():
    report_file_1 = 'test_reports/test1.yaml'
    _do_find('tests/extensions/python_test_files/simple_success.pyt', report_file_1)

    report_file_2 = 'test_reports/test2.yaml'
    _do_find('tests/extensions/python_test_files/group_ordering_1.pyt', report_file_2)

    report_file_3 = 'test_reports/test3.yaml'
    _do_find('tests/extensions/python_test_files/no_annotations.pyt', report_file_3)

    # Inject something that's not in the first file into a copy of it, this tests the code path of
    # having two plugins that find different things in the same file.
    report_file_4 = 'test_reports/test4.yaml'

    with open(report_file_1) as in_tmp:
        tmp_report = yaml.safe_load(in_tmp)

    tmp_report['simple_success.pyt'].append(
        {
            'annotation_data': ['terrible', 'irrelevant', 'silly-silly'],
            'annotation_token': '.. ignored:',
            'filename': 'simple_success.pyt',
            'found_by': 'python',
            'line_number': 999
         }
    )

    with open(report_file_4, 'w') as out_tmp:
        yaml.safe_dump(tmp_report, out_tmp)

    report_result = call_script(
        (
            'generate_docs',
            report_file_1,
            report_file_2,
            report_file_3,
            report_file_4,
            '--config_file',
            'tests/test_configurations/.annotations_test_success_with_report_docs',
        ),
        delete_test_docs=False
    )

    # Basic success
    assert report_result.exit_code == EXIT_CODE_SUCCESS
    assert "Report rendered in" in report_result.output

    # All file types are created
    for created_doc in ('test_reports/index.rst', 'test_reports/choice-id.rst', 'test_reports/annotation-pii.rst'):
        assert os.path.exists(created_doc)

    # Annotations from all files are present
    with open('test_reports/index.rst') as full_report_file:
        full_doc = full_report_file.read()

    # The first file
    assert "simple_success.pyt" in full_doc

    # The second file
    assert "group_ordering_1.pyt" in full_doc

    # This one had no annotations, and should not be in there
    assert "no_annotations.pyt" not in full_doc

    # The item we inserted above
    assert "999" in full_doc

    # Clean up after ourselves
    delete_report_files('.rst')


def test_generate_report_missing_key():
    find_result = call_script((
        'static_find_annotations',
        '--config_file',
        'tests/test_configurations/.annotations_test_python_only',
        '--source_path=tests/extensions/python_test_files/simple_success.pyt',
        '--no_lint',
        '-v',
    ), False)

    assert find_result.exit_code == EXIT_CODE_SUCCESS
    assert "Writing report..." in find_result.output
    report_file = re.search(r'Generating report to (.*)', find_result.output).groups()[0]
    assert os.path.exists(report_file)

    report_result = call_script((
        'generate_docs',
        report_file,
        '--config_file',
        'tests/test_configurations/.annotations_test_python_only',
    ))

    assert report_result.exit_code == EXIT_CODE_FAILURE
    assert "No report_template_dir key in tests/test_configurations/" in report_result.output
