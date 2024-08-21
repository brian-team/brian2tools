{# Jinja2 template for SpikeGeneratorGroup in table format #}

|-------------------------------|------------------------------------------------|
| **Name**                      | {{ group['name'] }}                           |
| **Population Size**           | {{ group['N'] }}                              |
| **Neurons**                   | {{ expander.prepare_array(group['indices']) }}    |
| **Spike Times**               | {{ expander.prepare_array(group['times']) }}      |
| **Period**                    | {{ group['period'] }}                         |
| **Run Regularly** (if present) | {% if 'run_regularly' in group %} {% for run_reg in group['run_regularly'] %} {{ expander.expand_runregularly(run_reg) }}{% if not loop.last %}\n{% endif %}{% endfor %} {% endif %} |
