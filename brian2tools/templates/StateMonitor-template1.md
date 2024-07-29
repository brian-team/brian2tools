{# Jinja2 template for Statemon in simple text format #}

Monitors variable{{ expander.check_plural(statemon['variables']) }}: {{ statemon['variables'] | join(', ', expander.render_expression) }} of {{ expander.expand_SpikeSource(statemon['source']) }}

{% if statemon['record'] is boolean %}
    {% if statemon['record'] %}
        for all members
    {% else %}
        for no member
    {% endif %}
{% else %}
    {% if statemon['record']|length == 0 %}
        for no member
    {% else %}
        for member{{ expander.check_plural(statemon['record']) }}: {{ statemon['record'] | join(', ') }}
    {% endif %}
{% endif %}
