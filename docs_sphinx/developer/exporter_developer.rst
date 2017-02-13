NeuroML exporter
================

.. contents::
    Overview
    :local:

The main work of the exporter is done in the `~brian2tools.nmlexport.lemsexport`
module.

It consists of two main classes:

- `~brian2tools.nmlexport.lemsexport.NMLExporter` - responsible for building
  the NeuroML2/LEMS model.

- `~brian2tools.nmlexport.lemsexport.LEMSDevice` - responsible for code
  generation. It gathers all variables needed to describe the model and calls
  ``NMLExporter`` with well-prepared parameters.

NMLExporter
-----------
The whole process of building NeuroML model starts with calling the
``create_lems_model`` method. It selects crucial Brian 2 objects to further
parse and pass them to respective methods.

.. code:: python

        if network is None:
            net = Network(collect(level=1))
        else:
            net = network

        if not constants_file:
            self._model.add(lems.Include(LEMS_CONSTANTS_XML))
        else:
            self._model.add(lems.Include(constants_file))
        includes = set(includes)
        for incl in INCLUDES:
            includes.add(incl)
        neuron_groups  = [o for o in net.objects if type(o) is NeuronGroup]
        state_monitors = [o for o in net.objects if type(o) is StateMonitor]
        spike_monitors = [o for o in net.objects if type(o) is SpikeMonitor]
        
        for o in net.objects:
            if type(o) not in [NeuronGroup, StateMonitor, SpikeMonitor,
                               Thresholder, Resetter, StateUpdater]:
                logger.warn("""{} export functionality
                               is not implemented yet.""".format(type(o).__name__))

        # Thresholder, Resetter, StateUpdater are not interesting from our perspective
        if len(netinputs)>0:
            includes.add(LEMS_INPUTS)
        for incl in includes:
            self.add_include(incl)
        # First step is to add individual neuron deifinitions and initialize
        # them by MultiInstantiate
        for e, obj in enumerate(neuron_groups):
            self.add_neurongroup(obj, e, namespace, initializers)

Neuron Group
~~~~~~~~~~~~
A method ``add_neurongroup`` requires more attention. This is the method 
responsible for building cell model in LEMS (as so-called ``ComponentType``) 
and initializing it when necessary. 

In order to build a whole network of cells with different initial values, 
we need to use the ``MultiInstantiate`` LEMS tag. A method ``make_multiinstantiate``
does this job. It iterates over all parameters and analyses equation
to find those with iterator variable ``i``. Such variables are initialized
in a ``MultiInstantiate`` loop at the beginning of a simulation.

More details about the methods described above can be found in the code comments.

DOM structure
~~~~~~~~~~~~~

Until this point the whole model is stored in `NMLExporter._model`, because
the method ``add_neurongroup`` takes advantage of ``pylems`` module to create
a XML structure. After that we export it to ``self._dommodel`` and rather 
use NeuroML2 specific content. To extend it one may use
``self._extend_dommodel()`` method, giving as parameter a proper DOM structure
(built for instance using python ``xml.dom.minidom``).

.. code:: python

        # DOM structure of the whole model is constructed below
        self._dommodel = self._model.export_to_dom()
        # input support - currently only Poisson Inputs
        for e, obj in enumerate(netinputs):
            self.add_input(obj, counter=e)
        # A population should be created in *make_multiinstantiate*
        # so we can add it to our DOM structure.
        if self._population:
            self._extend_dommodel(self._population)
        # if some State or Spike Monitors occur we support them by
        # Simulation tag
        self._model_namespace['simulname'] = "sim1"
        self._simulation = NeuroMLSimulation(self._model_namespace['simulname'],
                                             self._model_namespace['networkname'])
        for e, obj in enumerate(state_monitors):
            self.add_statemonitor(obj, filename=recordingsname, outputfile=True)
        for e, obj in enumerate(spike_monitors):
            self.add_spikemonitor(obj, filename=recordingsname)


Some of the NeuroML structures are already implemented in ``supporting.py``. For example:

- ``NeuroMLSimulation`` - describes Simulation, adds plot and lines, adds outputfiles for spikes and voltage recordings;

