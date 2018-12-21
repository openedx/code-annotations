"""
Annotation searcher for Django model comment searching Django introspection.
"""
import inspect
import os
import pprint
import re

from six import text_type

from code_annotations.base import BaseSearch
from code_annotations.django_reporting_helpers import get_model_id, get_models_requiring_annotations
from code_annotations.helpers import (
    fail,
    generate_annotation_regex_from_config,
    get_annotation_regex,
    yaml_ordered_dump,
    yaml_ordered_load
)

DEFAULT_SAFELIST_FILE_PATH = '.pii_safe_list.yml'


class DjangoSearch(BaseSearch):
    """
    Handles Django model comment searching for annotations.
    """

    def __init__(self, config, report_path, verbosity):
        """
        Initialize for DjangoSearch.

        Args:
            config: Configuration file path
            report_path: Directory to write the report file to
            verbosity: Integer representing verbosity level (0-3)
        """
        super(DjangoSearch, self).__init__(config, report_path, verbosity)
        self.local_models, self.non_local_models = get_models_requiring_annotations()

    def seed_safelist(self):
        """
        Seed a new safelist file with all non-local models that need to be vetted.
        """
        self.config.setdefault('safelist_path', DEFAULT_SAFELIST_FILE_PATH)

        if os.path.exists(self.config['safelist_path']):
            fail('{} already exists, not overwriting.'.format(self.config['safelist_path']))

        self.echo(
            'Found {} non-local models requiring annotations. Adding them to safelist.'.format(
                len(self.non_local_models))
        )

        safelist_data = {get_model_id(model): {} for model in self.non_local_models}

        with open(self.config['safelist_path'], 'w') as safelist_file:
            yaml_ordered_dump(safelist_data, stream=safelist_file)

        self.echo('Successfully created safelist file "{}".'.format(self.config['safelist_path']))
        self.echo('Now, you need to:')
        self.echo('  1) Make sure that any un-annotated models in the safelist are annotated, and')
        self.echo('  2) Annotate any LOCAL models (see --list_local_models).')

    def list_local_models(self):
        """
        Dump a list of models in the local code tree that need annotations to stdout.
        """
        if self.local_models:
            self.echo(
                'Listing {} local models requiring annotations:'.format(len(self.local_models))
            )
            pprint.pprint(sorted([get_model_id(model) for model in self.local_models]), indent=4)
        else:
            self.echo('No local models requiring annotations.')

    def search(self):
        """
        Introspect the configured Django model docstrings for annotations.

        Returns:
            Dict of all found annotations keyed by filename
        """
        if os.path.exists(self.config['safelist_path']):
            self.echo('Found safelist at {}. Reading.'.format(self.config['safelist_path']))
            with open(self.config['safelist_path']) as safelist_file:
                safelisted_models = yaml_ordered_load(safelist_file)
        else:
            raise Exception('Safelist not found! Generate one with the --seed_safelist command.')

        annotation_tokens, annotation_regexes = generate_annotation_regex_from_config(self.config)
        query = get_annotation_regex(annotation_regexes)

        annotated_models = {}

        # Walk all models and their parents looking for annotations
        # TODO: Untangle this nest
        # pylint: disable=too-many-nested-blocks
        for model in self.local_models.union(self.non_local_models):
            model_id = get_model_id(model)
            hierarchy = inspect.getmro(model)
            model_annotations = []

            # See if any annotations exist in the docstring
            for obj in hierarchy:
                if obj.__doc__ is not None:
                    if any(anno in obj.__doc__ for anno in annotation_tokens):
                        # Read in the source file to get the line number
                        filename = inspect.getsourcefile(obj)
                        with open(filename, 'r') as file_handle:
                            txt = file_handle.read()

                        for inner_match in re.finditer(query, obj.__doc__):
                            # TODO: This is duplicated code with extensions/base.py
                            # No matter how long the regex is, there should only be 2 non-None items,
                            # with the first being the annotation token and the 2nd being the comment.
                            cleaned_groups = [item for item in inner_match.groups() if item is not None]

                            if len(cleaned_groups) != 2:  # pragma: no cover
                                raise Exception('{}: Number of found items in the list is not 2. Found: {}'.format(
                                    get_model_id(obj),
                                    cleaned_groups
                                ))

                            annotation, comment = cleaned_groups

                            # Get the line number by counting newlines + 1 (for the first line).
                            # Note that this is the line number of the beginning of the comment, not the
                            # annotation token itself. We find based on the entire code content of the model
                            # as that seems to be the only way to be sure we're getting the correct line number.
                            # It is slow and should be replaced if we can find a better way that is accurate.
                            line = txt.count('\n', 0, txt.find(inspect.getsource(obj))) + 1

                            model_annotations.append({
                                'found_by': "django",
                                'filename': filename,
                                'line_number': line,
                                'annotation_token': annotation.strip(),
                                'annotation_data': comment.strip(),
                                'extra': {
                                    'object_id': model_id,
                                    'full_comment': obj.__doc__.strip()
                                }
                            })
            if model_annotations:
                if model_id in safelisted_models:
                    self._add_error("{} is annotated, but also in the safelist.".format(model_id))
                self.format_file_results(annotated_models, [model_annotations])
            elif model_id not in safelisted_models:
                self._add_error("{} is not annotated and not in the safelist!".format(model_id))
            else:
                if not safelisted_models[model_id]:
                    self._add_error("{} is in the safelist but has no annotations!".format(model_id))
                for annotation in safelisted_models[model_id]:
                    comment = safelisted_models[model_id][annotation]
                    model_annotations.append({
                        'found_by': "safelist",
                        'filename': self.config['safelist_path'],
                        'line_number': 0,
                        'annotation_token': annotation.strip(),
                        'annotation_data': comment.strip(),
                        'extra': {
                            'object_id': model_id,
                            'full_comment': text_type(safelisted_models[model_id])
                        }
                    })
                self.format_file_results(annotated_models, [model_annotations])
        return annotated_models
