"""
Tests for code_annotations.helpers that don't get exercised elsewhere.
"""
from collections import OrderedDict

from click.testing import CliRunner

from code_annotations.helpers import yaml_ordered_dump, yaml_ordered_load


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
