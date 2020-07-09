"""
Docstring

.. pii: Annotation 1 with:
     
     Multi-line and multi-paragraph.
"""
# Should be able to finish the group outside of the same comment if necessary
# .. pii_types: id, name
# .. pii_retirement: local_api, consumer_api


def do():
    """.. pii: Annotation 2 with:
     
           Multi-line and multi-paragraph.
        .. pii_types: id, name
        .. pii_retirement: local_api, consumer_api
    """
    pass


def re():
    """.. pii: Annotation 3 with:
    
         Multi-line and multi-paragraph.
    .. pii_retirement: local_api, consumer_api
    .. pii_types: id, name"""
    pass


def mi():
    """
    Comment above annotation
    .. pii: Annotation 4 with:
    
         Multi-line and multi-paragraph.
    .. pii_types: id, name
    .. pii_retirement: local_api, consumer_api
    Comment below annotation
    """
    pass


def fa():
    """.. no_pii: Annotation 5 with:
    
         Multi-line and multi-paragraph."""
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
