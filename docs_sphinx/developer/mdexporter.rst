Markdown exporter
=================

This is the developer documentation for `~brian2tools.mdexport` package, that
provides information about understanding `~brian2tools.baseexport`'s standard dictionary,
standard markdown expander `~brian2tools.mdexport.expander.MdExpander` and writing custom expand functions.

.. contents::
    Overview
    :local:

Standard dictionary
-------------------

The package `~brian2tools.baseexport` collects all the required Brian model information and
arranges them in an intuitive way, that can potentially be used for various
exporters and use cases. Therefore, understanding the representation will be helpful for
further manipulation.

The dictionary contains a list of ``run`` dictionaries with each containing
information about the particular run simulation.

.. code:: python

    # list of run dictionaries
    [
        . . . .
        {   # run dictionary
            duration: <Quantity>,
            components: {
                            . . .
                        },
            initializers_connectors: [. . .],
            inactive: [ . . .]
        },
        . . . .
    ]

Typically, a ``run`` dictionary has four fields,

- ``duration``: simulation length
- ``components``: dictionary of network components like `~brian2.groups.neurongroup.NeuronGroup`,
  `~brian2.synapses.synapses.Synapses`, etc.
- ``initializers_connectors``: list of initializers and synaptic connections
- ``inactive``: list of components that were inactive for the particular run

All the Brian `~brian2.core.network.Network` components that are under ``components`` field, have
components like, `~brian2.groups.neurongroup.NeuronGroup`, `~brian2.synapses.synapses.Synapses`, etc and would look like,

.. code:: python

    {
        'neurongroup': [. . . .],
        'poissongroup': [. . . .],
        'spikegeneratorgroup': [. . . .],
        'statemonitor': [. . . .],
        'synapses': [. . . .],
        . . . .
    }

Each component field has a list of objects of that component defined in the run time.
The dictionary representation of `~brian2.groups.neurongroup.NeuronGroup` and its similar types would look like,

.. code:: python

    neurongroup: [
        {
            'name': <name of the group>,
            'N': <population size>,
            'user_method': <integration method>,
            'equations': <model equations> {
                '<variable name>':{ 'unit': <unit>,
                                    'type': <equation type>
                                    'var_type': <variable dtype>
                                    'expr': <expression>,
                                    'flags': <list of flags>
                }
                . . .
            }
            'events': <events> {
                '<event_name>':{'threshold':{'code': <threshold code>,
                                             'when': <when slot>,
                                             'order': <order slot>,
                                             'dt': <clock dt>
                                },
                                'reset':{'code': <reset code>,
                                         'when': <when slot>,
                                         'order': <order slot>,
                                         'dt': <clock dt>
                                },
                                'refractory': <refractory period>             
                }
                . . .
            }
            'run_regularly': <run_regularly statements>
            [
                {
                    'name': <name of run_regularly>
                    'code': <statement>
                    'dt': <run_regularly clock dt>
                    'when': <when slot of run_regularly>
                    'order': <order slot of run_regularly>
                }
                . . .
            ]
            'when': <when slot of group>,
            'order': <order slot of group>,
            'identifiers': {'<name>': <value>,
            . . .
            }
        }
    ]

Similarly, `~brian2.monitors.statemonitor.StateMonitor` and its similar types are represented like,

.. code:: python

    statemonitor: [
        {
            'name': <name of the group>,
            'source': <name of source>,
            'variables': <list of monitored variables>,
            'record': <list of monitored members>,
            'dt': <time step>
            'when': <when slot of group>,
            'order': <order slot of group>,
        }
    . . .
    ]

As `~brian2.synapses.synapses.Synapses` has many similarity with `~brian2.groups.neurongroup.NeuronGroup`, the dictionary of the same
also looks similar to it, however some of the `~brian2.synapses.synapses.Synapses` specific fields are,

