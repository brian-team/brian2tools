Name {{ poissongrp['name'] }} with population size {{ poissongrp['N'] }} and rate as {{ render_expression(poissongrp['rates']) }}.

        {% if poissongrp.get('identifiers', None) %}
        Constants:
        {{ expand_identifiers(poissongrp['identifiers']) }}
        {% endif %}

        {% if poissongrp.get('run_regularly', None) %}
        Run regularly:
        {% for run_reg in poisngrp['run_regularly'] %}
        {{ expand_runregularly(run_reg) }}
        {% endfor %}
        {% endif %}