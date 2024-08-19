{# Jinja2 template for Statemon in simple text format #}
Monitors variable{{ expander.check_plural(group['variables']) }}: {%- for var in group['variables'] -%}
    {{ expander.render_expression(var) }}{%- if not loop.last -%}, {%- endif -%}
{%- endfor %} of {{ expander.expand_SpikeSource(group['source']) }} {%- if group['record'] is boolean -%}
    {%- if group['record'] -%} for all members {%- else -%} for no member {%- endif -%}
{%- else -%}
    {%- if group['record']|length == 0 -%} for no member {%- else -%} for member{{ expander.check_plural(group['record']) }}: {{ group['record'] | join(', ') }} {%- endif -%}
{%- endif -%}