- ``NeuroMLSimpleNetwork`` - creates a network of cells given some ComponentType;

- ``NeuroMLTarget`` - picks target for simulation runner.

At the end of the model parsing, a simulation tag is built and added with a target pointing to it.

.. code:: python

        simulation = self._simulation.build()
        self._extend_dommodel(simulation)
        target = NeuroMLTarget(self._model_namespace['simulname'])
        target = target.build()
        self._extend_dommodel(target)

You may access the final DOM structure by accessing the ``model``` property or
export it to a XML file by calling the ``export_to_file()`` method of the
``NMLExporter`` object.

Model namespace
~~~~~~~~~~~~~~~
In many places of the code a dictionary ``self._model_namespace`` is used. 
As LEMS used identifiers ``id`` to name almost all of its components, we 
want to be consistent in naming them. The dictionary stores names of 
model's components and allows to refer it later in the code.

LEMSDevice
----------
``LEMSDevice`` allows you to take advantage of Brian 2's code generation mechanism.
It makes usage of the module easier, as it means for user that they just 
need to import ``brian2tools.nmlexport`` and set the device
``neuroml2`` like this:

.. code:: python

    import brian2lems.nmlexport

    set_device('neuroml2', filename="ifcgmtest.xml")

In the class init a flag ``self.build_on_run`` was set to ``True`` which 
means that exporter starts working immediately after encountering the ``run``
statement.

.. code:: python

    def __init__(self):
        super(LEMSDevice, self).__init__()
        self.runs = []
        self.assignments = []
        self.build_on_run = True
        self.build_options = None
        self.has_been_run = False

First of all method ``network_run`` is called which gathers of necessary
variables from the script or function namespaces and passes it to ``build`` 
method. In ``build`` we select all needed variables to separate dictionaries, 
create a name of the recording files and eventually build the exporter.

.. code:: python

        initializers = {}
        for descriptions, duration, namespace, assignments in self.runs:
            for assignment in assignments:
                if not assignment[2] in initializers:
                    initializers[assignment[2]] = assignment[-1]
        if len(self.runs) > 1:
            raise NotImplementedError("Currently only single run is supported.")
        if len(filename.split("."))!=1:
            filename_ = 'recording_' + filename.split(".")[0]
        else:
            filename_ = 'recording_' + filename
        exporter = NMLExporter()
        exporter.create_lems_model(self.network, namespace=namespace,
                                                 initializers=initializers,
                                                 recordingsname=filename_)
        exporter.export_to_file(filename)

LEMS Unit Constants
~~~~~~~~~~~~~~~~~~~
Last lines of the method are saving ``LemsConstantUnit.xml`` file 
alongside with our model file. This is due to the fact that in some places 
of mathematical expressions LEMS requires unitless variables, e.g. instead of 
``1 mm`` it wants ``0.001``. So we store most popular units transformed to 
constants in a separate file which is included in the model file header.

.. code:: python

    if lems_const_save:
        with open(os.path.join(nmlcdpath, LEMS_CONSTANTS_XML), 'r') as f:
            with open(LEMS_CONSTANTS_XML, 'w') as fout:
                fout.write(f.read())


Other modules
-------------
If you want to know more about other scripts included in package
( `~brian2tools.nmlexport.lemsrendering`, `~brian2tools.nmlexport.supporting`,
`~brian2tools.nmlexport.cgmhelper`), please read their docstrings or comments
included in the code.


TODO
----
- synapses support;

First attempt to make synapses export work was made during GSOC period. The problem with that
feature is related to the fact that NeuroML and brian2 internal synapses implementation differs substantially.
For instance, in NeuroML there are no predefined rules for connections, but user needs to explicitly define a synapse.
Moreover, in Brian 2, for efficiency reasons, postsynaptic potentials are
normally modeled in the post-synaptic cell (for linearly summating synapses,
this is equivalent but much more efficient), whereas in NeuroML they are modeled
as part of the synapse (simulation speed is not an issue here).

- network input support;

Although there are some classes supporting ``PoissonInput`` in the ``supporting.py``, full functionality
of  input is still not provided, as it is stongly linked with above synapses problems.
