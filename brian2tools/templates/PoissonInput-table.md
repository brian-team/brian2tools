{# Jinja2 template for PoissonInput in table format #}

|-------------------------------|------------------------------------------------|
| **PoissonInput Size**          | {{ group['N'] }}                              |
| **Target Variable**            | {{ expander.render_expression(group['target_var']) }} |
| **Rate**                       | {{ expander.render_expression(group['rate']) }}    |
| **Weight**                     | {{ expander.render_expression(group['weight']) }}  |
| **Constants** (if present)     | {% if 'identifiers' in group %} {% for identifier, value in group['identifiers'].items() %} {{ identifier }}: {{ value }} {% if not loop.last %}\n{% endif %}{% endfor %} {% endif %} |
