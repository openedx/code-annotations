"""
Tests for the Python static extension
"""
import pytest

from code_annotations.base import AnnotationConfig
from code_annotations.extensions.python import PythonAnnotationExtension
from code_annotations.helpers import VerboseEcho
from tests.helpers import EXIT_CODE_FAILURE, EXIT_CODE_SUCCESS, call_script


@pytest.mark.parametrize('test_file,expected_exit_code,expected_message', [
    ('simple_success.pyt', EXIT_CODE_SUCCESS, 'Search found 20 annotations in'),
    ('group_ordering_1.pyt', EXIT_CODE_SUCCESS, 'Search found 3 annotations in'),
    ('group_ordering_2.pyt', EXIT_CODE_SUCCESS, 'Search found 9 annotations in'),
    ('group_failures_1.pyt', EXIT_CODE_FAILURE, 'File("group_failures_1.pyt") finished with an incomplete group'),
    ('group_failures_2.pyt', EXIT_CODE_FAILURE, 'File("group_failures_2.pyt") finished with an incomplete group'),
    ('choice_failures_1.pyt', EXIT_CODE_FAILURE, '"doesnotexist" is not a valid choice for ".. ignored:"'),
    ('choice_failures_2.pyt', EXIT_CODE_FAILURE, '"doesnotexist" is not a valid choice for ".. ignored:"'),
    ('choice_failures_3.pyt', EXIT_CODE_FAILURE, '"terrible|silly-silly" is not a valid choice for ".. ignored:"'),
    ('choice_failures_4.pyt', EXIT_CODE_FAILURE, '"terrible" is already present in this annotation'),
    ('choice_failures_5.pyt', EXIT_CODE_FAILURE, 'No choices found for ".. ignored:"'),
])
def test_grouping_and_choice_failures(test_file, expected_exit_code, expected_message):
    result = call_script((
        'static_find_annotations',
        '--config_file',
        'tests/test_configurations/.annotations_test',
        '--source_path=tests/extensions/python_test_files/' + test_file,
        '-vv'
    ))
    assert result.exit_code == expected_exit_code
    assert expected_message in result.output

    if expected_exit_code == EXIT_CODE_FAILURE:
        assert "Search failed due to linting errors!" in result.output


@pytest.mark.parametrize('test_file,annotations', [
    (
        'multiline_simple.pyt',
        [
            ('.. pii:', """A long description that
  spans multiple
  lines"""),
            ('.. pii_types:', 'id, name'),
        ]
    ),
    (
        'multiline_indented.pyt',
        [
            ('.. pii:', """A long description that
        spans multiple indented
        lines"""),
            ('.. pii_types:', 'id, name'),
        ]
    ),
    (
        'multiline_empty_first_line.pyt',
        [
            ('.. pii:', """This is an annotation that
  spans multiple lines and allows developers to
  write more extensive docs."""),
        ]
    ),
    (
        'multiline_paragraphs.pyt',
        [
            ('.. pii:', """This is an annotation that
  spans multiple paragraphs.

  This allows developers to write even more
  extensive docs."""),
            ('.. pii:', """Annotation 1 with:

     Multi-line and multi-paragraph.""")
        ]
    ),
    (
        'multiline_singlelinecomment.pyt',
        [
            ('.. pii:', """A long description that
  spans multiple
  lines"""),
            ('.. pii_types:', 'id, name'),
        ]
    ),
])
def test_multi_line_annotations(test_file, annotations):
    config = AnnotationConfig('tests/test_configurations/.annotations_test')
    annotator = PythonAnnotationExtension(config, VerboseEcho())

    with open(f'tests/extensions/python_test_files/{test_file}') as fi:
        result_annotations = annotator.search(fi)

    assert len(annotations) == len(result_annotations)
    for annotation, result_annotation in zip(annotations, result_annotations):
        assert result_annotation['annotation_token'] == annotation[0]
        assert result_annotation['annotation_data'] == annotation[1]
