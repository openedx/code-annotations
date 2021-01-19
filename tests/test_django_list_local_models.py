#!/usr/bin/env python
"""
Tests for listing local models.
"""
from unittest.mock import DEFAULT, MagicMock, patch

import pytest

from tests.helpers import call_script_isolated


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT,
)
@pytest.mark.parametrize("local_model_ids,non_local_model_ids", [
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
        [],  # No local models to print on stdout.
        [
            MagicMock(_meta=MagicMock(app_label='fake_app_3', object_name='FakeModelC')),
            MagicMock(_meta=MagicMock(app_label='fake_app_4', object_name='FakeModelD')),
        ],
    ),
])
def test_listing_local_models(local_model_ids, non_local_model_ids, **kwargs):
    """
    Test the success case for listing local models.
    """
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        local_model_ids,
        non_local_model_ids,
        0,  # Number of total models found, irrelevant here
        []  # List of model ids that need anntations, irrelevant here
    )
    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--list_local_models']
    )
    assert result.exit_code == 0
    if not local_model_ids:
        assert 'No local models requiring annotations.' in result.output
    else:
        assert 'Listing {} local models requiring annotations'.format(len(local_model_ids)) in result.output
