"""
Tests for code_annotations/base.py
"""
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
        'group1': [
            {'token1': None}
        ],
        'group2': [
            {'token2': None, 'foo': None}
        ]
    }
    search = FakeSearch(config)
    assert search._get_group_for_token('foo') is None  # pylint: disable=protected-access


@pytest.mark.parametrize("test_config,expected_message", [
    ('.annotations_test_missing_source_path', "source_path"),
    ('.annotations_test_missing_report_path', "report_path"),
    ('.annotations_test_missing_safelist_path', "safelist_path"),
])
def test_missing_config(test_config, expected_message):
    with pytest.raises(ConfigurationException) as exception:
        AnnotationConfig('tests/test_configurations/{}'.format(test_config), None, 3)

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
        AnnotationConfig('tests/test_configurations/{}'.format(test_config), None, 3)

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
        AnnotationConfig('tests/test_configurations/{}'.format(test_config), None, 3)

    exc_msg = str(exception.value)
    assert expected_message in exc_msg
