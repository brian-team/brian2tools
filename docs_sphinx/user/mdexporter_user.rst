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
threshold (increases with each spike) and run in debug mode that prints the
output markdown text

.. code:: python

    from brian2 import *
    import brian2tools.mdexport

    set_device('markdown', build_on_run=False)  # manual build

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

    device.build(debug=True)

The non-rendered output would look like,

.. code::

    # Network details
    The Network consists of **1** simulation run
    _______________________________________________________________________________

    Duration of simulation is **2. s**

    **Neuron group defined:**
    - Name **neurongroup**, with population size **1**.

        **Dynamics:**

        $\frac{d}{d t} vt$=$\frac{10.mV - vt}{15.ms}$, where unit of $vt$ is V

        $\frac{d}{d t} v$=$- \frac{v}{10.ms}$, where unit of $v$ is V

        exact method is used for integration

        **Events:**

        Event **spike**, after $v \gt vt$, , $v$&#8592;$0$, $vt$+=$3.mV$, 


    **Poisson spike source defined:**
    - 	Name **poissongroup**, with population size **1** and rate as $0.5 kHz$.


    **Activity recorders defined:**
    -   Monitors variable: $vt$ of neurongroup for all members
    -   Monitors variable: $v$ of neurongroup for all members
    **Spiking activity recorder defined:**
    - 	Monitors variables: $i$,$t$,$v$ of neurongroup, for member: True when event **spike** is triggered.


    **Synapse defined:**
    - 	From poissongroup to neurongroup

        **Pathways:**

        On **pre** of event spike statements: $v$+=$3.mV$ executed


    **Initializing values at starting:**
    - Variable $vt$ of neurongroup initialized with $10. mV$ to all members

    - Variable $rates$ of poissongroup initialized with $0.5 kHz$ to all members


    **Synaptic Connection defined:**
    - Connection from poissongroup to neurongroup

Similar to other device modes, to inform Brian to run in the exporter mode, 
the user should make the minimal changes like importing the required package
and mentioning device `markdown` in `set_device()`.

User options
------------

Various user options (apart from that of `RuntimeDevice`)shall be passed to 
`set_device()` or in `device.build()` and some important options are,

``expand_class``
    Expander class, that contains expander functions to get information from
    `baseexport` and use them to write markdown text. By default, `Std_mdexpander`
    is used but user can override the expand functions to have custom model
    descriptions (see `developer documentation` for writing custom expander 
    class).

    A small example to use custom expand_class for the above example,

    .. code::

        class Custom_expander(Std_mdexpander):
            # override expand function
            # neuron: is the standard dictionary of NeuronGroup
            def expand_NeuronGroup(self, neuron):
                md_str = ''
                # use the dictionary information
                # expand_equations() is expand function for model equations
                md_str += ('My population is ' + neuron['N'] +
                        'my dynamics is ' +
                        self.expand_equations(neuron['equations']))
                return md_str

        set_device('markdown', expand_class=Custom_expander)
        . . . .

    would replace the standard markdown description of `NeuronGroup` with 
    `Custom_expander`'s `expand_NeuronGroup()`

``filename``
    Filename to write output markdown text. To use the same filename  of the user
    script, `''` (empty string) shall be passed. By default, no file writing is
    done

``brian_verbose``
    Whether to use Brian based names. By default, set as `False` for easy understanding
    to even non-Brian users. For the above adaptive threshold example, when 
    `brian_verbose` is set as `True`, the changes would look like,

    .. code::

        ...
        **StateMonitors defined:**
        ...

        **NeuronGroup defined:**
        ...

        **PoissonGroup defined:**
        ...

        **SpikeMonitor defined:**
        ...

        **Initializers defined:**
        ...

``author``
    Author name to add in meta field

``add_meta``
    If `True`, the meta data is added to the header of output markdown.
    By default, set as `False`.

``github_md``
    If set as `True`, the output string will use images to show rendered
    mathematical equations or symbols. Shall be used in non-Mathjax based
    compilers like GitHub

Limitations
-----------

Since the package uses `baseexport` in the background, all the limitations
applicable to `baseexport` applies here too
