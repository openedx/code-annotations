"""
Tests for the extension base classes
"""

import re

from code_annotations.extensions.base import SimpleRegexAnnotationExtension
from code_annotations.helpers import VerboseEcho
from tests.helpers import FakeConfig


class FakeExtension(SimpleRegexAnnotationExtension):
    extension_name: str = 'fake_extension'

    lang_comment_definition: dict[str, str] = {
        'multi_start': re.escape('foo'),
        'multi_end': re.escape('bar'),
        'single': re.escape('baz')
    }


def test_nothing_found() -> None:
    """
    Make sure nothing fails when no annotation is found.
    """
    config = FakeConfig()

    r = FakeExtension(config, VerboseEcho())
    with open('tests/extensions/base_test_files/empty.foo') as f:
        r.search(f)


def test_strip_single_line_comment_tokens() -> None:
    config = FakeConfig()

    extension = FakeExtension(config, VerboseEcho())
    text = """baz line1
  baz line2
bazline3
baz   line4"""
    expected_result = """ line1
 line2
line3
   line4"""
    # pylint: disable=protected-access
    assert expected_result == extension._strip_single_line_comment_tokens(text)
