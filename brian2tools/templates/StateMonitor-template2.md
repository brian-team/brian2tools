{# Jinja2 template for Statemon in table format #}

|-------------------------------|--------------------------------------------------|
| **Monitored Variables**       | {{ statemon['variables'] | join(', ', expander.render_expression) }} |
| **Source**                    | {{ expander.expand_SpikeSource(statemon['source']) }} |
| **Recording**                 | {% if statemon['record'] is boolean %}
                                      {% if statemon['record'] %}
                                        for all members
                                      {% else %}
                                        for no member
                                      {% endif %}
                                    {% else %}
                                      {% if statemon['record']|length == 0 %}
                                        for no member
                                      {% else %}
                                        for member{{ expander.check_plural(statemon['record']) }}: {{ statemon['record'] | join(', ') }}
                                      {% endif %}
                                    {% endif %}
