#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for the `code-annotations` module.
"""
import os

import pytest
from click.testing import CliRunner
from mock import DEFAULT, MagicMock, patch

from code_annotations.cli import entry_point
from code_annotations.django_reporting_helpers import get_model_id

FAKE_SAFELIST_PATH = 'fake_safelist_path.yaml'

FAKE_CONFIG_FILE = """
safelist_path: {fake_safelist_path}
report_path: test_reports
annotations:
    pii:
        - ".. pii::"
        - ".. pii_types::":
            choices: [id, name, other]
        - ".. pii_retirement::":
            choices: [retained, local_api, consumer_api, third_party]
    nopii: ".. no_pii::"
    ignored:
        ".. ignored::":
            choices: [irrelevant, terrible, silly-silly]
""".format(
    fake_safelist_path=FAKE_SAFELIST_PATH
)


def _call_script(args_list, test_filesystem_cb=None):
    """
    Call the code_annotations script with the given params and a generic config file.

    Returns:
        click.testing.Result: Result from the `CliRunner.invoke()` call.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('test_config.yml', 'w') as f:
            f.write(FAKE_CONFIG_FILE)

        result = runner.invoke(
            entry_point,
            args_list
        )
        print(result)
        print(result.output)

        if test_filesystem_cb:
            test_filesystem_cb()
    return result


@patch.multiple(
    'code_annotations.find_django',
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
    )

    def test_safelist_callback():
        assert os.path.exists(FAKE_SAFELIST_PATH)
        with open(FAKE_SAFELIST_PATH, 'r') as fake_safelist_file:
            fake_safelist = fake_safelist_file.read()
        for model in non_local_models:
            assert get_model_id(model) in fake_safelist
        for model in local_models:
            assert get_model_id(model) not in fake_safelist

    result = _call_script(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--seed_safelist'],
        test_filesystem_cb=test_safelist_callback,
    )
    assert result.exit_code == 0
    assert 'Successfully created safelist file' in result.output


@patch.multiple(
    'code_annotations.find_django',
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
        [],  # No local models to print on stdout.
        [
            MagicMock(_meta=MagicMock(app_label='fake_app_3', object_name='FakeModelC')),
            MagicMock(_meta=MagicMock(app_label='fake_app_4', object_name='FakeModelD')),
        ],
    ),
])
def test_listing_local_models(local_models, non_local_models, **kwargs):
    """
    Test the success case for listing local models.
    """
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        local_models,
        non_local_models,
    )
    result = _call_script(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--list_local_models']
    )
    assert result.exit_code == 0
    if not local_models:
        assert 'No local models requiring annotations.' in result.output
    else:
        assert 'Listing {} local models requiring annotations'.format(len(local_models)) in result.output
