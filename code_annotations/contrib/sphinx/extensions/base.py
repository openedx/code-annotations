"""
Base utilities for building annotation-based Sphinx extensions.
"""

import typing as t

from code_annotations.base import AnnotationConfig
from code_annotations.find_static import StaticSearch


def find_annotations(
    source_path: str,
    config_path: str | t.Any,
    group_by_key: str
) -> dict[str, dict[str, t.Any]]:
    """
    Find the feature toggles as defined in the configuration file.

    Args:
        source_path: Path to the source code to search
        config_path: Path to the configuration file or a Traversable object
        group_by_key: Key in annotations to group by

    Returns:
        Toggles indexed by name
    """
    config = AnnotationConfig(
        str(config_path), verbosity=-1, source_path_override=source_path
    )
    search = StaticSearch(config)
    all_results = search.search()
    toggles: dict[str, dict[str, t.Any]] = {}
    for filename in all_results:
        for annotations in search.iter_groups(all_results[filename]):
            current_entry: dict[str, t.Any] = {}
            for annotation in annotations:
                key = annotation["annotation_token"]
                value = annotation["annotation_data"]
                if key == group_by_key:
                    toggle_name = value
                    toggles[toggle_name] = current_entry
                    current_entry["filename"] = filename
                    current_entry["line_number"] = annotation["line_number"]
                else:
                    current_entry[key] = value

    return toggles


def quote_value(value: t.Any) -> str:
    """
    Quote a Python object if it is string-like.

    Args:
        value: Value to potentially quote

    Returns:
        Quoted string if the value is string-like, otherwise str representation
    """
    if value in ("True", "False", "None"):
        return str(value)
    try:
        float(value)
        return str(value)
    except ValueError:
        pass
    if isinstance(value, str):
        return f'"{value}"'
    return str(value)
