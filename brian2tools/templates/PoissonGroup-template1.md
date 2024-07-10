Name {{ poisngrp['name'] }} with population size {{ poisngrp['N'] }} and rate as {{ render_expression(poisngrp['rates']) }}.

        {% if poisngrp.get('identifiers', None) %}
        Constants:
        {{ expand_identifiers(poisngrp['identifiers']) }}
        {% endif %}

        {% if poisngrp.get('run_regularly', None) %}
        Run regularly:
        {% for run_reg in poisngrp['run_regularly'] %}
        {{ expand_runregularly(run_reg) }}
        {% endfor %}
        {% endif %}