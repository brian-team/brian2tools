{# Jinja2 template for PoissonInput in a simple text format #}

PoissonInput with size {{ group['N'] }} gives input to variable {{ expander.render_expression(group['target_var']) }} with rate {{ expander.render_expression(group['rate']) }} and weight of {{ expander.render_expression(group['weight']) }}.

{% if 'identifiers' in group %}
**Constants:**
{% for identifier, value in group['identifiers'].items() %}
- {{ identifier }}: {{ value }}
{% endfor %}
{% endif %}
