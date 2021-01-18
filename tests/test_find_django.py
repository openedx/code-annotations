#!/usr/bin/env python
"""
Tests for find annotations in Django models.
"""
import sys
from unittest.mock import DEFAULT, patch

from code_annotations.find_django import DjangoSearch
from tests.fake_models import (
    FakeBaseModelAbstract,
    FakeBaseModelBoring,
    FakeBaseModelBoringWithAnnotations,
    FakeBaseModelNoAnnotation,
    FakeBaseModelProxy,
    FakeBaseModelWithAnnotation,
    FakeBaseModelWithNoDocstring,
    FakeChildModelMultiAnnotation,
    FakeChildModelMultiWithBrokenAnnotations,
    FakeChildModelSingleAnnotation,
    FakeChildModelSingleWithAnnotation
)
from tests.helpers import EXIT_CODE_FAILURE, EXIT_CODE_SUCCESS, call_script, call_script_isolated


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_simple_success(**kwargs):
    """
    Tests the basic case where all models have annotations, with an empty safelist.
    """
    test_models = {
        FakeChildModelSingleAnnotation,
        FakeChildModelMultiAnnotation,
        FakeChildModelSingleWithAnnotation,
        FakeBaseModelWithNoDocstring
    }
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set(),
        len(test_models),
        [DjangoSearch.get_model_id(m) for m in test_models]
    )

    def report_callback(report_contents):
        """
        Get the text of the report and make sure all of the expected models are in it.

        Args:
            report_contents:

        Returns:
            Raw text contents of the generated report file
        """
        for model in test_models:
            assert 'object_id: {}'.format(DjangoSearch.get_model_id(model)) in report_contents

    fake_safelist = """
    fake_app_2.FakeBaseModelWithNoDocstring:
        ".. no_pii:": "No PII"
    """

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report', '--coverage', '-vvv'],
        test_filesystem_report_cb=report_callback,
        fake_safelist_data=fake_safelist
    )

    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'Linting passed without errors' in result.output
    assert 'Generating report to' in result.output
    assert 'Search found 6 annotations' in result.output


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_no_viable_models(**kwargs):
    """
    Tests the basic case where all models have annotations, with an empty safelist.
    """
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        set(),
        set(),
        0,
        []
    )

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report'],
    )

    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'Linting passed without errors' in result.output
    assert 'Generating report to' in result.output
    assert 'Search found 0 annotations' in result.output


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_model_not_annotated(**kwargs):
    """
    Test that a non-annotated model fails.
    """
    test_models = {FakeBaseModelNoAnnotation, }
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set(),
        0,
        []
    )

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report', '-vv']
    )

    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'fake_app_1.FakeBaseModelNoAnnotation has no annotations' in result.output
    assert 'Linting passed without errors.' in result.output
    assert 'Generating report to' in result.output


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_model_in_safelist_not_annotated(**kwargs):
    """
    Test that a safelisted model with no annotations fails.
    """
    test_models = {FakeBaseModelNoAnnotation, }
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set(),
        0,
        []
    )

    fake_safelist_data = """
    {
        fake_app_1.FakeBaseModelNoAnnotation: {}
    }
    """

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report'],
        fake_safelist_data=fake_safelist_data,
    )

    assert result.exit_code == EXIT_CODE_FAILURE
    assert 'fake_app_1.FakeBaseModelNoAnnotation is in the safelist but has no annotations!' in result.output
    assert '1 errors:' in result.output
    assert 'Generating report to' not in result.output


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_model_in_safelist_annotated(**kwargs):
    """
    Test that a safelisted model succeeds.
    """
    test_models = {FakeBaseModelNoAnnotation, }
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set(),
        0,
        []
    )

    fake_safelist_data = """
    {
        fake_app_1.FakeBaseModelNoAnnotation: {".. no_pii:": "This model is annotated."}
    }
    """

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report'],
        fake_safelist_data=fake_safelist_data,
    )

    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'Linting passed without errors' in result.output
    assert 'Generating report to' in result.output
    assert 'Search found 1 annotations' in result.output


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_no_safelist(**kwargs):
    """
    Test that we fail when there is no safelist.
    """
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (set(), set(), 0, [])

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report'],
        fake_safelist_data=None,
    )

    assert result.exit_code == EXIT_CODE_FAILURE
    assert 'Safelist not found!' in result.output
    assert 'Generating report to' not in result.output


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_in_safelist_and_annotated(**kwargs):
    """
    Test that a model which is annotated and also in the safelist fails.
    """
    test_models = {FakeBaseModelWithAnnotation, }
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set(),
        0,
        []
    )

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report'],
        fake_safelist_data='{{{}: ".. no_pii:"}}'.format(DjangoSearch.get_model_id(FakeBaseModelWithAnnotation))
    )

    assert result.exit_code == EXIT_CODE_FAILURE
    assert 'fake_app_2.FakeBaseModelWithAnnotation is annotated, but also in the safelist.' in result.output
    assert '1 errors:' in result.output
    assert 'Generating report to' not in result.output


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_no_docstring(**kwargs):
    """
    Test that a model with no docstring doesn't break anything.
    """
    test_models = {FakeBaseModelWithNoDocstring, }
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set(),
        0,
        []
    )
    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report', '-vv']
    )

    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'fake_app_2.FakeBaseModelWithNoDocstring has no annotations' in result.output
    assert 'Linting passed without errors.' in result.output
    assert 'Generating report to' in result.output


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_ordering_error(**kwargs):
    """
    Tests broken annotations to make sure the error paths work.
    """
    test_models = {FakeChildModelSingleAnnotation, FakeChildModelMultiWithBrokenAnnotations}
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set(),
        0,
        []
    )

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint', '--report']
    )

    assert result.exit_code == EXIT_CODE_FAILURE
    assert "missing non-optional annotation: '.. pii:'" in result.output


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_without_linting(**kwargs):
    """
    Tests to make sure reports will be written in the case of errors, if linting is off.
    """
    test_models = {FakeChildModelSingleAnnotation, FakeChildModelMultiWithBrokenAnnotations}
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set(),
        0,
        []
    )

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--report']
    )

    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'Linting passed without errors' not in result.output
    assert 'Generating report to' in result.output


