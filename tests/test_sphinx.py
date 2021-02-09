"""
Test sphinx extensions.
"""
from code_annotations.contrib.sphinx.extensions.base import find_annotations, quote_value


def test_collect_pii_for_sphinx():
    annotations = find_annotations(
        "tests/extensions/python_test_files/simple_success.pyt",
        "tests/test_configurations/.annotations_test",
        ".. pii:",
    )
    assert {
        ".. pii_types:": ["id", "name"],
        ".. pii_retirement:": ["local_api", "consumer_api"],
        "filename": "simple_success.pyt",
        "line_number": 1,
    } == annotations["Annotation 1"]

    assert {
        ".. pii_types:": ["id", "name"],
        ".. pii_retirement:": ["local_api", "consumer_api"],
        "filename": "simple_success.pyt",
        "line_number": 11,
    } == annotations["Annotation 2"]

    assert 5 == len(annotations)


def test_quote_value():
    assert "True" == quote_value("True")
    assert "None" == quote_value("None")
    assert "1" == quote_value("1")
    assert "1.414" == quote_value("1.414")
    assert '"some string"' == quote_value("some string")
