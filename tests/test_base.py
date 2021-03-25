"""
Tests for code_annotations/base.py
"""
from collections import OrderedDict

import pytest

from code_annotations.base import AnnotationConfig, ConfigurationException
from tests.helpers import FakeConfig, FakeSearch


def test_get_group_for_token_missing_token():
    config = FakeConfig()
    search = FakeSearch(config)
    assert search._get_group_for_token('foo') is None  # pylint: disable=protected-access


def test_get_group_for_token_multiple_groups():
    config = FakeConfig()
    config.groups = {
        'group1': ['token1'],
        'group2': ['token2', 'foo']
    }
    search = FakeSearch(config)
    assert search._get_group_for_token('foo') == 'group2'  # pylint: disable=protected-access


@pytest.mark.parametrize("test_config,expected_message", [
    ('.annotations_test_missing_source_path', "source_path"),
    ('.annotations_test_missing_report_path', "report_path"),
    ('.annotations_test_missing_safelist_path', "safelist_path"),
])
def test_missing_config(test_config, expected_message):
    with pytest.raises(ConfigurationException) as exception:
        AnnotationConfig(f'tests/test_configurations/{test_config}', None, 3)

    exc_msg = str(exception.value)
    assert "required keys are missing from the configuration file" in exc_msg
    assert expected_message in exc_msg


@pytest.mark.parametrize("test_config,expected_message", [
    ('.annotations_test_coverage_negative', "Invalid coverage target. -50.0 is not between 0 and 100."),
    ('.annotations_test_coverage_over_100', "Invalid coverage target. 150.0 is not between 0 and 100."),
    ('.annotations_test_coverage_nan', 'Coverage target must be a number between 0 and 100 not "not a number".'),
])
def test_bad_coverage_targets(test_config, expected_message):
    with pytest.raises(ConfigurationException) as exception:
        AnnotationConfig(f'tests/test_configurations/{test_config}', None, 3)

    exc_msg = str(exception.value)
    assert expected_message in exc_msg


def test_coverage_target_int():
    # We just care that this doesn't throw an exception
    AnnotationConfig('tests/test_configurations/{}'.format('.annotations_test_coverage_int'), None, 3)


@pytest.mark.parametrize("test_config,expected_message", [
    ('.annotations_test_duplicate_token', ".. no_pii: is configured more than once, tokens must be unique."),
    ('.annotations_test_duplicate_token_2_groups', ".. no_pii: is configured more than once, tokens must be unique."),
    ('.annotations_test_group_no_annotations', 'Group "pii_group" must have more than one annotation.'),
    ('.annotations_test_group_one_token', 'Group "pii_group" must have more than one annotation.'),
    ('.annotations_test_group_bad_type', "{'.. pii:': ['bad', 'type']} is an unknown annotation type."),
])
def test_annotation_configuration_errors(test_config, expected_message):
    with pytest.raises(ConfigurationException) as exception:
        AnnotationConfig(f'tests/test_configurations/{test_config}', None, 3)

    exc_msg = str(exception.value)
    assert expected_message in exc_msg


def test_format_results_for_report():
    """
    Test that report formatting puts annotations into groups correctly
    """
    config = FakeConfig()
    config.echo.set_verbosity(3)
    config.groups = {
        'group1': ['token1'],
        'group2': ['token2', 'foo']
    }

    search = FakeSearch(config)

    # Create a fake result set for _format_results_for_report to work on
    fake_results = OrderedDict()

    # First file has 6 annotations. expected_group_id is a special key for this test, allowing us to loop through
    # these below and know what group each result should be in.
    fake_results['foo/bar.py'] = [
            {
                'found_by': 'test',
                'filename': 'foo/bar.py',
                'line_number': 1,
                'annotation_token': 'token2',
                'annotation_data': 'file 1 annotation 1',
                'expected_group_id': 1
            },
            {
                'found_by': 'test',
                'filename': 'foo/bar.py',
                'line_number': 1,
                'annotation_token': 'foo',
                'annotation_data': 'file 1 annotation 2',
                'expected_group_id': 1
            },
            {
                'found_by': 'test',
                'filename': 'foo/bar.py',
                'line_number': 4,
                'annotation_token': 'not_in_a_group',
                'annotation_data': 'file 1 annotation 3',
                'expected_group_id': 2
            },
            {
                'found_by': 'test',
                'filename': 'foo/bar.py',
                'line_number': 10,
                'annotation_token': 'token1',
                'annotation_data': 'file 1 annotation 4',
                'expected_group_id': 3
            },
            {
                'found_by': 'test',
                'filename': 'foo/bar.py',
                'line_number': 12,
                'annotation_token': 'token2',
                'annotation_data': 'file 1 annotation 5',
                'expected_group_id': 4
            },
            {
                'found_by': 'test',
                'filename': 'foo/bar.py',
                'line_number': 12,
                'annotation_token': 'foo',
                'annotation_data': 'file 1 annotation 6',
                'expected_group_id': 4
            },
        ]

    fake_results['foo/baz.py'] = [
            {
                'found_by': 'test',
                'filename': 'foo/bar.py',
                'line_number': 1,
                'annotation_token': 'token2',
                'annotation_data': 'file 2 annotation 1',
                'expected_group_id': 5
            },
            {
                'found_by': 'test',
                'filename': 'foo/bar.py',
                'line_number': 1,
                'annotation_token': 'foo',
                'annotation_data': 'file 1 annotation 2',
                'expected_group_id': 5
            }
        ]

    # Run the format function
    results = search._format_results_for_report(fake_results)  # pylint: disable=protected-access

    for filename in fake_results:
        for fake in fake_results[filename]:
            for formatted in results[filename]:
                # When we find the same annotation, make sure that grouping is correct
                if fake['annotation_data'] == formatted['annotation_data']:
                    assert fake['expected_group_id'] == formatted['report_group_id']
                    break
