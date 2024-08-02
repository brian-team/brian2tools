{# Jinja2 template for PoissonInput in table format #}

|-------------------------------|------------------------------------------------|
| **PoissonInput Size**          | {{ poinp['N'] }}                              |
| **Target Variable**            | {{ expander.render_expression(poinp['target_var']) }} |
| **Rate**                       | {{ expander.render_expression(poinp['rate']) }}    |
| **Weight**                     | {{ expander.render_expression(poinp['weight']) }}  |
| **Constants** (if present)     | {% if 'identifiers' in poinp %} {% for identifier, value in poinp['identifiers'].items() %} {{ identifier }}: {{ value }} {% if not loop.last %}\n{% endif %}{% endfor %} {% endif %} |