.. code:: python

    synapses: [
        {
            'name': <name of the synapses object>,
            'equations': <model equations> {
                '<variable name>':{ 'unit': <unit>,
                                    'type': <equation type>
                                    'var_type': <variable dtype>
                                    'expr': <expression>,
                                    'flags': <list of flags>
                }
                . . .
            }

            'summed_variables': <summed variables>
            [
                {
                    'target': <name of target group>,
                    'code': <variable name>,
                    'name': <name of the summed variable>,
                    'dt': <time step>,
                    'when': <when slot of run_regularly>,
                    'order': <order slot of run_regularly>
                }
                . . .
            ]

            'pathways': <synaptic pathways>
            [
                {
                    'prepost': <pre or post event>,
                    'event': <event name>,
                    'code': <variable name>,
                    'source': <source group name>,
                    'name': <name of the summed variable>,
                    'clock': <time step>,
                    'when': <when slot of run_regularly>,
                    'order': <order slot of run_regularly>,
                }
                . . .
            ]
        }
    ]

Also, the ``identifiers`` takes into account of `~brian2.input.timedarray.TimedArray` and
`custom user functions <https://brian2.readthedocs.io/en/stable/advanced/functions.html#user-provided-functions>`_.
The ``initializers_connectors`` field contains a list of initializers and synaptic connections,
and their structure would look like,

