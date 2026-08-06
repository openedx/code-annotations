{% if annotation.annotation_data is sequence and annotation.annotation_data is not string %}
{% for a in annotation.annotation_data %}
<a href="choice-{{ slugify(a) }}.html">{{ a }}</a>{% if not loop.last %}, {% endif %}
{% endfor %}

{% else %}
{{ annotation.annotation_data }}
{% endif %}
