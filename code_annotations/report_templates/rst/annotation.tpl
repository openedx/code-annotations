{% if is_third_party %}
{# no links for third party code since we don't know where to link to #}
{% if annotation.extra and annotation.extra.object_id %}
{{ annotation.extra.object_id }} {% if annotation.line_number > 0 %}line {{ annotation.line_number }}{% endif %}: {{ annotation.annotation_token }} {% include "annotation_data.tpl" %}
{% else %}
{{ filename }}:{{ annotation.line_number }}: {{ annotation.annotation_token }} {% include "annotation_data.tpl" %}
{% endif %}

{% elif annotation.extra and annotation.extra.object_id %}
`{{ annotation.extra.object_id }} {% if annotation.line_number > 0 %}line {{ annotation.line_number }}{% endif %} <{{ source_link_prefix }}{{ filename }}#L{{ annotation.line_number }}>`_: {{ annotation.annotation_token }} {% include "annotation_data.tpl" %}
{% else %}
`{{ filename }}:{{ annotation.line_number }} <{{ source_link_prefix }}{{ filename }}#L{{ annotation.line_number }}>`_: {{ annotation.annotation_token }} {% include "annotation_data.tpl" %}
{% endif %}
