Connections {{ synapse['name'] }}, connecting {{ expander.expand_SpikeSource(synapse['source']) }} to {{ expander.expand_SpikeSource(synapse['target']) }}
{% if not expander.keep_initializer_order and 'connectors' in synapse and synapse['connectors']|length -%}
    {{ tab }}{{ expander.expand_connector(synapse['connectors'][0]) }}
{% endif %}
{% if 'equations' in synapse -%}
    {{ tab }}{{ bold('Model dynamics:') }}
    {{ expander.expand_equations(synapse['equations']) }}
    {% if 'user_method' in synapse -%}
        {{ tab }}The equations are integrated with the '{{ synapse['user_method'] }}' method.{{ endll }}
    {% endif %}
{% endif %}
{% if 'pathways' in synapse -%}
    {{ expander.expand_pathways(synapse['pathways']) }}
    {% if 'equations' not in synapse and 'identifiers' in synapse -%}
        {{ tab }}, where {{ expander.expand_identifiers(synapse['identifiers']) }}.
    {% endif %}
{% endif %}
{% if 'summed_variables' in synapse -%}
    {{ tab }}{{ bold('Summed variables:') }}
    {{ expander.expand_summed_variables(synapse['summed_variables']) }}
{% endif %}
{% if 'identifiers' in synapse and 'equations' in synapse -%}
    {{ tab }}{{ bold('Constants:') }} {{ expander.expand_identifiers(synapse['identifiers']) }}
{% endif %}
{% if not expander.keep_initializer_order and 'initializer' in synapse and synapse['initializer']|length -%}
    {{ tab }}{{ bold('Initial values:') }}
    {% for initializer in synapse['initializer'] -%}
        {{ tab }}* {{ expander.expand_initializer(initializer) }}
    {% endfor %}
{% endif %}