"""
Tests for the StaticSearch/DjangoSearch API.
"""

from code_annotations import annotation_errors
from code_annotations.base import AnnotationConfig
from code_annotations.find_static import StaticSearch


def test_annotation_errors():
    config = AnnotationConfig(
        "tests/test_configurations/.annotations_test",
        verbosity=-1,
        source_path_override="tests/extensions/python_test_files/choice_failures_1.pyt",
    )
    search = StaticSearch(config)
    results = search.search()
    search.check_results(results)

    # The first error should be an invalid choice error
    annotation, error_type, args = search.annotation_errors[0]
    assert {
        "annotation_data": ["doesnotexist"],
        "annotation_token": ".. ignored:",
        "filename": "choice_failures_1.pyt",
        "found_by": "python",
        "line_number": 1,
    } == annotation
    assert annotation_errors.InvalidChoice == error_type
    assert (
        "doesnotexist",
        ".. ignored:",
        ["irrelevant", "terrible", "silly-silly"],
    ) == args


def test_annotation_errors_ordering():
    # You should modify the value below every time a new annotation error type is added.
    assert 6 == len(annotation_errors.TYPES)
    # The value below must not be modified, ever. The number of annotation error types should NEVER exceed 10. Read the
    # module docs for more information.
    assert len(annotation_errors.TYPES) < 10
    # This is just to check that the ordering of the annotation error types does not change. You should not change this
    # test, but eventually add your own below.
    assert annotation_errors.MissingToken == annotation_errors.TYPES[5]
