"""
Stevedore extension for static annotation searching in any plain text file.
"""

import re

import six

from code_annotations.extensions.base import AnnotationExtension
from code_annotations.helpers import clean_abs_path


class PlaintextAnnotationExtension(AnnotationExtension):
    """
    Extension for any type of text files.
    """

    extension_name = 'plaintext'

    def __init__(self, config, echo):
        """
        Set up the extension, create the regex used to do searches.

        Args:
            config: The configuration dict
            echo: VerboseEcho object for logging
        Returns:
            None
        """
        super(PlaintextAnnotationExtension, self).__init__(config, echo)

        strings_to_search = []
        annotation_tokens = config['annotations']

        # Take the configured annotations and turn them into a regex for our search

        # TODO: Refactor this wall of text and extend to enforce groups
        for annotation_or_group in annotation_tokens:
            if isinstance(annotation_tokens[annotation_or_group], six.string_types):
                strings_to_search.append(annotation_tokens[annotation_or_group])
            elif isinstance(annotation_tokens[annotation_or_group], (list, tuple)):
                group = annotation_tokens[annotation_or_group]
                for annotation in group:
                    if isinstance(annotation, six.string_types):
                        strings_to_search.append(annotation)
                    elif isinstance(annotation, dict):
                        strings_to_search.append(list(annotation.keys())[0])
                    else:
                        raise TypeError('{} is an unknown type. Annotations must be strings or list/tuples.'.format(
                            annotation_tokens[annotation_or_group])
                        )
            else:
                raise TypeError('{} is an unknown type. Annotations must be strings or list/tuples.'.format(
                    annotation_tokens[annotation_or_group])
                )

        self.query = r'{}'.format('|'.join(strings_to_search))

        self.ECHO.echo_v("Plaintext extension regex query: {}".format(self.query))

    def validate(self, file_handle):
        """
        Validate any annotations in the given file are properly formatted.

        Args:
            file_handle: Open file handle for the file to validate

        Returns:
            Tuple of (success, list strings describing reasons for failure)
        """
        # TODO: Implement!
        return True

    def search(self, file_handle):
        """
        Search for annotations in the given file.

        Args:
            file_handle: Handle for the file to validate

        Returns:
            List of dicts describing found annotations, or an empty list
        """
        txt = file_handle.read()
        found_annotations = []

        # Fast out if no annotations exist in the file
        if re.search(self.query, txt):
            line_num = 0
            for line in txt.splitlines():
                line_num += 1
                for m in re.finditer(self.query, line):
                    token = line[m.start():m.end()].strip()
                    substring = line[m.end():None].strip()

                    found_annotations.append({
                        'found_by': self.extension_name,
                        'filename': clean_abs_path(file_handle.name, self.config['source_path']),
                        'line_number': line_num,
                        'annotation_token': token,
                        'annotation_data': substring
                    })

        return found_annotations
