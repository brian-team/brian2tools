{# Jinja2 template for PoissonInput in a simple text format #}

PoissonInput with size {{ poinp['N'] }} gives input to variable {{ expander.render_expression(poinp['target_var']) }} with rate {{ expander.render_expression(poinp['rate']) }} and weight of {{ expander.render_expression(poinp['weight']) }}.

{% if 'identifiers' in poinp %}
**Constants:**
{% for identifier, value in poinp['identifiers'].items() %}
- {{ identifier }}: {{ value }}
{% endfor %}
{% endif %}
