|-------------------------------|------------------------------------------------|
| **Neuron population**         | Group {{ (group['name']) }}, consisting of {{ (group['N']) }} neurons. |
| **Model dynamics**            | {{ expander.expand_equations(group['equations']) }} |
| **Integration method**        | {% if group['user_method'] %} The equations are integrated with the '{{ group['user_method'] }}' method. {% endif %} |
| **Events** (if present)       | {% if 'events' in group %} {{ expander.expand_events(group['events']) }} {% endif %} |
| **Constants** (if present)    | {% if 'identifiers' in group %} {{ expander.expand_identifiers(group['identifiers']) }} {% endif %} |
| **Initial values** (if present)| {% if not expander.keep_initializer_order and 'initializer' in group and group['initializer']|length %} {% for initializer in group['initializer'] %} {{ initializer.variable }}: {{ initializer.value }}{% if initializer.unit %} [{{ initializer.unit }}]{% endif %} {% if not loop.last %}\n{% endif %}{% endfor %} {% endif %} |
| **Run regularly** (if present)| {% if 'run_regularly' in group %} {% for run_reg in group['run_regularly'] %} {{ expander.expand_runregularly(run_reg) }} {% if not loop.last %}\n{% endif %}{% endfor %} {% endif %} |
