{% block content %}{% endblock %}

{% for choice in all_choices %}
.. _choice_{{ slugify(choice) }}: {{ slugify('choice_' + choice) + '.rst' }}
{% endfor %}

{% for annotation in all_annotations %}
.. _annotation_{{ slugify(annotation) }}: {{ slugify('annotation_' + annotation) + '.rst' }}
{% endfor %}


{% block footer %}
Built at {{ create_time }}
{% endblock %}
