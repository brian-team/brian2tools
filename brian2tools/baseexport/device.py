from brian2.devices.device import RuntimeDevice
from brian2.devices.device import Device, all_devices
from brian2.core.namespace import get_local_namespace
from brian2.groups import NeuronGroup
from brian2.groups.group import CodeRunner
from brian2.input import PoissonGroup, SpikeGeneratorGroup

from .collector import *
from .helper import _prune_identifiers


class BaseExporter(RuntimeDevice):
    """
    Class defining `ExportDevice` device mode to generate standard dictioanry
    representation of the defined model. The `BaseExporter` class is derived
    from `RuntimeDevice` to inform Brian to run the Network in this mode

    Attributes
    ----------

    network_dic : dict
        Standard dictionary containing network components

    Methods
    -------

    network_run(network, duration, namespace, level, **kwds)
        Function to execute when `Network.run()` statement is encountered

    See Also
    --------
    1. brian2.core.network.Network class
    2. brian2.devices.device.RuntimeDevice class
    3. brian2tools.nmlexport package

    """

    def __init__(self):
        """
        Constructor to define build and run options
        """

        super(BaseExporter, self).__init__()

        self.build_on_run = True
        self.has_been_run = False
        self.available_objs = (NeuronGroup, SpikeGeneratorGroup,
                               PoissonGroup)
        self.initializers = {}
    

    def network_run(self, network, duration, namespace = None, level = 0, 
                                                                **kwds):
        """
        Method to be executed when `Network.run()` is called in `stdformat`
        device mode

        Parameters
        ----------

        network : `brian2.core.network.Network`
            Network object
        
        duration : `brian2.units.fundamentalunits.Quantity`
            The amount of duration to run
        
        namespace : dict, optional
            Additional namespace other than group-specific namespaces.
            If not specfied, collected from local and global scope of `run()`
            statement
        
        level : int, optional
            Depth of the stack frame to look for namespace items

        """

        # `_clocks` is required to run `Network.before_run(namespace)`
        network._clocks = {object.clock for object in network.objects}

        # if namespace not defined
        if namespace is None:
            namespace = get_local_namespace(level + 2)
        # prepare objects using `before_run()`
        network.before_run(namespace)

        self.network_dict = {}  # dictionary with Network components

        # loop through all the objects of network and collect object 
        # specific identifiers
        for object in network.objects:
            # check NeuronGroup
            # TODO shall this be bundeled to common collect_Group()?
            if isinstance(object, NeuronGroup):
                # get dict and identifiers
                neuron_dict, neuron_identifiers = collect_NeuronGroup(object)
                # resolve group-specific identifiers
                neuron_identifiers = object.resolve_all(neuron_identifiers, 
                                                        namespace)
                # prune away unwanted identifiers
                neuron_identifiers = _prune_identifiers(neuron_identifiers)
                # add identifiers field
                neuron_dict['identifiers'] = neuron_identifiers
                # add initializers
                neuron_dict['initializers'] = self.initializers[object.name]
                # check neurongroup key already exists, if not create one
                if 'neurongroup' not in self.network_dict.keys():
                    self.network_dict['neurongroup'] = []
                self.network_dict['neurongroup'].append(neuron_dict)

            # check PoissonGroup
            if isinstance(object, PoissonGroup):
                # get dict and identifiers
                posn_dict, posn_identifiers = collect_PoissonGroup(object)
                # resolve group-specific identifiers
                posn_identifiers = object.resolve_all(posn_identifiers,
                                                      namespace)
                # prune away unwanted identifiers
                posn_identifiers = _prune_identifiers(posn_identifiers)
                # add identifiers field
                posn_dict['identifiers'] = posn_identifiers
                # check poissongroup key already exists, if not create one
                if 'poissongroup' not in self.network_dict.keys():
                    self.network_dict['poissongroup'] = []
                self.network_dict['poissongroup'].append(posn_dict)
            
            # check SpikeGeneratorGroup
            if isinstance(object, SpikeGeneratorGroup):
                # get dict and identifiers
                spkgn_dict = collect_SpikeGenerator(object)
                # check poissongroup key already exists, if not create one
                if 'spikegeneratorgroup' not in self.network_dict.keys():
                    self.network_dict['spikegeneratorgroup'] = []
                self.network_dict['spikegeneratorgroup'].append(posn_dict)
                self.network_dict['spikegeneratorgroup'].append(spkgn_dict)
            
            if not isinstance(object, self.available_objs):
                if isinstance(object, CodeRunner) and not isinstance(object.group, self.available_objs):
                    raise NotImplementedError("Object {} is not implemented for standard format export".format(str(type(object))))
            
    def variableview_set_with_expression_conditional(self, variableview, cond, code,
                                                     run_namespace, check_units=True):
        if variableview.group.name not in self.initializers.keys():
            self.initializers[variableview.group.name] = []
        self.initializers[variableview.group.name].append({variableview.name: code})

    def variableview_set_with_expression(self, variableview, item, code, run_namespace, check_units=True):
        if variableview.group.name not in self.initializers.keys():
            self.initializers[variableview.group.name] = []
        self.initializers[variableview.group.name].append({variableview.name: (item, code)})

# instantiate StdDevice object and add to all_devices        
std_device = BaseExporter()
all_devices['ExportDevice'] = std_device

