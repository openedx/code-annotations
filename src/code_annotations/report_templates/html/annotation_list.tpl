{% extends "base.tpl" %}
{% block content %}
Annotations found in {{ report|length }} files.

{% for filename in report %}
{% set is_third_party = third_party_package_location in filename %}

<h2 id="file-{{ slugify(filename) }}">{{ filename }}</h2>
    <div class="file-annotations">
    {{ report[filename]|length }} annotations {% if is_third_party %}(installed package){% endif %}<br />
    </div>

    {% for annotation in report[filename] %}
        {% if loop.changed(annotation.report_group_id) %}
            {% if not loop.first %}</ul></div>{% endif %}
            <div class="group-annotations"><ul>
        {% endif %}
                <li>{% include 'annotation.tpl' %}</li>
        {% if loop.last %}
            </ul></div>
        {% endif %}
    {% endfor %}


{% endfor %}

{% endblock %}
