"""
Stevedore extension for static annotation searching in Javascript files.
"""
import re

from code_annotations.extensions.base import SimpleRegexAnnotationExtension


class JavascriptAnnotationExtension(SimpleRegexAnnotationExtension):
    """
    Annotation extension for Javascript source files.
    """

    extension_name = 'javascript'

    lang_comment_definition = {
        'multi_start': re.escape('/*'),
        'multi_end': re.escape('*/'),
        'single': re.escape('//')
    }
