{# Basic information about the SpikeGeneratorGroup #}
{{ tab }}Name {{ (group['name']) }},
with population size {{ (group['N']) }},
has neuron{{ 's' if group['indices']|length > 1 else '' }}: 
{{ expander.prepare_array(group['indices']) }}
that spike at times 
{{ expander.prepare_array(group['times']) }},
with period {{ group['period'] }}.
{{ endll }}

{# Check for the 'run_regularly' key and expand if it exists #}
{% if 'run_regularly' in group %}
    {{ tab }}{{ ('Run regularly:') }}
    {{ endll }}
    {% for run_reg in group['run_regularly'] %}
        {{ expander.expand_runregularly(run_reg) }}
    {% endfor %}
{% endif %}
