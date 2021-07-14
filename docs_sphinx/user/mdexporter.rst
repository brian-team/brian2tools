Markdown exporter
=================

This is the user documentation of `~brian2tools.mdexport` package, that
provides functionality to describe Brian2 models in Markdown. The markdown
description provides human-readable information of Brian components defined.
In background, the exporter uses the :doc:`baseexporter` to collect information
from the run time and expand them to markdown strings.

.. contents::
    Overview
    :local:

.. _working_example_label:

Working example
---------------

As a quick start to use the package, let us take a simple model with
`adaptive threshold that increases with each spike <https://brian2.readthedocs.io/en/stable/examples/adaptive_threshold.html>`_
and write the markdown output in a file

.. code:: python

    from brian2 import *
    import brian2tools.mdexport
    # set device 'markdown'
    set_device('markdown', filename='model_description')

    eqs = '''
    dv/dt = -v/(10*ms) : volt
    dvt/dt = (10*mV-vt)/(15*ms) : volt
    '''

    reset = '''
    v = 0*mV
    vt += 3*mV
    '''

    IF = NeuronGroup(1, model=eqs, reset=reset, threshold='v>vt',
                    method='exact')
    IF.vt = 10*mV
    PG = PoissonGroup(1, 500 * Hz)

    C = Synapses(PG, IF, on_pre='v += 3*mV')
    C.connect()

    Mv = StateMonitor(IF, 'v', record=True)
    Mvt = StateMonitor(IF, 'vt', record=True)
    # Record the value of v when the threshold is crossed
    M_crossings = SpikeMonitor(IF, variables='v')
    run(2*second)

The rendered file ``model_description.md`` would look like,

.. raw:: html

    <div style="background-color:bisque;">
    <h1 id="network-details">Network details</h1>
    <p><strong>Neuron population :</strong></p>
    <ul>
    <li><p>Group <strong>neurongroup</strong>, consisting of <strong>1</strong> neurons.</p>
    <p>  <strong>Model dynamics:</strong></p>
    <p>  <img src="https://render.githubusercontent.com/render/math?math=\frac{d}{d t} v">=<img src="https://render.githubusercontent.com/render/math?math=- \frac{v}{10 \cdot ms}"></p>
    <p>  <img src="https://render.githubusercontent.com/render/math?math=\frac{d}{d t} vt">=<img src="https://render.githubusercontent.com/render/math?math=\frac{10 \cdot mV - vt}{15 \cdot ms}"></p>
    <p>  The equations are integrated with the &#39;exact&#39; method.</p>
    <p>  <strong>Events:</strong></p>
    <p>  If <img src="https://render.githubusercontent.com/render/math?math=v \gt vt">, a <strong>spike</strong> event is triggered and <img src="https://render.githubusercontent.com/render/math?math=v">&#8592;<img src="https://render.githubusercontent.com/render/math?math=0">, Increase <img src="https://render.githubusercontent.com/render/math?math=vt"> by <img src="https://render.githubusercontent.com/render/math?math=3 \cdot mV">.</p>
    <p>  <strong>Initial values:</strong></p>
    <ul>
    <li>Variable <img src="https://render.githubusercontent.com/render/math?math=vt">= <img src="https://render.githubusercontent.com/render/math?math=10.0\,\mathrm{m}\,\mathrm{V}"></li>
    </ul>
    </li>
    </ul>
    <p><strong>Poisson spike source :</strong></p>
    <ul>
    <li>Name <strong>poissongroup</strong>, with                 population size <strong>1</strong> and rate as <img src="https://render.githubusercontent.com/render/math?math=0.5\,\mathrm{k}\,\mathrm{Hz}">.</li>
    </ul>
    <p><strong>Synapse :</strong></p>
    <ul>
    <li><p>Connections <strong>synapses</strong>, connecting <em>poissongroup</em> to <em>neurongroup</em>    . Pairwise connections.</p>
    <p>For each <strong>pre-synaptic</strong> spike: Increase <img src="https://render.githubusercontent.com/render/math?math=v"> by <img src="https://render.githubusercontent.com/render/math?math=3 \cdot mV"></p>
    </li>
    </ul>
    <p>The simulation was run for <strong>2. s</strong></p>
    </div>

.. note::

    By default, Monitors are not included in markdown output, and the order of variable 
    initializations and `~brian2.synapses.synapses.Synapses.connect` statements are not shown but rather included 
    with the respective objects. However, these default options shall be changed according to one's
    need (see developer documentation of :doc:`../developer/mdexporter` for how to change the default 
    options).

Similar to other Brian2 device modes, to inform Brian to run in the exporter mode,
the minimal changes required are importing the package
and mentioning device ``markdown`` in `~brian2.devices.device.set_device`. The markdown output can be
accessed from ``device.md_text``.

The above example can also be run in ``debug`` mode to print the output in ``stdout``. In that case,
the changes to the above example are,


.. code:: python

    from brian2 import *
    import brian2tools.mdexport
    # set device 'markdown'
    set_device('markdown', debug=True)  # to print the output in stdout
    . . .

    run(2*second)


Exporter specific build options
-------------------------------

Various options (apart from that of `~brian2.devices.device.RuntimeDevice`) shall be passed to 
`~brian2.devices.device.set_device` or in ``device.build()``. Exporter specific ``build_options`` are,

``expander``
    Expander is the object of the call that contains expander functions to get information from
    `~brian2tools.baseexport` and use them to write markdown text. By default, `~brian2tools.mdexport.expander.MdExpander`
    is used. The default argument values can be changed and expand functions can be
    overridden (see developer documentation of :doc:`../developer/mdexporter` for more details and how to write custom
    expander functions).

    A small example to enable ``github_md`` in expander that
    specifies, whether rendered output should be non-Mathjax based
    (as compilers like GitHub)

.. code::

    from brian2tools.mdexport.expander import MdExpander
    # change default value
    custom_options = MdExpander(github_md=True)
    set_device('markdown', expander=custom_options)  # pass the custom expander object
    . . . .

``filename``
    Filename to write output markdown text. To use the same filename  of the user
    script, ``''`` (empty string) shall be passed. By default, no file writing is
    done

Limitations
-----------

Since the package uses `~brian2tools.baseexport` in the background, all the limitations
applicable to `~brian2tools.baseexport` applies here as well
