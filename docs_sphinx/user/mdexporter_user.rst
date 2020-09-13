Markdown exporter
=================

This is the user documentation of `~brian2tools.mdexport` package, that
provides functionality to describe Brian 2 models in Markdown. The Markdown
description contains human-readable information of Brian components defined
in the `Network`. In background, the exporter uses `~brian2tools.baseexport`
to collect information from the run time and expand them to markdown strings.

.. contents::
    Overview
    :local:

Working example
---------------

As a quick start to use the exporter, let us take a simple model with adaptive
threshold (increases with each spike) and write the markdown output in a file

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
    run(2*second, report='text')

The file `model_description.md` would look like,

.. raw:: html

    <div style="background-color:bisque;">

    <h1 id="networkdetails">Network details</h1>

    <p>The Network consist of <strong>1</strong> simulation                     run</p>

    <hr />

    <h3 id="run1details">Run 1 details</h3>

    <p>Duration of simulation is <strong>2. s</strong></p>

    <p><strong>Neuron group :</strong></p>

    <ul>
    <li><p>Name <strong>neurongroup</strong>, with                 population size <strong>1</strong>.</p>

    <p><strong>Dynamics:</strong></p>

    <p><img src="https://render.githubusercontent.com/render/math?math=\frac{d}{d t} v">=<img src="https://render.githubusercontent.com/render/math?math=- \frac{v}{10.ms}">, where unit of <img src="https://render.githubusercontent.com/render/math?math=v"> is V</p>

    <p><img src="https://render.githubusercontent.com/render/math?math=\frac{d}{d t} vt">=<img src="https://render.githubusercontent.com/render/math?math=\frac{10.mV - vt}{15.ms}">, where unit of <img src="https://render.githubusercontent.com/render/math?math=vt"> is V</p>

    <p>exact method is used for integration</p>

    <p><strong>Events:</strong></p>

    <p>Event <strong>spike</strong>, after <img src="https://render.githubusercontent.com/render/math?math=v \gt vt">, <img src="https://render.githubusercontent.com/render/math?math=v">&#8592;<img src="https://render.githubusercontent.com/render/math?math=0">, <img src="https://render.githubusercontent.com/render/math?math=vt">+=<img src="https://render.githubusercontent.com/render/math?math=3.mV"></p></li>
    </ul>

    <p><strong>Poisson spike source :</strong></p>

    <ul>
    <li>Name <strong>poissongroup</strong>, with                 population size <strong>1</strong> and rate as <img src="https://render.githubusercontent.com/render/math?math=0.5 kHz">.</li>
    </ul>

    <p><strong>Synapse :</strong></p>

    <ul>
    <li><p>From poissongroup to neurongroup</p>

    <p><strong>Pathways:</strong></p>

    <p>On <strong>pre</strong> of event spike statements: <img src="https://render.githubusercontent.com/render/math?math=v">+=<img src="https://render.githubusercontent.com/render/math?math=3.mV"> executed</p></li>
    </ul>

    <p><strong>Activity recorder :</strong></p>

    <ul>
    <li>Monitors variable: <img src="https://render.githubusercontent.com/render/math?math=vt"> of neurongroup for all members-     Monitors variable: <img src="https://render.githubusercontent.com/render/math?math=v"> of neurongroup for all members</li>
    </ul>

    <p><strong>Spiking activity recorder :</strong></p>

    <ul>
    <li>Monitors variables: <img src="https://render.githubusercontent.com/render/math?math=t">,<img src="https://render.githubusercontent.com/render/math?math=v">,<img src="https://render.githubusercontent.com/render/math?math=i"> of neurongroup for all members when event <strong>spike</strong> is triggered.</li>
    </ul>

    <p><strong>Initializing at start</strong> and <strong>Synaptic connection :</strong></p>

    <ul>
    <li><p>Variable <img src="https://render.githubusercontent.com/render/math?math=vt"> of neurongroup initialized with <img src="https://render.githubusercontent.com/render/math?math=10. mV"> to all members</p></li>

    <li><p>Variable <img src="https://render.githubusercontent.com/render/math?math=rates"> of poissongroup initialized with <img src="https://render.githubusercontent.com/render/math?math=0.5 kHz"> to all members</p></li>

    <li><p>Connection from poissongroup to neurongroup</p></li>
    </ul>
    </div>

Similar to other device modes, to inform Brian to run in the exporter mode, 
the user should make the minimal changes of importing the required package
and mentioning device `markdown` in `set_device()`.

The above example can be run in `debug` mode to print the output in stdout. In that case,
the changes to the above example are,


.. code:: python

    from brian2 import *
    import brian2tools.mdexport
    # set device 'markdown'
    set_device('markdown', build_on_run=False)  # allow for manual build

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
    run(2*second, report='text')

    device.build()  # to print the output in stdout

Also, the markdown output can be accessed from `device.md_text`.

Exporter specific build options
-------------------------------

Various options (apart from that of `RuntimeDevice`) shall be passed to 
`set_device()` or in `device.build()`. Exporter specific ``build options are,

``expand_class``
    Expander class, that contains expander functions to get information from
    `baseexport` and use them to write markdown text. By default, `MdExpander`
    is used. The default argument values can be changed and expand functions can be
    overridden (see `developer documentation` for more details and how to write custom
    expander functions).

    A small example to use custom value for `github_md` of `expand_class` that
    specifies, whether rendered output should be non-Mathjax based
    (as in compilers like GitHub)

    .. code::
        . . . .
        from brian2tools.mdexport.expander import MdExpander
        # change default value
        custom_options = MdExpander(github_md=True)
        set_device('markdown', expand_class=custom_options)  # pass the custom expander object
        . . . .

``filename``
    Filename to write output markdown text. To use the same filename  of the user
    script, `''` (empty string) shall be passed. By default, no file writing is
    done

Limitations
-----------

Since the package uses `baseexport` in the background, all the limitations
applicable to `baseexport` applies here too
