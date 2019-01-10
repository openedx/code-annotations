#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for find annotations in Django models.
"""
from mock import DEFAULT, patch

from code_annotations.django_reporting_helpers import get_model_id
from tests.fake_models import (
    FakeBaseModelNoAnnotation,
    FakeBaseModelWithAnnotation,
    FakeBaseModelWithNoDocstring,
    FakeChildModelMultiAnnotation,
    FakeChildModelMultiWithBrokenAnnotations,
    FakeChildModelSingleAnnotation,
    FakeChildModelSingleWithAnnotation
)
from tests.helpers import EXIT_CODE_FAILURE, EXIT_CODE_SUCCESS, call_script_isolated


@patch.multiple(
    'code_annotations.find_django',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_simple_success(**kwargs):
    """
    Tests the basic case where all models have annotations, with an empty safelist.
    """
    test_models = {FakeChildModelSingleAnnotation, FakeChildModelMultiAnnotation, FakeChildModelSingleWithAnnotation}
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set()
    )

    def report_callback(report_contents):
        """
        Get the text of the report and make sure all of the expected models are in it.

        Args:
            report_contents:

        Returns:
            Raw text contents of the generated report file
        """
        for model in test_models:
            assert 'object_id: {}'.format(get_model_id(model)) in report_contents

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report'],
        test_filesystem_report_cb=report_callback
    )

    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'Linting passed without errors' in result.output
    assert 'Generating report to' in result.output
    assert 'Search found 5 annotations' in result.output


@patch.multiple(
    'code_annotations.find_django',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_no_viable_models(**kwargs):
    """
    Tests the basic case where all models have annotations, with an empty safelist.
    """
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        set(),
        set()
    )

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report'],
    )

    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'Linting passed without errors' in result.output
    assert 'Generating report to' in result.output
    assert 'Search found 0 annotations' in result.output


@patch.multiple(
    'code_annotations.find_django',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_model_not_annotated(**kwargs):
    """
    Test that a non-annotated model fails.
    """
    test_models = {FakeBaseModelNoAnnotation, }
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set()
    )

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report']
    )

    assert result.exit_code == EXIT_CODE_FAILURE
    assert 'fake_app_1.FakeBaseModel is not annotated and not in the safelist!' in result.output
    assert '1 errors:' in result.output
    assert 'Generating report to' not in result.output


@patch.multiple(
    'code_annotations.find_django',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_model_in_safelist_not_annotated(**kwargs):
    """
    Test that a safelisted model with no annotations fails.
    """
    test_models = {FakeBaseModelNoAnnotation, }
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set()
    )

    fake_safelist_data = """
    {
        fake_app_1.FakeBaseModel: {}
    }
    """

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report'],
        fake_safelist_data=fake_safelist_data,
    )

    assert result.exit_code == EXIT_CODE_FAILURE
    assert 'fake_app_1.FakeBaseModel is in the safelist but has no annotations!' in result.output
    assert '1 errors:' in result.output
    assert 'Generating report to' not in result.output


@patch.multiple(
    'code_annotations.find_django',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_model_in_safelist_annotated(**kwargs):
    """
    Test that a safelisted model succeeds.
    """
    test_models = {FakeBaseModelNoAnnotation, }
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set()
    )

    fake_safelist_data = """
    {
        fake_app_1.FakeBaseModel: {".. no_pii::": "This model is annotated."}
    }
    """

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report'],
        fake_safelist_data=fake_safelist_data,
    )

    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'Linting passed without errors' in result.output
    assert 'Generating report to' in result.output
    assert 'Search found 1 annotations' in result.output


@patch.multiple(
    'code_annotations.find_django',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_no_safelist(**kwargs):
    """
    Test that we fail when there is no safelist.
    """
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (set(), set())

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report'],
        fake_safelist_data=None,
    )

    assert result.exit_code == EXIT_CODE_FAILURE
    assert 'Safelist not found!' in result.output
    assert 'Generating report to' not in result.output


@patch.multiple(
    'code_annotations.find_django',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_in_safelist_and_annotated(**kwargs):
    """
    Test that a model which is annotated and also in the safelist fails.
    """
    test_models = {FakeBaseModelWithAnnotation, }
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set()
    )

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report'],
        fake_safelist_data='{{{}: ".. no_pii::"}}'.format(get_model_id(FakeBaseModelWithAnnotation))
    )

    assert result.exit_code == EXIT_CODE_FAILURE
    assert 'fake_app_2.FakeBaseModelWithAnnotation is annotated, but also in the safelist.' in result.output
    assert '1 errors:' in result.output
    assert 'Generating report to' not in result.output


@patch.multiple(
    'code_annotations.find_django',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_no_docstring(**kwargs):
    """
    Test that a model with no docstring doesn't break anything.
    """
    test_models = {FakeBaseModelWithNoDocstring, }
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set()
    )
    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report']
    )

    assert result.exit_code == EXIT_CODE_FAILURE
    assert 'fake_app_2.FakeBaseModelWithNoDocstring is not annotated and not in the safelist!' in result.output
    assert '1 errors:' in result.output
    assert 'Generating report to' not in result.output


@patch.multiple(
    'code_annotations.find_django',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_ordering_error(**kwargs):
    """
    Tests broken annotations to make sure the error paths work.
    """
    test_models = {FakeChildModelSingleAnnotation, FakeChildModelMultiWithBrokenAnnotations}
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set()
    )

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report']
    )

    assert result.exit_code == EXIT_CODE_FAILURE
    assert '".. pii_types::" is a member of a group, but no group is started!' in result.output
    assert '".. no_pii::" is not in the group that starts with' in result.output


@patch.multiple(
    'code_annotations.find_django',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_without_linting(**kwargs):
    """
    Tests to make sure reports will be written in the case of errors, if linting is off.
    """
    test_models = {FakeChildModelSingleAnnotation, FakeChildModelMultiWithBrokenAnnotations}
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set()
    )

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--report']
    )

    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'Linting passed without errors' not in result.output
    assert 'Generating report to' in result.output


@patch.multiple(
    'code_annotations.find_django',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_without_report(**kwargs):
    """
    Tests to make sure reports will be written in the case of errors, if linting is off.
    """
    test_models = {FakeChildModelSingleAnnotation}
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set()
    )

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint']
    )

    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'Linting passed without errors' in result.output
    assert 'Generating report to' not in result.output
