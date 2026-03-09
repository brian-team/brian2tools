Base exporter
=============

This is the user documentation of the `~brian2tools.baseexport` package, that
provides functionality to represent Brian2 models in a standard dictionary
format. The standard dictionary has a simple and easy to access hierarchy of model
information, that can be used for various model description exporters and custom
descriptions.

The `~brian2tools.baseexport` package is not meant to use directly but to
provide general framework to use other model description exporters on top of it.
However, the standard dictionary can be easily accessed as mentioned in the 
:ref:`Working Example <working_example>` section.

.. contents::
    Overview
    :local:

.. _working_example:

Working example
---------------
Once the ``device.build()`` is called, the standard dictionary can be accessed by the
``device.runs`` variable. To use the high-performance serialization, initialize the 
``furyexporter`` as follows:

.. code:: python

    from brian2 import *
    # Import the new furyexport package
    import brian2tools.baseexport.furyexport
    import pprint 

    # Set the device to your new FuryExporter
    set_device('furyexporter') 

    n = 100
    duration = 1*second
    group = NeuronGroup(n, 'dv/dt = -v / (10*ms) : 1', threshold='v > 1', reset='v = 0')
    group.v = 'rand()'

    run(duration)

    # Access the serialized simulation state
    pprint.pprint(device.runs)

The output standard dictionary would look similar to,

.. code::

    [{'components': {'neurongroup': [{'N': 100,
                                    'equations': {'v': {'expr': '(v_rest - v) / tau',
                                                        'flags': ['unless refractory'],
                                                        'type': 'differential equation',
                                                        'unit': volt,
                                                        'var_type': 'float'},
                                                    'v_rest': {'type': 'parameter',
                                                            'unit': volt,
                                                            'var_type': 'float'}},
                                    'events': {'spike': {'refractory': 5. * msecond,
                                                        'reset': {'code': 'v = v_rest',
                                                                    'dt': 100. * usecond,
                                                                    'order': 0,
                                                                    'when': 'resets'},
                                                        'threshold': {'code': 'v > v_th',
                                                                        'dt': 100. * usecond,
                                                                        'order': 0,
                                                                        'when': 'thresholds'}}},
                                    'identifiers': {'tau': 10. * msecond,
                                                    'v_th': 1. * volt},
                                    'name': 'neurongroup',
                                    'order': 0,
                                    'user_method': 'euler',
                                    'when': 'groups'}],
                    'spikemonitor': [{'dt': 100. * usecond,
                                    'event': 'spike',
                                    'name': 'spikemonitor',
                                    'order': 1,
                                    'record': 0,
                                    'source': 'neurongroup',
                                    'source_size': 100,
                                    'variables': [],
                                    'when': 'thresholds'}],
                    'statemonitor': [{'dt': 100. * usecond,
                                    'n_indices': 100,
                                    'name': 'statemonitor',
                                    'order': 0,
                                    'record': True,
                                    'source': 'neurongroup',
                                    'variables': ['v'],
                                    'when': 'start'}]},
    'duration': 1. * second,
    'initializers_connectors': [{'index': True,
                                'source': 'neurongroup',
                                'type': 'initializer',
                                'value': 0. * volt,
                                'variable': 'v'},
                                {'identifiers': {'N': 100},
                                'index': 'True',
                                'source': 'neurongroup',
                                'type': 'initializer',
                                'value': 'rand() * 20*mV * i / (N-1)',
                                'variable': 'v_rest'}]}]

To the user side, the changes required to use the exporter are very minimal
(very similar to accessing other Brian2 device modes). In the standard Brian code,
adding `~brian2tools.baseexport` import statement and setting device ``exporter``
with proper ``build_options`` will be sufficient to use the exporter. To print the dictionary in ``stdout``,
``debug`` option shall also be used, apart from using ``device.runs`` variable.
The changes required to run in ``debug`` mode for the above example are,

.. code:: python

    from brian2 import *
    import brian2tools.baseexport

    set_device('furyexporter', debug=True)

   . . . .

    run(duration)

Most of the standard dictionary items have the same object type as in Brian2. For instance,
``identifiers`` and ``dt`` fields have values of type `~brian2.units.fundamentalunits.Quantity` but ``N`` (population size)
is of type ``int``.

Limitations
-----------

The Base export currently supports most Brian2 features. Note that:
- Multicompartmental neurons (`~brian2.spatialneuron.spatialneuron.SpatialNeuron`) are still being integrated.
- The ``FuryExporter`` now provides a robust path for state persistence, addressing some previous limitations in the `Network.store`/`restore` workflow.
