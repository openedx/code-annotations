"""
Tests that a change in group ordering doesn't break following groups

Group ordered as defined in configuration

.. pii:: Group 1 - Annotation 1
.. pii_types:: id, name
.. pii_retirement:: local_api, consumer_api
"""
"""
Differently ordered group

.. pii:: Group 2 - Annotation 1
.. pii_retirement:: local_api, consumer_api
.. pii_types:: id, name
"""
"""
Group ordered as defined in configuration

.. pii:: Group 3 - Annotation 1
.. pii_types:: id, name
.. pii_retirement:: local_api, consumer_api
"""
