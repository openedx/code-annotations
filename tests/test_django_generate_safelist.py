#!/usr/bin/env python
"""
Tests for seeding the safelist.
"""
import os
from unittest.mock import DEFAULT, MagicMock, patch

import pytest

from code_annotations.find_django import DjangoSearch
from tests.helpers import DEFAULT_FAKE_SAFELIST_PATH, EXIT_CODE_FAILURE, EXIT_CODE_SUCCESS, call_script_isolated


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT,
)
@pytest.mark.parametrize("local_models,non_local_models", [
    (
        [
            MagicMock(_meta=MagicMock(app_label='fake_app_1', object_name='FakeModelA')),
            MagicMock(_meta=MagicMock(app_label='fake_app_2', object_name='FakeModelB')),
        ],
        [
            MagicMock(_meta=MagicMock(app_label='fake_app_3', object_name='FakeModelC')),
            MagicMock(_meta=MagicMock(app_label='fake_app_4', object_name='FakeModelD')),
        ],
    ),
    (
        [
            MagicMock(_meta=MagicMock(app_label='fake_app_1', object_name='FakeModelA')),
            MagicMock(_meta=MagicMock(app_label='fake_app_2', object_name='FakeModelB')),
        ],
        [],  # No non-local models to add to the safelist.
    ),
])
def test_seeding_safelist(local_models, non_local_models, **kwargs):
    """
    Test the success case for seeding the safelist.
    """
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        local_models,
        non_local_models,
        0,  # Number of total models found, irrelevant here
        []  # List of model ids that need anntations, irrelevant here
    )

    def test_safelist_callback():
        assert os.path.exists(DEFAULT_FAKE_SAFELIST_PATH)
        with open(DEFAULT_FAKE_SAFELIST_PATH) as fake_safelist_file:
            fake_safelist = fake_safelist_file.read()
        for model in non_local_models:
            assert DjangoSearch.get_model_id(model) in fake_safelist
        for model in local_models:
            assert DjangoSearch.get_model_id(model) not in fake_safelist

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--seed_safelist'],
        test_filesystem_cb=test_safelist_callback,
        fake_safelist_data=None
    )
    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'Successfully created safelist file' in result.output


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT,
)
def test_safelist_exists(**kwargs):
    """
    Test the success case for seeding the safelist.
    """
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = ([], [], 0, [])

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--seed_safelist']
    )
    assert result.exit_code == EXIT_CODE_FAILURE
    assert 'already exists, not overwriting.' in result.output
