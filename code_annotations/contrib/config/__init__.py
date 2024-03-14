"""
Expose contrib configuration file paths as Python variables, for use in 3rd-party utilities.
"""
import os

import pkg_resources

FEATURE_TOGGLE_ANNOTATIONS_CONFIG_PATH = pkg_resources.resource_filename(
    "code_annotations",
    os.path.join("contrib", "config", "feature_toggle_annotations.yaml"),
)
SETTING_ANNOTATIONS_CONFIG_PATH = pkg_resources.resource_filename(
    "code_annotations",
    os.path.join("contrib", "config", "setting_annotations.yaml"),
)
OPENEDX_EVENTS_ANNOTATIONS_CONFIG_PATH = pkg_resources.resource_filename(
    "code_annotations",
    os.path.join("contrib", "config", "openedx_events_annotations.yaml"),
)
