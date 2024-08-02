Name {{ group['name'] }} with population size {{ group['N'] }} and rate as {{ render_expression(group['rates']) }}.

        {% if group.get('identifiers', None) %}
        Constants:
        {{ expand_identifiers(group['identifiers']) }}
        {% endif %}

        {% if group.get('run_regularly', None) %}
        Run regularly:
        {% for run_reg in poisngrp['run_regularly'] %}
        {{ expand_runregularly(run_reg) }}
        {% endfor %}
        {% endif %}