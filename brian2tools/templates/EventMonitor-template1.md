{# Jinja2 template for EventMonitor in table format #}

|-------------------------------|--------------------------------------------------|
| **Monitored Variables**       | {{ eventmon['variables'] | join(', ', expander.render_expression) }} |
| **Source**                    | {{ expander.expand_SpikeSource(eventmon['source']) }} |
| **Recording**                 | {% if eventmon['record'] is boolean %}
                                      {% if eventmon['record'] %}
                                        for all members
                                      {% else %}
                                        for no member
                                      {% endif %}
                                    {% else %}
                                      {% if eventmon['record']|length == 0 %}
                                        for no member
                                      {% else %}
                                        for member{{ expander.check_plural(eventmon['record']) }}: {{ eventmon['record'] | join(', ') }}
                                      {% endif %}
                                    {% endif %}
| **Event Trigger**             | {{ eventmon['event']}}                   |
