"""
Annotation searcher for static comment searching via Stevedore plugins.
"""

import os

from code_annotations.base import BaseSearch


class StaticSearch(BaseSearch):
    """
    Handles static code searching for annotations.
    """

    def search_extension(self, ext, file_handle, file_extensions_map, filename_extension):
        """
        Execute a search on the given file using the given extension.

        Args:
            ext: Extension to execute the search on
            file_handle: An open file handle search
            file_extensions_map: Dict mapping of extension names to configured filename extensions
            filename_extension: The filename extension of the file being searched

        Returns:
            Tuple of (extension name, list of found annotation dicts)
        """
        # Only search this file if we are configured for its extension
        if filename_extension in file_extensions_map[ext.name]:
            # Reset the read handle to the beginning of the file in case another
            # extension moved it
            file_handle.seek(0)

            ext_results = ext.obj.search(file_handle)

            if ext_results:
                return ext.name, ext_results

        return ext.name, None

    def _search_one_file(self, full_name, known_extensions, file_extensions_map, all_results):
        """
        Perform an annotation search on a single file, using all extensions it is configured for.

        Args:
            full_name: Complete filename
            known_extensions: List of all file name extensions we are configured to work on
            file_extensions_map: Mapping of file name extensions to Stevedore extensions
            all_results: A dict of annotations returned from search()
        """
        filename_extension = os.path.splitext(full_name)[1][1:]

        if filename_extension not in known_extensions:
            self.echo.echo_vvv(
                f"{filename_extension} is not a known extension, skipping ({full_name})."
            )
            return

        self.echo.echo_vvv(full_name)

        # TODO: This should probably be a generator so we don't have to store all results in memory
        with open(full_name) as file_handle:
            # Call search_extension on all loaded extensions
            results = self.config.mgr.map(self.search_extension, file_handle, file_extensions_map, filename_extension)

            # Strip out plugin name, as it's already in the annotation
            results = [r for _, r in results]

            # Format and add the results to our running full set
            self.format_file_results(all_results, results)

    def search(self):
        """
        Walk the source tree, send known file types to extensions.

        Returns:
            Dict of all found annotations keyed by filename
        """
        # Index the results by extension name
        file_extensions_map = {}
        known_extensions = set()
        for extension_name in self.config.extensions:
            file_extensions_map[extension_name] = self.config.extensions[extension_name]
            known_extensions.update(self.config.extensions[extension_name])

        all_results = {}

        if os.path.isfile(self.config.source_path):
            self._search_one_file(self.config.source_path, known_extensions, file_extensions_map, all_results)
        else:
            for root, _, files in os.walk(self.config.source_path):
                for filename in files:
                    full_name = os.path.join(root, filename)
                    self._search_one_file(full_name, known_extensions, file_extensions_map, all_results)

        return all_results
