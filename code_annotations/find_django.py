"""
Annotation searcher for Django model comment searching Django introspection.
"""
import inspect
import os
import sys

import django
import yaml
from django.apps import apps
from django.db import models

from code_annotations.base import BaseSearch
from code_annotations.helpers import clean_annotation, fail, get_annotation_regex

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
        super().__init__(config)
        self.local_models, self.non_local_models, total, needing_annotation = self.get_models_requiring_annotations()
        self.model_counts = {
            'total': total,
            'annotated': 0,
            'unannotated': 0,
            'needing_annotation': len(needing_annotation),
            'not_needing_annotation': total - len(needing_annotation),
            'safelisted': 0
        }
        self.uncovered_model_ids = set()
        self.echo.echo_vvv('Local models:\n   ' + '\n   '.join([str(m) for m in self.local_models]) + '\n')
        self.echo.echo_vvv('Non-local models:\n   ' + '\n   '.join([str(m) for m in self.non_local_models]) + '\n')
        self.echo.echo_vv('The following models require annotations:\n   ' + '\n   '.join(needing_annotation) + '\n')

    def _increment_count(self, count_type, incr_by=1):
        self.model_counts[count_type] += incr_by

    def seed_safelist(self):
        """
        Seed a new safelist file with all non-local models that need to be vetted.
        """
        if os.path.exists(self.config.safelist_path):
            fail(f'{self.config.safelist_path} already exists, not overwriting.')

        self.echo(
            'Found {} non-local models requiring annotations. Adding them to safelist.'.format(
                len(self.non_local_models))
        )

        safelist_data = {self.get_model_id(model): {} for model in self.non_local_models}

        with open(self.config.safelist_path, 'w') as safelist_file:
            safelist_comment = """
# This is a Code Annotations automatically-generated Django model safelist file.
# These models must be annotated as follows in order to be counted in the coverage report.
# See https://code-annotations.readthedocs.io/en/latest/safelist.html for more information.
#
# fake_app_1.FakeModelName:
#    ".. no_pii:": "This model has no PII"
# fake_app_2.FakeModel2:
#    ".. choice_annotation:": foo, bar, baz

"""
            safelist_file.write(safelist_comment.lstrip())
            yaml.safe_dump(safelist_data, stream=safelist_file, default_flow_style=False)

        self.echo(f'Successfully created safelist file "{self.config.safelist_path}".', fg='red')
        self.echo('Now, you need to:', fg='red')
        self.echo('  1) Make sure that any un-annotated models in the safelist are annotated, and', fg='red')
        self.echo('  2) Annotate any LOCAL models (see --list_local_models).', fg='red')

    def list_local_models(self):
        """
        Dump a list of models in the local code tree that need annotations to stdout.
        """
        if self.local_models:
            self.echo(
                'Listing {} local models requiring annotations:'.format(len(self.local_models))
            )
            self.echo.pprint(sorted([self.get_model_id(model) for model in self.local_models]), indent=4)
        else:
            self.echo('No local models requiring annotations.')

    def _append_model_annotations(self, model_type, model_id, query, model_annotations):
        """
        Find the given model's annotations in the file and add them to model_annotations.

        Args:
            model_type: The type of model we're searching
            model_id: The text representation of the model name from get_model_id
            query: The regex to run to find annotations in the docstring
            model_annotations: The running list of found annotations in search() that we are to add to
        """
        # Read in the source file to get the line number
        filename = inspect.getsourcefile(model_type)
        with open(filename) as file_handle:
            txt = file_handle.read()

        # Get the line number by counting newlines + 1 (for the first line).
        # Note that this is the line number of the beginning of the comment, not the
        # annotation token itself. We find based on the entire code content of the model
        # as that seems to be the only way to be sure we're getting the correct line number.
        # It is slow and should be replaced if we can find a better way that is accurate.
        line = txt.count('\n', 0, txt.find(inspect.getsource(model_type))) + 1

        for inner_match in query.finditer(model_type.__doc__):
            try:
                annotation_token = inner_match.group('token')
                annotation_data = inner_match.group('data')
            except IndexError as error:
                # pragma: no cover
                raise ValueError('{}: Could not find "data" or "token" groups. Found: {}'.format(
                    self.get_model_id(model_type),
                    inner_match.groupdict()
                )) from error
            annotation_token, annotation_data = clean_annotation(annotation_token, annotation_data)
            model_annotations.append({
                'found_by': "django",
                'filename': filename,
                'line_number': line,
                'annotation_token': annotation_token,
                'annotation_data': annotation_data,
                'extra': {
                    'object_id': model_id,
                    'full_comment': model_type.__doc__.strip()
                }
            })

    def _append_safelisted_model_annotations(self, safelisted_models, model_id, model_annotations):
        """
        Append the safelisted annotations for the given model id to model_annotations.

        Args:
            safelisted_models: The dict of models and their annotations loaded from the safelist
            model_id: The text representation of the model name from get_model_id
            model_annotations: The running list of found annotations in search() that we are to add to
        """
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
                    'full_comment': str(safelisted_models[model_id])
                }
            })

    def _read_safelist(self):
        """
        Read the safelist and return the found models and their annotations.

        Returns:
            The Python representation of the safelist
        """
        if os.path.exists(self.config.safelist_path):
            self.echo(f'Found safelist at {self.config.safelist_path}. Reading.\n')
            with open(self.config.safelist_path) as safelist_file:
                safelisted_models = yaml.safe_load(safelist_file)
            self._increment_count('safelisted', len(safelisted_models))

            if safelisted_models:
                self.echo.echo_vv('   Safelisted models:\n   ' + '\n   '.join(safelisted_models))
            else:
                self.echo.echo_vv('   No safelisted models found.\n')

            return safelisted_models
        else:
            raise Exception('Safelist not found! Generate one with the --seed_safelist command.')

    def search(self):
        """
        Introspect the configured Django model docstrings for annotations.

        Returns:
            Dict of all found annotations keyed by filename
        """
        safelisted_models = self._read_safelist()
        annotation_tokens = self.config.annotation_tokens
        annotation_regexes = self.config.annotation_regexes
        query = get_annotation_regex(annotation_regexes)

        annotated_models = {}

        self.echo.echo_vv('Searching models and their parent classes...')

        # Walk all models and their parents looking for annotations
        for model in self.local_models.union(self.non_local_models):
            model_id = self.get_model_id(model)
            self.echo.echo_vv('   ' + model_id)
            hierarchy = inspect.getmro(model)
            model_annotations = []

            # If any annotations exist in the docstring add them to annotated_models
            for obj in hierarchy:
                if obj.__doc__ is not None:
                    if any(anno in obj.__doc__ for anno in annotation_tokens):
                        self.echo.echo_vvv('      ' + DjangoSearch.get_model_id(obj) + ' has annotations.')
                        self._append_model_annotations(obj, model_id, query, model_annotations)
                    else:
                        # Don't use get_model_id here, as this could be a base class below Model
                        self.echo.echo_vvv('      ' + str(obj) + ' has no annotations.')

            # If there are any annotations in the model, format them
            if model_annotations:
                self.echo.echo_vv("      {} has {} total annotations".format(model_id, len(model_annotations)))
                self._increment_count('annotated')
                if model_id in safelisted_models:
                    self._add_error(f"{model_id} is annotated, but also in the safelist.")
                self.format_file_results(annotated_models, [model_annotations])

            # The model is not in the safelist and is not annotated
            elif model_id not in safelisted_models:
                self._increment_count('unannotated')
                self.uncovered_model_ids.add(model_id)
                self.echo.echo_vv(f"      {model_id} has no annotations")

            # Otherwise it is not annotated and in the safelist
            else:
                if not safelisted_models[model_id]:
                    self.uncovered_model_ids.add(model_id)
                    self.echo.echo_vv(f"      {model_id} is in the safelist.")
                    self._add_error(f"{model_id} is in the safelist but has no annotations!")
                else:
                    self._increment_count('annotated')

                self._append_safelisted_model_annotations(safelisted_models, model_id, model_annotations)
                self.format_file_results(annotated_models, [model_annotations])

        return annotated_models

    def check_coverage(self):
        """
        Perform checking of coverage percentage based on stats collected in setup and search.

        Returns:
            Bool indicating whether or not the number of annotated models covers a percentage
                of total models needing annotations greater than or equal to the configured
                coverage_target.
        """
        self.echo("\nModel coverage report")
        self.echo("-" * 40)
        self.echo("Found {total} total models.".format(**self.model_counts))
        self.echo("{needing_annotation} needed annotation, {annotated} were annotated.".format(**self.model_counts))

        if self.model_counts['needing_annotation'] > 0:
            pct = float(self.model_counts['annotated']) / float(self.model_counts['needing_annotation']) * 100.0
            pct = round(pct, 1)
        else:
            pct = 100.0

        self.echo(f"Coverage is {pct}%\n")

        if self.uncovered_model_ids:
            displayed_uncovereds = list(self.uncovered_model_ids)
            displayed_uncovereds.sort()
            self.echo(
                "Coverage found {} uncovered models:\n   ".format(len(self.uncovered_model_ids)) +
                "\n   ".join(displayed_uncovereds)
            )

        if pct < float(self.config.coverage_target):
            self.echo(
                "\nCoverage threshold not met! Needed {}, actually {}!".format(
                    self.config.coverage_target,
                    pct
                )
            )
            return False

        return True

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
        return f'{model._meta.app_label}.{model._meta.object_name}'

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
        models_requiring_annotations = []
        total_models = 0

        for app in apps.get_app_configs():
            for root_model in app.get_models():
                total_models += 1
                if DjangoSearch.requires_annotations(root_model):
                    if DjangoSearch.is_non_local(root_model):
                        non_local_models.add(root_model)
                    else:
                        local_models.add(root_model)

                    models_requiring_annotations.append(DjangoSearch.get_model_id(root_model))

        return local_models, non_local_models, total_models, models_requiring_annotations
