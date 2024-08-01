        | **Variable**                     | **Value**                                      |
|---------------------------------|------------------------------------------------|
| **Name**                        | {{ poisngrp['name'] }}                        |
| **Population size**             | {{ poisngrp['N'] }}                           |
| **Rate**                        | {{ render_expression(poisngrp['rates']) }}     |
| **Constants** (if present)      | {% if poisngrp.get('identifiers', None) %} {{ expand_identifiers(poisngrp['identifiers']) }} {% endif %} |
| **Run regularly** (if present)  | {% if poisngrp.get('run_regularly', None) %} {% for run_reg in poisngrp['run_regularly'] %} {{ expand_runregularly(run_reg) }} {% endfor %} {% endif %} |