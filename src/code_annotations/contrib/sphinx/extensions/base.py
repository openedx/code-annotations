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
        config_path, verbosity=-1, source_path_override=source_path
    )
    search = StaticSearch(config)
    all_results = search.search()
    toggles = {}
    for filename in all_results:
        for annotations in search.iter_groups(all_results[filename]):
            current_entry = {}
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
