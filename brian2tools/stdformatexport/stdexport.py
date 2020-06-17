from brian2.devices.device import RuntimeDevice
from brian2.devices.device import Device, all_devices
from brian2.core.namespace import get_local_namespace
from brian2.groups import NeuronGroup
from brian2.input import PoissonGroup, SpikeGeneratorGroup

from .simple_collectors import *

class StdDevice(RuntimeDevice):
    """
    Class defining `stdformat` device mode to generate standard dictioanry 
    representation of the defined model. The `StdDevice` class is derived 
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

        super(StdDevice, self).__init__()

        self.build_on_run = True
        self.has_been_run = False
    
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

        #`_clocks` is required to run `Network.before_run(namespace)`
        network._clocks = {object.clock for object in network.objects}

        #if namespace not defined
        if namespace is None:
            namespace = get_local_namespace(level + 2)
        #prepare objects using `before_run()`
        network.before_run(namespace)

        
        self.network_dict = {}  #dictionary with Network components

        #list of neurons defined
        self.network_dict['neurongroup'] = []
        #list of Poissongroup defined
        self.network_dict['poissongroup'] = []
        #list of SpikeGeneratorGroup defined
        self.network_dict['spikegeneratorgroup'] = []

        #loop through all the objects of network and collect object 
        #specific identifiers
        for object in network.objects:
            #check NeuronGroup
            if isinstance(object, NeuronGroup):
                neuron_dict = collect_NeuronGroup(object)
                self.network_dict['neurongroup'].append(neuron_dict)

            #check PoissonGroup
            if isinstance(object, PoissonGroup):
                poisson_dict = collect_PoissonGroup(object)
                self.network_dict['poissongroup'].append(poisson_dict)
            
            #check SpikeGeneratorGroup
            if isinstance(object, SpikeGeneratorGroup):
                spikegen_dict = collect_SpikeGenerator(object)
                self.network_dict['spikegeneratorgroup'].append(spikegen_dict)

# instantiate StdDevice object and add to all_devices        
std_device = StdDevice()
all_devices['stdformat'] = std_device

