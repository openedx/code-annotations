"""
Mocked models for testing Django search functionality.
"""
from mock import MagicMock


# Base model with no annotation and its children
class FakeBaseModelNoAnnotation(object):
    """
    This is a fake model with no annotations.
    """

    _meta = MagicMock(app_label='fake_app_1', object_name='FakeBaseModelNoAnnotation', abstract=False, proxy=False)


class FakeChildModelNoAnnotation(FakeBaseModelNoAnnotation):
    """
    This model inherits, but also has no annotations.
    """

    _meta = MagicMock(app_label='fake_app_1', object_name='FakeChildModelNoAnnotation', abstract=False, proxy=False)


class FakeChildModelSingleAnnotation(FakeBaseModelNoAnnotation):
    """
    This model inherits and has one annotation.

    .. no_pii: Child model.
    """

    _meta = MagicMock(app_label='fake_app_1', object_name='FakeChildModelSingleAnnotation', abstract=False, proxy=False)


class FakeChildModelMultiAnnotation(FakeChildModelSingleAnnotation):
    """
    This model multi-level inherits and has one annotation. Its parent also has one.

    .. no_pii: Grandchild model.
    """

    _meta = MagicMock(app_label='fake_app_1', object_name='FakeChildModelMultiAnnotation', abstract=False, proxy=False)


# Base model with an annotation and its children
class FakeBaseModelWithAnnotation(object):
    """
    This is a fake model with one annotation.

    .. no_pii: Base model annotation.
    """

    _meta = MagicMock(app_label='fake_app_2', object_name='FakeBaseModelWithAnnotation', abstract=False, proxy=False)


class FakeChildModelWithAnnotation(FakeBaseModelWithAnnotation):
    """
    This model inherits, but also has no annotations.
    """

    _meta = MagicMock(app_label='fake_app_2', object_name='FakeChildModelWithAnnotation', abstract=False, proxy=False)


class FakeChildModelSingleWithAnnotation(FakeBaseModelWithAnnotation):
    """
    This model inherits and has one annotation.

    .. no_pii: Child model.
    """

    _meta = MagicMock(
        app_label='fake_app_2',
        object_name='FakeChildModelSingleWithAnnotation',
        abstract=False,
        proxy=False
    )


class FakeChildModelMultiWithAnnotation(FakeChildModelWithAnnotation):
    """
    This model multi-level inherits and has one annotation. Its parent also has one.

    .. no_pii: Grandchild model.
    """

    _meta = MagicMock(
        app_label='fake_app_2',
        object_name='FakeChildModelMultiWithAnnotation',
        abstract=False,
        proxy=False
    )


class FakeBaseModelWithNoDocstring(object):
    _meta = MagicMock(app_label='fake_app_2', object_name='FakeBaseModelWithNoDocstring', abstract=False, proxy=False)


class FakeChildModelMultiWithBrokenAnnotations(FakeChildModelWithAnnotation):
    """
    This model multi-level inherits and has one annotation. Its parent also has one.

    .. pii_types: id
    .. pii_retirement: retained
    """

    _meta = MagicMock(
        app_label='fake_app_2',
        object_name='FakeChildModelMultiWithBrokenAnnotations',
        abstract=False,
        proxy=False
    )


# Models for testing requires_annotations
class FakeBaseModelBoring(object):
    """
    This is a fake model with no annotations.
    """

    _meta = MagicMock(app_label='fake_app_3', object_name='FakeBaseModelBoring', abstract=False, proxy=False)


class FakeBaseModelBoringWithAnnotations(object):
    """
    This is a fake model with an annotation.

    .. no_pii: No PII.
    """

    _meta = MagicMock(
        app_label='fake_app_3',
        object_name='FakeBaseModelBoringWithAnnotations',
        abstract=False,
        proxy=False
    )


class FakeBaseModelAbstract(object):
    """
    This is a fake abstract model.
    """

    _meta = MagicMock(app_label='fake_app_3', object_name='FakeBaseModelAbstract', abstract=True, proxy=False)


class FakeBaseModelProxy(object):
    """
    This is a fake proxy model.
    """

    _meta = MagicMock(app_label='fake_app_3', object_name='FakeBaseModelProxy', abstract=False, proxy=True)
