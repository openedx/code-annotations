{{ "#" * doc_title|length }}
{{ doc_title }}
{{ "#" * doc_title|length }}

.. sidebar:: Table of Contents

    `Home <index.rst>`_

    Annotations

    {% for a in all_annotations %}
        * annotation_{{ slugify(a) }}_
    {% endfor %}

    Choices

    {% for choice in all_choices %}
        * choice_{{ slugify(choice) }}_
    {% endfor %}


.. contents::

{% block content %}{% endblock %}


{# backlinks for all choices #}
{% for choice in all_choices %}
.. _choice_{{ slugify(choice) }}: {{ slugify('choice_' + choice) + '.rst' }}
{% endfor %}


{# backlinks for all annotations #}
{% for annotation in all_annotations %}
.. _annotation_{{ slugify(annotation) }}: {{ slugify('annotation_' + annotation) + '.rst' }}
{% endfor %}


{% block footer %}
Built at {{ create_time.strftime('%Y-%m-%d %H:%M:%S %Z') }}
{% endblock %}
