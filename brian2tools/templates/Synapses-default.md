Connections {{ group['name'] }}, connecting {{ expander.expand_SpikeSource(group['source']) }} to {{ expander.expand_SpikeSource(group['target']) }}
{% if not expander.keep_initializer_order and 'connectors' in group and group['connectors']|length -%}
    {{ tab }}{{ expander.expand_connector(group['connectors'][0]) }}
{% endif %}
{% if 'equations' in group -%}
    {{ tab }}{{ bold('Model dynamics:') }}
    {{ expander.expand_equations(group['equations']) }}
    {% if 'user_method' in group -%}
        {{ tab }}The equations are integrated with the '{{ group['user_method'] }}' method.{{ endll }}
    {% endif %}
{% endif %}
{% if 'pathways' in group -%}
    {{ expander.expand_pathways(group['pathways']) }}
    {% if 'equations' not in group and 'identifiers' in group -%}
        {{ tab }}, where {{ expander.expand_identifiers(group['identifiers']) }}.
    {% endif %}
{% endif %}
{% if 'summed_variables' in group -%}
    {{ tab }}{{ bold('Summed variables:') }}
    {{ expander.expand_summed_variables(group['summed_variables']) }}
{% endif %}
{% if 'identifiers' in group and 'equations' in group -%}
    {{ tab }}{{ bold('Constants:') }} {{ expander.expand_identifiers(group['identifiers']) }}
{% endif %}
{% if not expander.keep_initializer_order and 'initializer' in group and group['initializer']|length -%}
    {{ tab }}{{ bold('Initial values:') }}
    {% for initializer in group['initializer'] -%}
        {{ tab }}* {{ expander.expand_initializer(initializer) }}
    {% endfor %}
{% endif %}