@patch.multiple(
    'code_annotations.find_django.DjangoSearch',
    get_models_requiring_annotations=DEFAULT
)
def test_find_django_without_report(**kwargs):
    """
    Tests to make sure reports will be written in the case of errors, if linting is off.
    """
    test_models = {FakeChildModelSingleAnnotation}
    mock_get_models_requiring_annotations = kwargs['get_models_requiring_annotations']
    mock_get_models_requiring_annotations.return_value = (
        test_models,
        set(),
        0,
        []
    )

    result = call_script_isolated(
        ['django_find_annotations', '--config_file', 'test_config.yml', '--lint']
    )

    assert result.exit_code == EXIT_CODE_SUCCESS
    assert 'Linting passed without errors' in result.output
    assert 'Generating report to' not in result.output


@patch('code_annotations.find_django.issubclass')
def test_requires_annotations_abstract(mock_issubclass):
    """
    Abstract classes should not require annotations
    """
    mock_issubclass.return_value = True
    assert DjangoSearch.requires_annotations(FakeBaseModelAbstract) is False


@patch('code_annotations.find_django.issubclass')
def test_requires_annotations_proxy(mock_issubclass):
    """
    Proxy classes should not require annotations
    """
    mock_issubclass.return_value = True
    assert DjangoSearch.requires_annotations(FakeBaseModelProxy) is False


@patch('code_annotations.find_django.issubclass')
def test_requires_annotations_normal(mock_issubclass):
    """
    Non-abstract, non-proxy models should require annotations
    """
    mock_issubclass.return_value = True
    assert DjangoSearch.requires_annotations(FakeBaseModelBoring) is True


def test_requires_annotations_not_a_model():
    """
    Things which are not models should not require annotations
    """
    assert DjangoSearch.requires_annotations(dict) is False


def test_is_non_local_simple():
    """
    Our model is local, should show up as such
    """
    assert DjangoSearch.is_non_local(FakeBaseModelAbstract) is False


@patch('code_annotations.find_django.inspect.getsourcefile')
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
            mock_getsourcefile.return_value = f'{prefix}/bar.py'
            assert DjangoSearch.is_non_local(FakeBaseModelAbstract) is True
    else:
        # If there are no prefixes in the test environment, there's really nothing to do here.
        pass


@patch('code_annotations.find_django.issubclass')
@patch('code_annotations.find_django.DjangoSearch.setup_django')
@patch('code_annotations.find_django.DjangoSearch.is_non_local')
@patch('code_annotations.find_django.django.apps.apps.get_app_configs')
def test_get_models_requiring_annotations(mock_get_app_configs, mock_is_non_local, mock_setup_django, mock_issubclass):
    # Lots of fakery going on here. This class mocks Django AppConfigs to deliver our fake models.
    class FakeAppConfig:
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

    local_models, non_local_models, total, needing_annotations = DjangoSearch.get_models_requiring_annotations()

    assert len(local_models) == 1
    assert len(non_local_models) == 1
    assert list(local_models)[0] == FakeBaseModelBoringWithAnnotations
    assert list(non_local_models)[0] == FakeBaseModelBoring
    assert total == 2
    assert len(needing_annotations) == 2


@patch('code_annotations.find_django.DjangoSearch.setup_django')
@patch('code_annotations.find_django.DjangoSearch.get_models_requiring_annotations')
def test_find_django_no_coverage_configured(mock_get_models, mock_setup_django):
    """
    Tests the basic case where all models have annotations, with an empty safelist.
    """
    mock_get_models.return_value = ([], [], 0, [])
    mock_setup_django.return_value = True

    result = call_script(
        [
            'django_find_annotations',
            '--config_file', 'tests/test_configurations/.annotations_test_missing_coverage_target',
            '--coverage',
            '-vvv',
        ]
    )

    assert result.exit_code == EXIT_CODE_FAILURE
    assert "Please add 'coverage_target' to your configuration before running --coverage" in result.output


@patch('code_annotations.find_django.django.setup')
def test_setup_django(mock_django_setup):
    """
    This is really just for coverage.
    """
    mock_django_setup.return_value = True
    DjangoSearch.setup_django()
