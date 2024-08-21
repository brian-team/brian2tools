Name {{ group['name'] }} of population size {{ group['N'] }} and rate as {{ expander.render_expression(group['rates']) }}.

        {% if group.get('identifiers', None) %}
        Constants:
        {{ expander.expand_identifiers(group['identifiers']) }}
        {% endif %}

        {% if group.get('run_regularly', None) %}
     
        Run regularly:
        {% for run_reg in group['run_regularly'] %}
        {{ expander.expand_runregularly(run_reg) }}
        {% endfor %}
        {% endif %}


      
