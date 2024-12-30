"""
Expose contrib configuration file paths as Python variables, for use in 3rd-party utilities.
"""
import importlib.resources
import os

FEATURE_TOGGLE_ANNOTATIONS_CONFIG_PATH = importlib.resources.files(
    "code_annotations") / os.path.join("contrib", "config", "feature_toggle_annotations.yaml")

SETTING_ANNOTATIONS_CONFIG_PATH = importlib.resources.files(
    "code_annotations") / os.path.join("contrib", "config", "setting_annotations.yaml")

OPENEDX_EVENTS_ANNOTATIONS_CONFIG_PATH = importlib.resources.files(
    "code_annotations") / os.path.join("contrib", "config", "openedx_events_annotations.yaml")
