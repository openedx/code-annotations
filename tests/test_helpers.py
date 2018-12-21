"""
Tests for code_annotations.helpers that don't get exercised elsewhere.
"""
from collections import OrderedDict

import pytest
from click.testing import CliRunner

from code_annotations.helpers import (
    add_annotation_group,
    generate_annotation_regex_from_config,
    yaml_ordered_dump,
    yaml_ordered_load
)


def test_yaml_ordered_round_trip():
    data_to_dump = OrderedDict()
    data_to_dump['a'] = 'A'
    data_to_dump['b'] = 'B'
    data_to_dump['c'] = 'C'
    data_to_dump['d'] = 'D'
    data_to_dump['e'] = 'E'
    data_to_dump['f'] = 'F'

    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('out.yml', 'w') as out_file:
            yaml_ordered_dump(data_to_dump, out_file)

        with open('out.yml', 'r') as in_file:
            loaded_data = yaml_ordered_load(in_file)

    assert data_to_dump == loaded_data


def test_add_annotation_group():
    annotation_tokens = []
    annotation_regexes = []

    # Test simple string and dict, should succeed
    group_1 = [
        {'foo': 'foo_1'},
        {'bar': {'bar_1': 'bar_1_a', 'bar_2': 'bar_2_a'}},
        'baz'
    ]
    add_annotation_group(annotation_tokens, annotation_regexes, group_1)

    assert len(annotation_tokens) == 3
    assert len(annotation_regexes) == 3

    # Test with an unknown type, should throw an exception
    group_2 = [
        ['bing', 'bong']
    ]

    with pytest.raises(TypeError):
        add_annotation_group(annotation_tokens, annotation_regexes, group_2)

    assert len(annotation_tokens) == 3
    assert len(annotation_regexes) == 3


def test_regex_from_config_err():
    config = {
        'annotations': {
            'nopii': '.. no_pii::',
            'pii': [
                '.. pii::',
                {'.. pii_types::': {'choices': ['id', 'name', 'other']}},
                {'.. pii_retirement::': {'choices': ['retained', 'local_api', 'consumer_api', 'third_party']}}
            ],
            'ignored': {'.. ignored::': {'choices': ['irrelevant', 'terrible', 'silly-silly']}},
            'NOT_A_VALID_TYPE': set()
        },
        'report_path': 'test_reports',
        'safelist_path': 'fake_safelist_path.yaml',
        'verbosity': 3
    }

    with pytest.raises(TypeError):
        generate_annotation_regex_from_config(config)
