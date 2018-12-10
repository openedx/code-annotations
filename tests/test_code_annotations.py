#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for the `code-annotations` module.
"""
from __future__ import absolute_import, unicode_literals

import os

import pytest
from click.testing import CliRunner
from mock import DEFAULT, patch

from code_annotations.cli import entry_point

FAKE_SAFELIST_PATH = 'fake_safelist_path.yaml'

FAKE_CONFIG_FILE = """
safelist_path: {fake_safelist_path}
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
    'code_annotations.cli',
    get_models_requiring_annotations=DEFAULT,
)
@pytest.mark.parametrize("local_model_ids,non_local_model_ids", [
    (
        [
            'fake_app_1.FakeModelA',
            'fake_app_2.FakeModelB',
        ],
        [
            'fake_app_3.FakeModelC',
            'fake_app_4.FakeModelD',
        ],
    ),
    (
        [
            'fake_app_1.FakeModelA',
            'fake_app_2.FakeModelB',
        ],
        [],  # No non-local models to add to the safelist.
    ),
])
def test_seeding_safelist(local_model_ids, non_local_model_ids, **kwargs):
    """
    Test the success case for seeding the safelist.
    """
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        local_model_ids,
        non_local_model_ids,
    )

    def test_safelist_callback():
        assert os.path.exists(FAKE_SAFELIST_PATH)
        with open(FAKE_SAFELIST_PATH, 'r') as fake_safelist_file:
            fake_safelist = fake_safelist_file.read()
        for model_id in non_local_model_ids:
            assert model_id in fake_safelist
        for model_id in local_model_ids:
            assert model_id not in fake_safelist

    result = _call_script(
        ['pii_report_django', '--config_file', 'test_config.yml', '--seed_safelist'],
        test_filesystem_cb=test_safelist_callback,
    )
    assert result.exit_code == 0
    assert 'Successfully created safelist file' in result.output


@patch.multiple(
    'code_annotations.cli',
    get_models_requiring_annotations=DEFAULT,
)
@pytest.mark.parametrize("local_model_ids,non_local_model_ids", [
    (
        [
            'fake_app_1.FakeModelA',
            'fake_app_2.FakeModelB',
        ],
        [
            'fake_app_3.FakeModelC',
            'fake_app_4.FakeModelD',
        ],
    ),
    (
        [],  # No local models to print on stdout.
        [
            'fake_app_3.FakeModelC',
            'fake_app_4.FakeModelD',
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
    )
    result = _call_script(
        ['pii_report_django', '--config_file', 'test_config.yml', '--list_local_models']
    )
    assert result.exit_code == 0
    if not local_model_ids:
        assert 'No local models requiring annotations.' in result.output
    else:
        assert 'Listing {} local models requiring annotations'.format(len(local_model_ids)) in result.output
