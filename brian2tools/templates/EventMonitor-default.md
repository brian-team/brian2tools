{# Jinja2 template for EventMonitor in a simple text format #}

Monitors variable{{ expander.check_plural(group['variables']) }}: {{ group['variables'] | join(', ', expander.render_expression) }} of {{ expander.expand_SpikeSource(group['source']) }}

{% if group['record'] is boolean %}
    {% if group['record'] %}
        for all members
    {% else %}
        for no member
    {% endif %}
{% else %}
    {% if group['record']|length == 0 %}
        for no member
    {% else %}
        for member{{ expander.check_plural(group['record']) }}: {{ group['record'] | join(', ') }}
    {% endif %}
{% endif %}

when event {{ group['event'] }} is triggered

{{ endll }}
