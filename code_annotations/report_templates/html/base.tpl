<html>
<head>
    <title>{{ doc_title }}</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <style>
    body {
        font-family: 'Trebuchet MS', sans-serif;
    }

    .title {
        text-align: center;
    }

    .table {
        display: table;
        border-spacing: 12px;
    }

    .row {
        display: table-row;
        margin-bottom: 0;
        margin-top: 0;
        width: 100%;
    }

    .cell1 {
        display: table-cell;
        width: 20%;
        margin-right: 1%;
        border: 1px solid #ccc;
        margin 12px;
        background-color: #ffffee;
    }

    .cell2 {
        display: table-cell;
        width: 79%;
        margin-right: 1%;
        margin 12px;
    }

    .group-annotations {
        border: 1px solid #ccc;
        margin: 10px;
    }
    </style>
</head>
<body>
<h1 class="title">{{ doc_title }}</h1>

<div class="table">
    <div class="row">
        <div class="cell1">
            <h3><a href="index.html">Home</a></h3>

            <h3>Annotations</h3>

            <ul>
            {% for a in all_annotations %}
                <li><a href="annotation-{{ slugify(a) }}.html">annotation_{{ slugify(a) }}</a></li>
            {% endfor %}
            </ul>

            <h3>Choices</h3>

            <ul>
            {% for choice in all_choices %}
                <li><a href="choice-{{ slugify(choice) }}.html">choice_{{ slugify(choice) }}</a></li>
            {% endfor %}
            </ul>
        </div>
        <div class="cell2">
            <h2>Files in this page</h2>
            <ul>
            {% for filename in report %}
                <li><a href="#file-{{ slugify(filename) }}">{{ filename }}</a></li>
            {% endfor %}
            </ul>

            {% block content %}{% endblock %}
        </div>
    </div>
</div>
{% block footer %}
<div class="footer">
<br /><br />
<hr />
Built at {{ create_time.strftime('%Y-%m-%d %H:%M:%S %Z') }}
</div>
{% endblock %}
</body>
</html>
