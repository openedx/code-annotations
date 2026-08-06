"""
Stevedore extension for static annotation searching in Python files.
"""
import re

from code_annotations.extensions.base import SimpleRegexAnnotationExtension


class PythonAnnotationExtension(SimpleRegexAnnotationExtension):
    """
    Annotation extension for Python source files.
    """

    extension_name = 'python'

    lang_comment_definition = {
        'multi_start': re.escape('"""'),
        'multi_end': re.escape('"""'),
        'single': re.escape('#')
    }
