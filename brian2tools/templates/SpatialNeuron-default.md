## Network details
 **Neuron population:**
Group {{ (group['name']) }}, consisting of {{ (group['N']) }} neurons.
{{ tab }}{{ ('Model dynamics:') }}
{{ expander.expand_equations(group['equations']) }}
 {% if group['user_method'] %}
    {{ tab }}The equations are integrated with the '{{ group['user_method'] }}' method.
{% endif %}
{% if 'events' in group %}
    {{ tab }}{{ ('Events:') }}
    {{ expander.expand_events(group['events']) }}
{% endif %}
{% if 'identifiers' in group %}
    {{ tab }}{{ ('Constants:') }} {{ expander.expand_identifiers(group['identifiers']) }}
{% endif %}
{% if not expander.keep_initializer_order and 'initializer' in group and group['initializer']|length %}
    {{ tab }}{{ ('Initial values:') }}
    {% for initializer in group['initializer'] %}
        {{ tab }}* {{ expander.expand_initializer(initializer) }}
    {% endfor %}
{% endif %}
{% if 'run_regularly' in group %}
    {{ tab }}{{ ('Run regularly') }}{{ expander.check_plural(group['run_regularly']) }}:
    {% for run_reg in group['run_regularly'] %}
        {{ expander.expand_runregularly(run_reg) }}
    {% endfor %}
{% endif %}
               


