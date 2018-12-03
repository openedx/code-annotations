"""
Tests for the extension base classes
"""

import re

import pytest

from code_annotations.extensions.base import AnnotationExtension, SimpleRegexAnnotationExtension
from code_annotations.helpers import VerboseEcho


class FakeExtension(SimpleRegexAnnotationExtension):
    extension_name = 'fake_extension'

    lang_comment_definition = {
        'multi_start': re.escape('foo'),
        'multi_end': re.escape('bar'),
        'single': re.escape('baz')
    }


def test_annotation_types():
    """
    Confirm that all of the good annotation types configure without error
    """
    config = {
        'annotations': {
            'pii': [
                '.. pii::',
                {'.. pii_types::': {'choices': ['id', 'name', 'other']}},
                {'.. pii_retirement::': {'choices': ['retained', 'local_api', 'consumer_api', 'third_party']}}
            ],
            'nopii': '.. no_pii::',
            'ignored': {'.. ignored::': {'choices': ['irrelevant', 'terrible', 'silly-silly']}}
        }
    }

    FakeExtension(config, VerboseEcho())


def test_bad_annotation_type():
    """
    Confirm bad annotation types throw a TypeError
    """
    config = {
        'annotations': {
            'pii': object()
        }
    }

    with pytest.raises(TypeError):
        AnnotationExtension(config, None)


def test_bad_annotation_group_type():
    """
    Confirm bad annotation group types throw a TypeError
    """
    config = {
        'annotations': {
            'pii': [
                '.. pii::',
                '.. no_pii::',
                list()
            ]
        }
    }

    with pytest.raises(TypeError):
        SimpleRegexAnnotationExtension(config, None)


def test_validate():
    """
    Validate doesn't do anything yet, just make sure it doesn't throw any errors
    """
    r = FakeExtension({'annotations': []}, VerboseEcho())
    assert r.validate(None)


def test_nothing_found():
    """
    Make sure nothing fails when no annotation is found.
    """
    r = FakeExtension({'annotations': []}, VerboseEcho())
    with open('tests/extensions/base_test_files/empty.foo') as f:
        r.search(f)
