#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for the `code-annotations` module.
"""
from __future__ import absolute_import, unicode_literals

import os

from click.testing import CliRunner
from code_annotations.cli import cli
from mock import DEFAULT, patch

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
            cli,
            args=[
                '--config_file', 'test_config.yml',
            ] + args_list
        )
        if test_filesystem_cb:
            test_filesystem_cb()
    print(result)
    print(result.output)
    return result


@patch.multiple(
    'code_annotations.cli',
    get_models_requiring_annotations=DEFAULT,
)
def test_seeding_safelist(**kwargs):
    """
    """
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    local_model_ids = [
        'fake_app_1.FakeModelA',
        'fake_app_2.FakeModelB',
    ]
    non_local_model_ids = [
        'fake_app_3.FakeModelC',
        'fake_app_4.FakeModelD',
    ]
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
        ['pii_report_django', '--seed_safelist'],
        test_filesystem_cb=test_safelist_callback,
    )
    assert result.exit_code == 0
    assert 'Successfully created safelist file' in result.output
