{% extends "base.tpl" %}
{% block content %}
Complete Annotation List
------------------------
Annotations found in {{ report|length }} files.

{% for filename in report %}
{{ filename }} has {{ report[filename]|length }} annotations.

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
