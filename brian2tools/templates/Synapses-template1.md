Connections {{ synapse['name'] }}, connecting {{ self.expand_SpikeSource(synapse['source']) }} to {{ self.expand_SpikeSource(synapse['target']) }}
{% if not self.keep_initializer_order and 'connectors' in synapse %}
    {% if synapse['connectors']|length %}
        {{ tab }}{{ self.expand_connector(synapse['connectors'][0]) }}
    {% endif %}
{% else %}
    .{{ endll }}
{% endif %}

{% if 'equations' in synapse %}
    {{ tab }}{{ bold('Model dynamics:') }}{{ endll }}
    {{ self.expand_equations(synapse['equations']) }}
    {% if 'user_method' in synapse %}
        {{ tab }}The equations are integrated with the '{{ synapse['user_method'] }}' method.{{ endll }}
    {% endif %}
{% endif %}

{% if 'pathways' in synapse %}
    {{ self.expand_pathways(synapse['pathways']) }}
    {% if 'equations' not in synapse and 'identifiers' in synapse %}
        {{ tab }}, where {{ self.expand_identifiers(synapse['identifiers']) }}.
    {% endif %}
    {{ endll }}
{% endif %}

{% if 'summed_variables' in synapse %}
    {{ tab }}{{ bold('Summed variables:') }}{{ endll }}
    {{ self.expand_summed_variables(synapse['summed_variables']) }}
{% endif %}

{% if 'identifiers' in synapse and 'equations' in synapse %}
    {{ tab }}{{ bold('Constants:') }} {{ self.expand_identifiers(synapse['identifiers']) }}{{ endll }}
{% endif %}

{% if not self.keep_initializer_order and 'initializer' in synapse and synapse['initializer']|length %}
    {{ tab }}{{ bold('Initial values:') }}\n
    {% for initializer in synapse['initializer'] %}
        {{ tab }}* {{ self.expand_initializer(initializer) }}\n
    {% endfor %}
    \n
{% endif %}