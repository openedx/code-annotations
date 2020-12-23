"""
Base utilities for building annotation-based Sphinx extensions.
"""


from code_annotations.base import AnnotationConfig
from code_annotations.find_static import StaticSearch


def find_annotations(source_path, config_path, group_by_key):
    """
    Find the feature toggles as defined in the configuration file.

    Return:
        toggles (dict): feature toggles indexed by name.
    """
    config = AnnotationConfig(
        config_path, verbosity=0, source_path_override=source_path
    )
    results = StaticSearch(config).search()

    toggles = {}
    current_entry = {}
    for filename, entries in results.items():
        for entry in entries:
            key = entry["annotation_token"]
            value = entry["annotation_data"]
            if key == group_by_key:
                toggle_name = value
                toggles[toggle_name] = {
                    "filename": filename,
                    "line_number": entry["line_number"],
                }
                current_entry = toggles[toggle_name]
            else:
                current_entry[key] = value

    return toggles


def quote_value(value):
    """
    Quote a Python object if it is string-like.
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
