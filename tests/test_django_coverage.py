"""
Tests for the DjangoSearch coverage functionality.
"""
from unittest.mock import DEFAULT, patch

import pytest

from code_annotations.find_django import DjangoSearch
from tests.fake_models import (
    FakeBaseModelAbstract,
    FakeBaseModelBoring,
    FakeBaseModelBoringWithAnnotations,
    FakeBaseModelNoAnnotation,
    FakeBaseModelProxy,
    FakeBaseModelWithAnnotation,
    FakeBaseModelWithNoDocstring,
    FakeChildModelMultiAnnotation,
    FakeChildModelMultiWithBrokenAnnotations,
    FakeChildModelSingleAnnotation,
    FakeChildModelSingleWithAnnotation
)
from tests.helpers import EXIT_CODE_FAILURE, EXIT_CODE_SUCCESS, call_script_isolated

ALL_FAKE_MODELS = (
    FakeBaseModelAbstract,
    FakeBaseModelBoring,
    FakeBaseModelBoringWithAnnotations,
    FakeBaseModelNoAnnotation,
    FakeBaseModelProxy,
    FakeBaseModelWithAnnotation,
    FakeBaseModelWithNoDocstring,
    FakeChildModelMultiAnnotation,
    FakeChildModelMultiWithBrokenAnnotations,
    FakeChildModelSingleAnnotation,
    FakeChildModelSingleWithAnnotation
)


@patch('code_annotations.find_django.issubclass')
@patch('code_annotations.find_django.DjangoSearch.setup_django')
@patch('code_annotations.find_django.DjangoSearch.is_non_local')
@patch('code_annotations.find_django.django.apps.apps.get_app_configs')
def test_coverage_all_models(mock_get_app_configs, mock_is_non_local, mock_setup_django, mock_issubclass):
    # Lots of fakery going on here. This class mocks Django AppConfigs to deliver our fake models.
    class FakeAppConfig:
        def get_models(self):
            return ALL_FAKE_MODELS

    # This lets us deterministically decide that one model is local, and the other isn't, for testing both branches.
    mock_is_non_local.side_effect = [True, False] * 8

    # This just fakes setting up Django
    mock_setup_django.return_value = True

    # This mocks out Django's get_app_configs to return our fake AppConfig
    mock_get_app_configs.return_value = [FakeAppConfig()]

    # This lets us pretend that all of our fake models inherit from Django's model.Model.
    # If we try to do that inheritance Django will throw errors unless we do a full Django
    # testing setup.
    mock_issubclass.return_value = True

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--coverage', '-vvv'],
    )

    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'Found 11 total models.' in result.output
    assert 'Coverage is 66.7%' in result.output
    assert 'Coverage found 3 uncovered models:' in result.output
    assert 'Search found 10 annotations' in result.output


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT,
)
@pytest.mark.parametrize("local_models,should_succeed,expected_message", [
    (
        [FakeBaseModelNoAnnotation, FakeBaseModelWithNoDocstring, FakeChildModelSingleAnnotation],
        False,
        "Coverage threshold not met! Needed 50.0, actually 33.3!"
    ),
    (
        [FakeBaseModelNoAnnotation, FakeBaseModelBoringWithAnnotations, FakeChildModelSingleAnnotation],
        True,
        "Coverage is 66.7%"
    ),
    (
        [FakeBaseModelNoAnnotation, FakeChildModelSingleAnnotation],
        True,
        "Coverage is 50.0%"
    ),
    (
        [FakeBaseModelBoringWithAnnotations, FakeChildModelSingleAnnotation],
        True,
        "Coverage is 100.0%"
    ),
    (
        [FakeBaseModelNoAnnotation, FakeBaseModelWithNoDocstring],
        False,
        "Coverage threshold not met! Needed 50.0, actually 0.0!"
    ),
    (
        [],
        True,
        "Coverage is 100.0%"
    ),
])
def test_coverage_thresholds(local_models, should_succeed, expected_message, **kwargs):
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        set(local_models),
        set(),
        len(local_models),
        [DjangoSearch.get_model_id(m) for m in local_models]
    )

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--coverage', '-vvv'],
    )

    assert result.exit_code == EXIT_CODE_SUCCESS if should_succeed else EXIT_CODE_FAILURE
    assert expected_message in result.output
