"""
Tests for the extension base classes
"""

import re

from code_annotations.extensions.base import SimpleRegexAnnotationExtension
from code_annotations.helpers import VerboseEcho
from tests.helpers import FakeConfig


class FakeExtension(SimpleRegexAnnotationExtension):
    extension_name = 'fake_extension'

    lang_comment_definition = {
        'multi_start': re.escape('foo'),
        'multi_end': re.escape('bar'),
        'single': re.escape('baz')
    }


def test_nothing_found():
    """
    Make sure nothing fails when no annotation is found.
    """
    config = FakeConfig()

    r = FakeExtension(config, VerboseEcho())
    with open('tests/extensions/base_test_files/empty.foo') as f:
        r.search(f)
