"""
Stevedore extension for static annotation searching in javascript files.
"""

from .base import AnnotationExtension


# TODO: Make this work.
class JavascriptAnnotationExtension(AnnotationExtension):
    """
    Annotation extension for Javascript source files.
    """

    extension_name = 'javascript'

    def validate(self, file_handle):
        """
        Validate that any annotations in the given file are properly formatted.

        Args:
            file_handle: Open file handle for the file to validate, set to beginning of the file

        Returns:
            Tuple of (success, list strings describing reasons for failure)
        """
        return True

    def search(self, file_handle):
        """
        Search for annotations in the given file.

        Args:
            file_handle: Open file handle for the file to validate, set to beginning of the file

        Returns:
            List of dicts describing found annotations, or an empty list
        """
        return []