.. code:: python

    [
        {   <initializer>
            'source': <source group name>,
            'variable': <variable that is initialized>,
            'index': <indices that are affected>,
            'value': <value>, 'type': 'initializer'
        },
        . . .
        {   <connection>
            {'i': <i>, 'j': <j>,
            'probability': <probability of connection>,
            'n_connections': <number of connections>,
            'synapses': <name of the synapse>,
            'source': <source group name>,
            'target': <target group name>, 'type': 'connect'
        }
        . . .
    ]

As a working example, to get the standard dictionary of model description when using
`STDP <https://brian2.readthedocs.io/en/stable/examples/synapses.STDP.html>`_ example,

.. code:: python

    [{'components': 
    {'neurongroup': [{'N': 1,
                    'equations': {'ge': {'expr': '-ge / taue',
                                        'type': 'differential equation',
                                        'unit': radian,
                                        'var_type': 'float'},
                                    'v': {'expr': '(ge * (Ee-v) + El - v) / taum',
                                        'type': 'differential equation',
                                        'unit': volt,
                                        'var_type': 'float'}},
                    'events': {'spike': {'reset': {'code': 'v = vr',
                                                    'dt': 100. * usecond,
                                                    'order': 0,
                                                    'when': 'resets'},
                                        'threshold': {'code': 'v>vt',
                                                        'dt': 100. * usecond,
                                                        'order': 0,
                                                        'when': 'thresholds'}}},
                    'identifiers': {'Ee': 0. * volt,
                                    'El': -74. * mvolt,
                                    'taue': 5. * msecond,
                                    'taum': 10. * msecond,
                                    'vr': -60. * mvolt,
                                    'vt': -54. * mvolt},
                    'name': 'neurongroup',
                    'order': 0,
                    'user_method': 'euler',
                    'when': 'groups'}],
    'poissongroup': [{'N': 1000,
                    'name': 'poissongroup',
                    'rates': 15. * hertz}],
    'spikemonitor': [{'dt': 100. * usecond,
                    'event': 'spike',
                    'name': 'spikemonitor',
                    'order': 1,
                    'record': True,
                    'source': 'poissongroup',
                    'variables': ['i', 't'],
                    'when': 'thresholds'}],
    'statemonitor': [{'dt': 100. * usecond,
                    'n_indices': 2,
                    'name': 'statemonitor',
                    'order': 0,
                    'record': array([0, 1], dtype=int32),
                    'source': 'synapses',
                    'variables': ['w'],
                    'when': 'start'}],
    'synapses': [{'equations': {'Apost': {'expr': '-Apost / taupost',
                                        'flags': ['event-driven'],
                                        'type': 'differential equation',
                                        'unit': radian,
                                        'var_type': 'float'},
                                'Apre': {'expr': '-Apre / taupre',
                                        'flags': ['event-driven'],
                                        'type': 'differential equation',
                                        'unit': radian,
                                        'var_type': 'float'},
                                'w': {'type': 'parameter',
                                    'unit': radian,
                                    'var_type': 'float'}},
                'identifiers': {'dApost': -0.000105,
                                'dApre': 0.0001,
                                'gmax': 0.01,
                                'taupost': 20. * msecond,
                                'taupre': 20. * msecond},
                'name': 'synapses',
                'pathways': [{'clock': 100. * usecond,
                                'code': 'ge += w\n'
                                        'Apre += dApre\n'
                                        'w = clip(w + Apost, 0, gmax)',
                                'event': 'spike',
                                'name': 'synapses_pre',
                                'order': -1,
                                'prepost': 'pre',
                                'source': 'poissongroup',
                                'target': 'neurongroup',
                                'when': 'synapses'},
                                {'clock': 100. * usecond,
                                'code': 'Apost += dApost\n'
                                        'w = clip(w + Apre, 0, gmax)',
                                'event': 'spike',
                                'name': 'synapses_post',
                                'order': 1,
                                'prepost': 'post',
                                'source': 'neurongroup',
                                'target': 'poissongroup',
                                'when': 'synapses'}],
                'source': 'poissongroup',
                'target': 'neurongroup'}]},
    'duration': 100. * second,
    'initializers_connectors': [{'index': True,
                                'source': 'poissongroup',
                                'type': 'initializer',
                                'value': 15. * hertz,
                                'variable': 'rates'},
                                {'n_connections': 1,
                                'probability': 1,
                                'source': 'poissongroup',
                                'synapses': 'synapses',
                                'target': 'neurongroup',
                                'type': 'connect'},
                                {'identifiers': {'gmax': 0.01},
                                'index': 'True',
                                'source': 'synapses',
                                'type': 'initializer',
                                'value': 'rand() * gmax',
                                'variable': 'w'}]}]


MdExpander
----------

To use the dictionary representation for creating markdown strings, by
default `~brian2tools.mdexport.expander.MdExpander` class is used.
The class contains expand functions for different Brian components,
such that the user can easily override the particular function without
affecting others. Also, different options can be given during the instantiation of the object
and pass to the `~brian2.devices.device.set_device` or ``device.build()``.

As a simple example, to use GitHub based markdown rendering for mathematical statements,
and use Brian specific jargons,

.. code:: python

    from brian2tools import MdExpander  # import the standard expander
    # custom expander
    custom = MdExpander(github_md=True, brian_verbose=True)
    set_device('markdown', expander=custom)  # pass the custom expander

Details about the monitors are not included by default in the output markdown and to include
them,

.. code:: python

    # custom expander to include monitors
    custom_with_monitors = MdExpander(include_monitors=True)
    set_device('markdown', expander=custom_with_monitors)

Also, the order of variable initializations and `~brian2.synapses.synapses.Synapses.connect` statements
are not shown in the markdown output by default, this may likely result to inaccurate results, when the
values of variables during synaptic connections are contingent upon their order. In that case, the order
shall be included to markdown output as,

.. code:: python

    # custom expander to include monitors
    custom = MdExpander(keep_initializer_order=True)
    set_device('markdown', expander=custom)

The modified output with details about the order of initialization and Synaptic connection,
when running on the :ref:`working_example_label` would look like,

.. raw:: html

    <div style="background-color:bisque;">
    <h1 id="network-details">Network details</h1>
    <p><strong>Neuron population :</strong></p>
    <ul>
    <li><p>Group <strong>neurongroup</strong>, consisting of <strong>1</strong> neurons.</p>
    <p>  <strong>Model dynamics:</strong></p>
    <p>  <img src="https://render.githubusercontent.com/render/math?math=\frac{d}{d t} v">=<img src="https://render.githubusercontent.com/render/math?math=\frac{El + ge \cdot \left(Ee - v\right) - v}{taum}"></p>
    <p>  <img src="https://render.githubusercontent.com/render/math?math=\frac{d}{d t} ge">=<img src="https://render.githubusercontent.com/render/math?math=- \frac{ge}{taue}"></p>
    <p>  The equations are integrated with the &#39;euler&#39; method.</p>
    <p>  <strong>Events:</strong></p>
    <p>  If <img src="https://render.githubusercontent.com/render/math?math=v \gt vt">, a <strong>spike</strong> event is triggered and <img src="https://render.githubusercontent.com/render/math?math=v">&#8592;<img src="https://render.githubusercontent.com/render/math?math=vr">.</p>
    
    <p>  <strong>Constants:</strong>
    <img src="https://render.githubusercontent.com/render/math?math=El">= <img src="https://render.githubusercontent.com/render/math?math=-74.0\,\mathrm{m}\,\mathrm{V}">, <img src="https://render.githubusercontent.com/render/math?math=Ee">= <img src="https://render.githubusercontent.com/render/math?math=0.0\,\mathrm{V}">, <img src="https://render.githubusercontent.com/render/math?math=taue">= <img src="https://render.githubusercontent.com/render/math?math=5.0\,\mathrm{m}\,\mathrm{s}">, <img src="https://render.githubusercontent.com/render/math?math=taum">= <img src="https://render.githubusercontent.com/render/math?math=10.0\,\mathrm{m}\,\mathrm{s}">, <img src="https://render.githubusercontent.com/render/math?math=vt">= <img src="https://render.githubusercontent.com/render/math?math=-54.0\,\mathrm{m}\,\mathrm{V}">, and <img src="https://render.githubusercontent.com/render/math?math=vr">= <img src="https://render.githubusercontent.com/render/math?math=-60.0\,\mathrm{m}\,\mathrm{V}"></p>
    </li>
    </ul>
    <p><strong>Poisson spike source :</strong></p>
    <ul>
    <li>Name <strong>poissongroup</strong>, with population size <strong>1000</strong> and rate as <img src="https://render.githubusercontent.com/render/math?math=15.0\,\mathrm{Hz}">.</li>
    </ul>
    <p><strong>Synapse :</strong></p>
    <ul>
    <li><p>Connections <strong>synapses</strong>, connecting <em>poissongroup</em> to <em>neurongroup</em>.</p>
    <p><strong>Model dynamics:</strong></p>
    <p>Parameter <img src="https://render.githubusercontent.com/render/math?math=w"> (dimensionless)</p>
    <p><img src="https://render.githubusercontent.com/render/math?math=\frac{d}{d t} Apost">=<img src="https://render.githubusercontent.com/render/math?math=- \frac{Apost}{taupost}"></p>
    <p><img src="https://render.githubusercontent.com/render/math?math=\frac{d}{d t} Apre">=<img src="https://render.githubusercontent.com/render/math?math=- \frac{Apre}{taupre}"></p>
    <p>For each <strong>pre-synaptic</strong> spike: Increase <img src="https://render.githubusercontent.com/render/math?math=ge"> by <img src="https://render.githubusercontent.com/render/math?math=w">, Increase <img src="https://render.githubusercontent.com/render/math?math=Apre"> by <img src="https://render.githubusercontent.com/render/math?math=dApre">, <img src="https://render.githubusercontent.com/render/math?math=w">&#8592;<img src="https://render.githubusercontent.com/render/math?math=\operatorname{clip}{\left(Apost + w,0,gmax \right)}"></p>
    <p>For each <strong>post-synaptic</strong> spike: Increase <img src="https://render.githubusercontent.com/render/math?math=Apost"> by <img src="https://render.githubusercontent.com/render/math?math=dApost">, <img src="https://render.githubusercontent.com/render/math?math=w">&#8592;<img src="https://render.githubusercontent.com/render/math?math=\operatorname{clip}{\left(Apre + w,0,gmax \right)}"></p>
    <p><strong>Constants:</strong>
    <img src="https://render.githubusercontent.com/render/math?math=dApre">= <img src="https://render.githubusercontent.com/render/math?math=0.0001">, <img src="https://render.githubusercontent.com/render/math?math=dApost">= <img src="https://render.githubusercontent.com/render/math?math=-0.000105">, <img src="https://render.githubusercontent.com/render/math?math=taupre">= <img src="https://render.githubusercontent.com/render/math?math=20.0\,\mathrm{m}\,\mathrm{s}">, <img src="https://render.githubusercontent.com/render/math?math=taupost">= <img src="https://render.githubusercontent.com/render/math?math=20.0\,\mathrm{m}\,\mathrm{s}">, and <img src="https://render.githubusercontent.com/render/math?math=gmax">= <img src="https://render.githubusercontent.com/render/math?math=0.01"></p>
    </li>
    </ul>
    <p><strong>Initializing at start</strong> and <strong>Synaptic connection :</strong></p>
    <ul>
    <li><p>Variable <img src="https://render.githubusercontent.com/render/math?math=rates"> of <em>poissongroup</em> initialized with <img src="https://render.githubusercontent.com/render/math?math=15.0\,\mathrm{Hz}"></p>
    </li>
    <li><p>Connection from <em>poissongroup</em> to <em>neurongroup</em>. Pairwise connections.</p>
    </li>
    <li><p>Variable <img src="https://render.githubusercontent.com/render/math?math=w"> of <em>synapses</em> initialized with <img src="https://render.githubusercontent.com/render/math?math=gmax \cdot \mathcal{U}{\left(0, 1\right)}">, where <img src="https://render.githubusercontent.com/render/math?math=gmax">= <img src="https://render.githubusercontent.com/render/math?math=0.01">.</p>
    </li>
    </ul>
    <p>The simulation was run for <strong>100. s</strong></p>
    </div>


Similarly, ``author`` and ``add_meta`` options can also be customized during object instantiation, to
add author name and meta data respectively in the header of the markdown output.

Typically, expand function of the component would follow the structure similar to,

.. code:: python

    def expand_object(self, object_dict):
        # use object_dict information to write md_string
        md_string = . . . object_dict['field_A']
        return md_string

However, enumerating components like ``identifiers``, ``pathways`` have two functions in which the first
one simply loops the list and the second one expands the member. For example, with ``identifiers``,

.. code:: python

    def expand_identifiers(self, identifiers_list):
        # calls `expand_identifier` iteratively
        markdown_str = ''
        for identifier in identifiers_list:
            . . . 
            markdown_str += self.expand_identifier(identifier)
        return markdown_str

    def expand_identifier(self, identifier):
        # individual identifier expander
        markdown_str = ''
        . . . # use identifier dict to write markdown strings
        return markdown_str

All the individual expand functions are tied to `~brian2tools.mdexport.expander.MdExpander.create_md_string` function that calls and collects
all the returned markdown strings to pass it to ``device.md_text``


Writing custom expand class
---------------------------

With the understanding of standard dictionary representation and default markdown expand class (`~brian2tools.mdexport.expander.MdExpander`),
writing custom expand class becomes very straightforward. As a working example, the custom expander
class to write equations in a table like format,

.. code:: python

    from brian2tools import MdExpander
    from markdown_strings import table  # import table from markdown_strings

    # custom expander class to do custom modifications for model equations
    class Dynamics_table(MdExpander):

        def expand_equation(self, var, equation):
            # if differential equation pass `differential` flag as `True` to
            # render_expression()
            if equation['type'] == 'differential equation':
                return (self.render_expression(var, differential=True) +
                            '=' + self.render_expression(equation['expr']))
            else:
                return (self.render_expression(var) +
                            '=' + self.render_expression(equation['expr']))

        def expand_equations(self, equations):
            diff_rend_eqn = ['Differential equations']
            sub_rend_eqn = ['Sub-Expressions']
            # loop over
            for (var, eqn) in equations.items():
                if eqn['type'] == 'differential equation':
                    diff_rend_eqn.append(self.expand_equation(var, eqn))
                if eqn['type'] == 'subexpression':
                    sub_rend_eqn.append(self.expand_equation(var, eqn))

            # now pad space for shorter one
            if len(diff_rend_eqn) > len(sub_rend_eqn):
                shorter = diff_rend_eqn
                longer = sub_rend_eqn
            else:
                shorter = sub_rend_eqn
                longer = diff_rend_eqn
            for _ in range(len(longer) - len(shorter)):
                shorter.append('')

            # return table of rendered equations
            return table([shorter, longer])

    custom = Dynamics_table()
    set_device('markdown', expander=custom)  # pass the custom expander object

when using the above custom class with `COBAHH <https://brian2.readthedocs.io/en/stable/examples/COBAHH.html>`_ example, the equation part would
look like,

.. raw:: html

    <div style="background-color:bisque;">
    <p><strong>Dynamics:</strong></p>
    <table>
    <thead>
    <tr>
    <th>Sub-Expressions</th>
    <th>Differential equations</th>
    </tr>
    </thead>
    <tbody>
    <tr>
    <td><img src="https://render.githubusercontent.com/render/math?math=\alpha\_{n}">=<img src="https://render.githubusercontent.com/render/math?math=\frac{0.16}{ms.{exprel}{\left(\frac{VT + 15.mV - v}{5.mV} \right)}}"></td>
    <td><img src="https://render.githubusercontent.com/render/math?math=\frac{d}{d t} n">=<img src="https://render.githubusercontent.com/render/math?math=\alpha\_{n}.\left(1 - n\right) - \beta\_{n}.n"></td>
    </tr>
    <tr>
    <td><img src="https://render.githubusercontent.com/render/math?math=\alpha\_{h}">=<img src="https://render.githubusercontent.com/render/math?math=\frac{0.128.e^{\frac{VT + 17.mV - v}{18.mV}}}{ms}"></td>
    <td><img src="https://render.githubusercontent.com/render/math?math=\frac{d}{d t} v">=<img src="https://render.githubusercontent.com/render/math?math=\frac{- g\_{kd}.n^{4}.\left(- EK + v\right) - g\_{na}.h.m^{3}.\left(- ENa + v\right) + ge.\left(Ee - v\right) + gi.\left(Ei - v\right) + gl.\left(El - v\right)}{Cm}"></td>
    </tr>
    <tr>
    <td><img src="https://render.githubusercontent.com/render/math?math=\beta\_{m}">=<img src="https://render.githubusercontent.com/render/math?math=\frac{1.4}{ms.{exprel}{\left(\frac{- VT - 40.mV + v}{5.mV} \right)}}"></td>
    <td><img src="https://render.githubusercontent.com/render/math?math=\frac{d}{d t} gi">=<img src="https://render.githubusercontent.com/render/math?math=- \frac{1.0.gi}{taui}"></td>
    </tr>
    <tr>
    <td><img src="https://render.githubusercontent.com/render/math?math=\alpha\_{m}">=<img src="https://render.githubusercontent.com/render/math?math=\frac{1.28}{ms.{exprel}{\left(\frac{VT + 13.mV - v}{4.mV} \right)}}"></td>
    <td><img src="https://render.githubusercontent.com/render/math?math=\frac{d}{d t} h">=<img src="https://render.githubusercontent.com/render/math?math=\alpha\_{h}.\left(1 - h\right) - \beta\_{h}.h"></td>
    </tr>
    <tr>
    <td><img src="https://render.githubusercontent.com/render/math?math=\beta\_{n}">=<img src="https://render.githubusercontent.com/render/math?math=\frac{0.5.e^{\frac{VT + 10.mV - v}{40.mV}}}{ms}"></td>
    <td><img src="https://render.githubusercontent.com/render/math?math=\frac{d}{d t} ge">=<img src="https://render.githubusercontent.com/render/math?math=- \frac{1.0.ge}{taue}"></td>
    </tr>
    <tr>
    <td><img src="https://render.githubusercontent.com/render/math?math=\beta\_{h}">=<img src="https://render.githubusercontent.com/render/math?math=\frac{4.0}{ms.\left(e^{\frac{VT + 40.mV - v}{5.mV}} + 1\right)}"></td>
    <td><img src="https://render.githubusercontent.com/render/math?math=\frac{d}{d t} m">=<img src="https://render.githubusercontent.com/render/math?math=\alpha\_{m}.\left(1 - m\right) - \beta\_{m}.m"></td>
    </tr>
    </tbody>
    </table>
    </div>
