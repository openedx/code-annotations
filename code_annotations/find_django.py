"""
Annotation searcher for Django model comment searching Django introspection.
"""
import inspect
import os
import pprint
import re
import sys

import django
from django.apps import apps
from django.db import models
from six import text_type

from code_annotations.base import BaseSearch
from code_annotations.helpers import fail, get_annotation_regex, yaml_ordered_dump, yaml_ordered_load

DEFAULT_SAFELIST_FILE_PATH = '.annotation_safe_list.yml'


class DjangoSearch(BaseSearch):
    """
    Handles Django model comment searching for annotations.
    """

    def __init__(self, config):
        """
        Initialize for DjangoSearch.

        Args:
            config: Configuration file path
        """
        super(DjangoSearch, self).__init__(config)
        self.local_models, self.non_local_models = self.get_models_requiring_annotations()

    def seed_safelist(self):
        """
        Seed a new safelist file with all non-local models that need to be vetted.
        """
        if os.path.exists(self.config.safelist_path):
            fail('{} already exists, not overwriting.'.format(self.config.safelist_path))

        self.echo(
            'Found {} non-local models requiring annotations. Adding them to safelist.'.format(
                len(self.non_local_models))
        )

        safelist_data = {self.get_model_id(model): {} for model in self.non_local_models}

        with open(self.config.safelist_path, 'w') as safelist_file:
            yaml_ordered_dump(safelist_data, stream=safelist_file)

        self.echo('Successfully created safelist file "{}".'.format(self.config.safelist_path))
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
            pprint.pprint(sorted([self.get_model_id(model) for model in self.local_models]), indent=4)
        else:
            self.echo('No local models requiring annotations.')

    def search(self):
        """
        Introspect the configured Django model docstrings for annotations.

        Returns:
            Dict of all found annotations keyed by filename
        """
        if os.path.exists(self.config.safelist_path):
            self.echo('Found safelist at {}. Reading.'.format(self.config.safelist_path))
            with open(self.config.safelist_path) as safelist_file:
                safelisted_models = yaml_ordered_load(safelist_file)
        else:
            raise Exception('Safelist not found! Generate one with the --seed_safelist command.')

        annotation_tokens = self.config.annotation_tokens
        annotation_regexes = self.config.annotation_regexes
        query = get_annotation_regex(annotation_regexes)

        annotated_models = {}

        # Walk all models and their parents looking for annotations
        # TODO: Untangle this nest
        # pylint: disable=too-many-nested-blocks
        for model in self.local_models.union(self.non_local_models):
            model_id = self.get_model_id(model)
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
                                    self.get_model_id(obj),
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
                        'filename': self.config.safelist_path,
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

    @staticmethod
    def requires_annotations(model):
        """
        Return true if the given model actually requires annotations, according to PLAT-2344.
        """
        # Anything inheriting from django.models.Model will have a ._meta attribute. Our tests
        # inherit from object, which doesn't have it, and will fail below. This is a quick way
        # to early out on both.
        if not hasattr(model, '_meta'):
            return False

        return issubclass(model, models.Model) \
            and not (model is models.Model) \
            and not model._meta.abstract \
            and not model._meta.proxy

    @staticmethod
    def is_non_local(model):
        """
        Determine if the given model is non-local to the current IDA.

        Non-local models are all installed models which are not "local", by
        definition.  "Local" models are installed models which are defined in code
        which physically lives in the current codebase, where "current codebase"
        ostensibly refers to the code providing the currently active django
        project.

        Args:
            model (django.db.models.Model): A model to check.

        Returns:
            bool: True if the given model is non-local.
        """
        # If the model _was_ local to the current IDA repository, it should be
        # defined somewhere under sys.prefix + '/src/' or in a path that points to
        # the current checked-out code.  On Posix systems according to our testing,
        # non-local packages get installed to paths containing either
        # "site-packages" or "dist-packages".
        non_local_path_prefixes = []
        for path in sys.path:
            if 'dist-packages' in path or 'site-packages' in path:
                non_local_path_prefixes.append(path)
        model_source_path = inspect.getsourcefile(model)
        return model_source_path.startswith(tuple(non_local_path_prefixes))

    @staticmethod
    def get_model_id(model):
        """
        Construct the django standard model identifier in "app_label.ModelClassName" notation.

        Args:
            model (django.db.models.Model): A model for which to create an identifier.

        Returns:
            str: identifier string for the given model.
        """
        return '{}.{}'.format(model._meta.app_label, model._meta.object_name)

    @staticmethod
    def setup_django():
        """
        Prepare to make django library function calls.

        On behalf of the current Django project in the current working directory,
        setup/load the django framework, specified settings, and apps therein.
        This should be called before calling any django submodule functions which
        expect apps to be loaded.

        This function is idempotent.
        """
        if sys.path[0] != '':  # pragma: no cover
            sys.path.insert(0, '')
        django.setup()

    @staticmethod
    def get_models_requiring_annotations():
        """
        Determine all local and non-local models via django model introspection.

        Note that non-local models returned may contain 1st party models (authored by
        edX).  This is a compromise in accuracy in order to simplify the generation
        of this list, and also to ease the transition from zero to 100% annotations
        in edX satellite repositories.

        Returns:
            tuple:
                2-tuple where the first item is a set of local models, and the
                second item is a set of non-local models.
        """
        DjangoSearch.setup_django()
        local_models = set()
        non_local_models = set()
        for app in apps.get_app_configs():
            for root_model in app.get_models():
                # getmro() includes the _entire_ inheritance closure, not just the direct inherited classes.
                heirarchy = inspect.getmro(root_model)
                for model in heirarchy:
                    if DjangoSearch.requires_annotations(model):
                        if DjangoSearch.is_non_local(model):
                            non_local_models.add(model)
                        else:
                            local_models.add(model)
        return local_models, non_local_models
