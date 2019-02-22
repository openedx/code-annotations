{% if annotation.extra and annotation.extra.object_id %}
`<{{ annotation.extra.object_id }}> line {{ annotation.line_number }} <{{ source_link_prefix }}{{ filename }}#L{{ annotation.line_number }}>`_: {{ annotation.annotation_token }} {% include "annotation_data.tpl" %}
{% else %}
`{{ filename }}:{{ annotation.line_number }} <{{ source_link_prefix }}{{ filename }}#L{{ annotation.line_number }}>`_: {{ annotation.annotation_token }} {% include "annotation_data.tpl" %}
{% endif %}
