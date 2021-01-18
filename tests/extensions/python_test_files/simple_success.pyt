"""
Docstring

.. pii: Annotation 1
.. pii_types: id, name
.. pii_retirement: local_api, consumer_api
"""


def do():
    """.. pii: Annotation 2
        .. pii_types: id, name
        .. pii_retirement: local_api, consumer_api
    """
    pass


def re():
    """.. pii: Annotation 3
    .. pii_retirement: local_api, consumer_api
    .. pii_types: id, name"""
    pass


def mi():
    """
    Comment above annotation
    .. pii: Annotation 4
    .. pii_types: id, name
    .. pii_retirement: local_api, consumer_api
    Comment below annotation
    """
    pass


def fa():
    """.. no_pii: Annotation 5"""
    pass


def so():
    """
    Test choices outside of a group
    .. ignored: silly-silly,terrible, irrelevant
    .. ignored: terrible irrelevant silly-silly
    """
    pass


def la():
    # .. pii: Annotation 6
    # .. pii_types: id, name
    # .. pii_retirement: local_api, consumer_api
    pass


def ti():
    # .. ignored: silly-silly,terrible, irrelevant
    # .. ignored: terrible irrelevant silly-silly
    pass
