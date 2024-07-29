|-------------------------------|------------------------------------------------|
| **Neuron population**         | Group {{ (neurongrp['name']) }}, consisting of {{ (neurongrp['N']) }} neurons. |
| **Model dynamics**            | {{ expander.expand_equations(neurongrp['equations']) }} |
| **Integration method**        | {% if neurongrp['user_method'] %} The equations are integrated with the '{{ neurongrp['user_method'] }}' method. {% endif %} |
| **Events** (if present)       | {% if 'events' in neurongrp %} {{ expander.expand_events(neurongrp['events']) }} {% endif %} |
| **Constants** (if present)    | {% if 'identifiers' in neurongrp %} {{ expander.expand_identifiers(neurongrp['identifiers']) }} {% endif %} |
| **Initial values** (if present)| {% if not expander.keep_initializer_order and 'initializer' in neurongrp and neurongrp['initializer']|length %} {% for initializer in neurongrp['initializer'] %} {{ initializer.variable }}: {{ initializer.value }}{% if initializer.unit %} [{{ initializer.unit }}]{% endif %} {% if not loop.last %}\n{% endif %}{% endfor %} {% endif %} |
| **Run regularly** (if present)| {% if 'run_regularly' in neurongrp %} {% for run_reg in neurongrp['run_regularly'] %} {{ expander.expand_runregularly(run_reg) }} {% if not loop.last %}\n{% endif %}{% endfor %} {% endif %} |
