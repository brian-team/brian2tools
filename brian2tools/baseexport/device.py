from brian2.devices.device import RuntimeDevice
from brian2.devices.device import Device, all_devices
from brian2.core.namespace import get_local_namespace
from brian2.groups import NeuronGroup
from brian2.groups.group import CodeRunner
from brian2.utils.logger import get_logger
from brian2.input import PoissonGroup, SpikeGeneratorGroup

from .collector import *

logger = get_logger(__name__)


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
    2. brian2.devices.cppstandalone.device.CPPStandaloneDevice class
    3. brian2.devices.device.RuntimeDevice class
    4. brian2tools.nmlexport package
    """

    def __init__(self):
        """
        Constructor to define build and run options
        """

        super(BaseExporter, self).__init__()

        self.build_on_run = True
        self.has_been_run = False
        self.build_options = None
        self.supported_objs = (NeuronGroup, SpikeGeneratorGroup,
                               PoissonGroup)
        self.runs = []
        self.initializers = []
        self.run_identifiers = []

    def reinit(self):
        """
        Save the build_on_run and build_options and use
        them to reinit
        """
        # save the options
        prev_build_on_run = self.build_on_run
        prev_build_options = self.build_options
        # call constructor and super class reinit()
        self.__init__()
        super(BaseExporter, self).reinit()
        # set the saved options
        self.build_on_run = prev_build_on_run
        self.build_options = prev_build_options

    def network_run(self, network, duration, namespace=None, level=0, **kwds):
        """
        Method to be executed when `Network.run()` is called in
        `ExportDevice` device mode

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

        if kwds:
            logger.warn(('Unsupported keyword argument(s) provided for run: '
                         '%s') % ', '.join(kwds.keys()))

        # `_clocks` is required to run `Network.before_run(namespace)`
        network._clocks = {object.clock for object in network.objects}

        # if namespace not defined
        if namespace is None:
            namespace = get_local_namespace(level + 2)
        # prepare objects using `before_run()`
        network.before_run(namespace)

        run_dict = {}          # dictionary with components of particular run
        run_components = {}    # network components during the run
        run_inactive = []      # inactive objects for the run

        # loop through all the objects of network
        for object in network.objects:
            
            # check the object is inactive
            # check NeuronGroup
            if isinstance(object, NeuronGroup):
                # get dictionary containing all information about object
                neuron_dict = collect_NeuronGroup(object, namespace)
                # check neurongroup key already exists, if not create one
                if 'neurongroup' not in run_components:
                    run_components['neurongroup'] = []
                run_components['neurongroup'].append(neuron_dict)

            # check PoissonGroup
            if isinstance(object, PoissonGroup):
                # get dict of all information
                posn_dict = collect_PoissonGroup(object, namespace)
                # check poissongroup key already exists, if not create one
                if 'poissongroup' not in run_components:
                    run_components['poissongroup'] = []
                run_components['poissongroup'].append(posn_dict)

            # check SpikeGeneratorGroup
            if isinstance(object, SpikeGeneratorGroup):
                # get dict containing required information
                # no identifiers are connected with object so default to None
                spkgn_dict = collect_SpikeGenerator(object)
                # check poissongroup key already exists, if not create one
                if 'spikegeneratorgroup' not in run_components:
                    run_components['spikegeneratorgroup'] = []
                run_components['spikegeneratorgroup'].append(spkgn_dict)

            if (not isinstance(object, self.supported_objs) and
                not isinstance(object.group, self.supported_objs)):
                raise NotImplementedError(
                        "Object {} is not implemented for\
                         standard format export".format(str(type(object))))

            # check any inactive objects present in the run
            if not object.active:
                run_inactive.append(object.name)

        run_dict = {'components': run_components,
                    'duration': duration
                   }
        # check any initializers defined in the run scope
        if self.initializers:
            run_dict['initializers'] = self.initializers
        # check the identifiers present in run level (like from initializers
        # expressions)
        if self.run_identifiers:
            run_dict['run_identifiers'] = self.run_identifiers
        # check any inactive objects present for this run
        if run_inactive:
            run_dict['inactive'] = run_inactive
        # reset the initializers, so it won't be repeated for other runs
        self.initializers = []
        # append the run_dict that contains all information about the
        # Brian objects defined in the scope of run()
        self.runs.append(run_dict)

        print(self.runs)

    def variableview_set_with_expression_conditional(self, variableview, cond, 
                                                     code, run_namespace,
                                                     check_units=True):
        """
        Capture setters with conditioanl expressions, 
        for eg. obj.var['i>5'] = 'rand() * -78 * mV'
        """
        # Note: by default, when 
        init_dict = {'source': variableview.group.name,
                     'variable': variableview.name,
                     'index': cond, 'value': code}
        self.initializers.append(init_dict)    
        
    def variableview_set_with_expression(self, variableview, item, code,
                                         run_namespace, check_units=True):
        """
        Capture setters with expressions,
        for eg. obj.var[0:2] = 'rand() * -78 * mV' or
        obj.var = 'rand() * -78 * mV'
        """
        init_dict = {'source': variableview.group.name,
                     'variable': variableview.name,
                     'value': code}
        # check item is of slice type, if so pass to indices
        # else pass the boolean
        if type(item) == slice:
            init_dict['index'] = list(range(variableview.group.N))[item]
        else:
            init_dict['index'] = item
        self.initializers.append(init_dict)

    def variableview_set_with_index_array(self, variableview, item, value,
                                          check_units = True):
        """
        Capture setters with particular,
        for eg. obj.var[0:2] = 'rand() * -78 * mV' or
        obj.var = 'rand() * -78 * mV'
        """
        init_dict = {'source': variableview.group.name,
                     'variable': variableview.name,
                     'value': value}
        # check type is slice, if so pass to indices
        # else pass the boolean
        if type(item) == slice:
            init_dict['index'] = list(range(variableview.group.N))[item]
        else:
            init_dict['index'] = item
        self.initializers.append(init_dict)


# instantiate StdDevice object and add to all_devices
std_device = BaseExporter()
all_devices['ExportDevice'] = std_device
