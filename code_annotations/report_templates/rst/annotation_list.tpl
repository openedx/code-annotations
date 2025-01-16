{% extends "base.tpl" %}
{% block content %}
Annotations found in {{ report|length }} files.

{% for filename in report %}
{% set is_third_party = third_party_package_location in filename %}

{{ filename }}
{{ "-" * filename|length }}

    .. note:: {{ report[filename]|length }} annotations {% if is_third_party %}(installed package){% endif %}


    {% for annotation in report[filename] %}
        {% if annotation.report_group_id %}
            {% if loop.changed(annotation.report_group_id) %}
                {% include 'annotation_group.tpl' %}


            {% endif %}
    * {% include 'annotation.tpl' %}

        {% else %}
            {% if loop.changed(annotation.report_group_id) %}

            {% endif %}
* {% include 'annotation.tpl' %}

        {% endif %}
    {% endfor %}

{% endfor %}

{% endblock %}
