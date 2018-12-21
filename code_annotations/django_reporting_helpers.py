"""
Django related functionality for code annotations.
"""
import inspect
import sys

import django
from django.apps import apps
from django.db import models


def requires_pii_annotations(model):
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


def get_model_id(model):
    """
    Construct the django standard model identifier in "app_label.ModelClassName" notation.

    Args:
        model (django.db.models.Model): A model for which to create an identifier.

    Returns:
        str: identifier string for the given model.
    """
    return '{}.{}'.format(model._meta.app_label, model._meta.object_name)


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
    setup_django()
    local_models = set()
    non_local_models = set()
    for app in apps.get_app_configs():
        for root_model in app.get_models():
            # getmro() includes the _entire_ inheritance closure, not just the direct inherited classes.
            heirarchy = inspect.getmro(root_model)
            for model in heirarchy:
                if requires_pii_annotations(model):
                    if is_non_local(model):
                        non_local_models.add(model)
                    else:
                        local_models.add(model)
    return local_models, non_local_models
