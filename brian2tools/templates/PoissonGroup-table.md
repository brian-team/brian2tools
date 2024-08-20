        | **Variable**                     | **Value**                                      |
|---------------------------------|------------------------------------------------|
| **Name**                        | {{ group['name'] }}                        |
| **Population size**             | {{ group['N'] }}                           |
| **Rate**                        | {{ expander.render_expression(group['rates']) }}     |
| **Constants** (if present)      | {% if group.get('identifiers', None) %} {{ expander.expand_identifiers(group['identifiers']) }} {% endif %} |
| **Run regularly** (if present)  | {% if group.get('run_regularly', None) %} {% for run_reg in group['run_regularly'] %} {{ expander.expand_runregularly(run_reg) }} {% endfor %} {% endif %} |