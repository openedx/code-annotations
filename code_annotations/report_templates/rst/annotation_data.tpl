{% if annotation.annotation_data is sequence and annotation.annotation_data is not string %}
{% for a in annotation.annotation_data %}
choice_{{ slugify(a) }}_{% if not loop.last %}, {% endif %}
{% endfor %}

{% else %}
{{ annotation.annotation_data }}
{% endif %}
