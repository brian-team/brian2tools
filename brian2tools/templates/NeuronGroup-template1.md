## Network details

        **Neuron population:**
        - Group {{ neurongrp.name }}, consisting of {{ neurongrp.N }} neurons.

        # Model dynamics
        {% for key, eqn in neurongrp.equations.items() %}
        - $\frac{d}{d t} {{ key }}$ = {{ eqn.expr }}{% if eqn.unit %} [{{ eqn.unit }}]{% endif %}
        {% endfor %}

        {% if neurongrp.user_method %}
        The equations are integrated with the '{{ neurongrp.user_method }}' method.
        {% endif %}

        # Events (if present)
        {% if 'events' in neurongrp %}
        **Events:**

        {% for event, details in neurongrp.events.items() %}
        - If {{ details.threshold.code }}, a {{ event }} event is triggered and {{ details.reset.code }}.
        {% endfor %}
        {% endif %}

        # Constants (if present)
        {% if 'identifiers' in neurongrp %}
        **Constants:**

        {% for identifier, value in neurongrp.identifiers.items() %}
        - {{ identifier }}: {{ value }}
        {% endfor %}
        {% endif %}

        # Initial values (if present)
        {% if 'initializer' in neurongrp and neurongrp['initializer'] %}
        **Initial values:**

        {% for initializer in neurongrp['initializer'] %}
        - {{ initializer.variable }}: {{ initializer.value }}{% if initializer.unit %} [{{ initializer.unit }}]{% endif %}
        {% endfor %}
        {% endif %}

        # Run regularly (if present)
        {% if 'run_regularly' in neurongrp %}
        **Run regularly:**

        {% for run_reg in neurongrp['run_regularly'] %}
        - {{ run_reg }}
        {% endfor %}
        {% endif %}