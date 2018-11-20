"""
Abstract and base classes to support plugins.
"""


class AnnotationExtension(object):
    """
    Abstract base class that annotation extensions will inherit from.
    """

    def __init__(self, config, echo):
        """
        Initialize this base object, save a handle to configuration.

        Args:
            config: The configuration object
            echo: VerboseEcho object used for logging
        """
        self.config = config
        self.ECHO = echo

    def validate(self, file_handle):
        """
        Validate that any annotations in the given file are properly formatted.
        """
        raise NotImplementedError('validate called on base class!')

    def search(self, file_handle):
        """
        Search for annotations in the given file.
        """
        raise NotImplementedError('search called on base class!')
