{# Basic information about the SpikeGeneratorGroup #}
{{ tab }}Name {{ (spkgen['name']) }},
with population size {{ (spkgen['N']) }},
has neuron{{ 's' if spkgen['indices']|length > 1 else '' }}: 
{{ expander.prepare_array(spkgen['indices']) }}
that spike at times 
{{ expander.prepare_array(spkgen['times']) }},
with period {{ spkgen['period'] }}.
{{ endll }}

{# Check for the 'run_regularly' key and expand if it exists #}
{% if 'run_regularly' in spkgen %}
    {{ tab }}{{ ('Run regularly:') }}
    {{ endll }}
    {% for run_reg in spkgen['run_regularly'] %}
        {{ expander.expand_runregularly(run_reg) }}
    {% endfor %}
{% endif %}
