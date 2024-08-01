{# Jinja2 template for Statemon in Markdown table format #}

| Variable(s) | Source | Record |
|-------------|--------|--------|
| {%- for var in statemon['variables'] -%}
    {{ expander.render_expression(var) }}{%- if not loop.last -%}, {%- endif -%}
{%- endfor %} | {{ expander.expand_SpikeSource(statemon['source']) }} | 
{%- if statemon['record'] is boolean -%}
    {%- if statemon['record'] -%} all members
    {%- else -%} no member
    {%- endif -%}
{%- else -%}
    {%- if statemon['record']|length == 0 -%} no member
    {%- else -%} members{{ expander.check_plural(statemon['record']) }}: {{ statemon['record'] | join(', ') }}
    {%- endif -%}
{%- endif %}
|