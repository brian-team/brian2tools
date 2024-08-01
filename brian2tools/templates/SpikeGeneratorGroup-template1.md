{# Jinja2 template for SpikeGeneratorGroup in table format #}

|-------------------------------|------------------------------------------------|
| **Name**                      | {{ spkgen['name'] }}                           |
| **Population Size**           | {{ spkgen['N'] }}                              |
| **Neurons**                   | {{ expander.prepare_array(spkgen['indices']) }}    |
| **Spike Times**               | {{ expander.prepare_array(spkgen['times']) }}      |
| **Period**                    | {{ spkgen['period'] }}                         |
| **Run Regularly** (if present) | {% if 'run_regularly' in spkgen %} {% for run_reg in spkgen['run_regularly'] %} {{ expander.expand_runregularly(run_reg) }}{% if not loop.last %}\n{% endif %}{% endfor %} {% endif %} |
