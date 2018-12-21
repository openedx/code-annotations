"""
Test django_reporting_helpers functions that aren't exercised elsewhere.
"""
import sys

import mock

from code_annotations.django_reporting_helpers import (
    get_models_requiring_annotations,
    is_non_local,
    requires_annotations,
    setup_django
)
from tests.fake_models import (
    FakeBaseModelAbstract,
    FakeBaseModelBoring,
    FakeBaseModelBoringWithAnnotations,
    FakeBaseModelProxy
)


@mock.patch('code_annotations.django_reporting_helpers.issubclass')
def test_requires_annotations_abstract(mock_issubclass):
    """
    Abstract classes should not require annotations
    """
    mock_issubclass.return_value = True
    assert requires_annotations(FakeBaseModelAbstract) is False


@mock.patch('code_annotations.django_reporting_helpers.issubclass')
def test_requires_annotations_proxy(mock_issubclass):
    """
    Proxy classes should not require annotations
    """
    mock_issubclass.return_value = True
    assert requires_annotations(FakeBaseModelProxy) is False


@mock.patch('code_annotations.django_reporting_helpers.issubclass')
def test_requires_annotations_normal(mock_issubclass):
    """
    Non-abstract, non-proxy models should require annotations
    """
    mock_issubclass.return_value = True
    assert requires_annotations(FakeBaseModelBoring) is True


def test_requires_annotations_not_a_model():
    """
    Things which are not models should not require annotations
    """
    assert requires_annotations(dict) is False


def test_is_non_local_simple():
    """
    Our model is local, should show up as such
    """
    assert is_non_local(FakeBaseModelAbstract) is False


@mock.patch('code_annotations.django_reporting_helpers.inspect.getsourcefile')
def test_is_non_local_site(mock_getsourcefile):
    """
    Try to test the various non-local paths, if the environment allows.
    """

    # This code is duplicated from the method itself.
    non_local_path_prefixes = []
    for path in sys.path:
        if 'dist-packages' in path or 'site-packages' in path:
            non_local_path_prefixes.append(path)

    if non_local_path_prefixes:
        for prefix in non_local_path_prefixes:
            mock_getsourcefile.return_value = '{}/bar.py'.format(prefix)
            assert is_non_local(FakeBaseModelAbstract) is True
    else:
        # If there are no prefixes in the test environment, there's really nothing to do here.
        pass


@mock.patch('code_annotations.django_reporting_helpers.django.setup')
def test_setup_django(mock_django_setup):
    """
    This is really just for coverage.
    """
    mock_django_setup.return_value = True
    setup_django()


@mock.patch('code_annotations.django_reporting_helpers.issubclass')
@mock.patch('code_annotations.django_reporting_helpers.setup_django')
@mock.patch('code_annotations.django_reporting_helpers.django.apps.apps.get_app_configs')
@mock.patch('code_annotations.django_reporting_helpers.is_non_local')
def test_get_models_requiring_annotations(mock_is_non_local, mock_get_app_configs, mock_setup_django, mock_issubclass):
    # Lots of fakery going on here. This class mocks Django AppConfigs to deliver our fake models.
    class FakeAppConfig(object):
        def get_models(self):
            return [FakeBaseModelBoring, FakeBaseModelBoringWithAnnotations]

    # This lets us deterministically decide that one model is local, and the other isn't, for testing both branches.
    mock_is_non_local.side_effect = [True, False]

    # This just fakes setting up Django
    mock_setup_django.return_value = True

    # This mocks out Django's get_app_configs to return our fake AppConfig
    mock_get_app_configs.return_value = [FakeAppConfig()]

    # This lets us pretend that all of our fake models inherit from Django's model.Model.
    # If we try to do that inheritance Django will throw errors unless we do a full Django
    # testing setup.
    mock_issubclass.return_value = True

    local_models, non_local_models = get_models_requiring_annotations()

    assert len(local_models) == 1
    assert len(non_local_models) == 1
    assert list(local_models)[0] == FakeBaseModelBoringWithAnnotations
    assert list(non_local_models)[0] == FakeBaseModelBoring
