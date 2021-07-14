from brian2.core.variables import DynamicArrayVariable
from brian2.devices.device import RuntimeDevice, Device, all_devices
from brian2.groups import NeuronGroup
from brian2.input import PoissonGroup, SpikeGeneratorGroup
from brian2 import (get_local_namespace, StateMonitor, SpikeMonitor,
                    EventMonitor, PopulationRateMonitor, Synapses,
                    Quantity, PoissonInput)
from brian2.utils.logger import get_logger
from brian2.utils.stringtools import get_identifiers
from .helper import _prepare_identifiers
import numpy as np
from .collector import *
try:
    import pprint
    pprint_available = True
except ImportError:
    pprint_available = False

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
                               PoissonGroup, StateMonitor, SpikeMonitor,
                               EventMonitor, PopulationRateMonitor, Synapses,
                               PoissonInput)
        self.runs = []
        self.initializers_connectors = []
        self.array_cache = {}

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

    def init_with_zeros(self, var, dtype):
        self.array_cache[var] = np.zeros(var.size, dtype=dtype)

    def init_with_arange(self, var, start, dtype):
        self.array_cache[var] = np.arange(0, var.size, dtype=dtype) + start

    def fill_with_array(self, var, arr):
        arr = np.asarray(arr)
        if arr.size == 0:
            return  # nothing to do
        if isinstance(var, DynamicArrayVariable) and not var.scalar:
            # We can never be sure about the size of a dynamic array, so
            # we can't do correct broadcasting. Therefore, we do not cache
            # them at all for now.
            self.array_cache[var] = None
        else:
            new_arr = np.empty(var.size, dtype=var.dtype)
            new_arr[:] = arr
            self.array_cache[var] = new_arr

    def code_object(self, owner, name, abstract_code, variables, template_name,
                    variable_indices, codeobj_class=None,
                    template_kwds=None, override_conditional_write=None,
                    compiler_kwds=None):
        pass  # Do nothing

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

        # dictionary to store objects and its collector functions
        collector_map={'neurongroup': {'f': collect_NeuronGroup, 'n': True},
                       'poissongroup': {'f': collect_PoissonGroup, 'n': True},
                       'spikegeneratorgroup': {'f': collect_SpikeGenerator,
                                               'n': True},
                       'statemonitor': {'f': collect_StateMonitor,
                                        'n': False},
                       'spikemonitor': {'f': collect_SpikeMonitor,
                                        'n': False},
                       'eventmonitor': {'f': collect_EventMonitor,
                                        'n': False},
                       'populationratemonitor':
                                       {'f': collect_PopulationRateMonitor,
                                        'n': False},
                        'synapses': {'f': collect_Synapses, 'n': True},
                        'poissoninput': {'f': collect_PoissonInput, 'n': True}
                      }

        # loop through all the objects of network
        for object in network.objects:

            # check the object is supported currently
            if not isinstance(object, self.supported_objs):
                unsupported = True
                if hasattr(object, 'group') and isinstance(
                                                        object.group,
                                                        self.supported_objs):
                    unsupported = False
                if unsupported:
                    raise NotImplementedError("Object {} is not implemented \
                                               for standard format export".
                                               format(str(type(object))))

            # get the object type in string with lower case
            object_instance = type(object).__name__.lower()
            # call collectors for valid objects or just pass
            if object_instance in collector_map:
                # map with approporiate collector function
                if collector_map[object_instance]['n']:
                    obj_dict = collector_map[object_instance]['f'](object,
                                                                   namespace)
                else:
                    obj_dict = collector_map[object_instance]['f'](object)
                # if key not exists in run_components, create one
                if object_instance not in run_components:
                    run_components[object_instance] = []
                run_components[object_instance].append(obj_dict)

            # check any inactive objects present in the run
            if not object.active:
                run_inactive.append(object.name)

        # copy fields to run_dict
        run_dict = {'components': run_components,
                    'duration': duration}
        # check any initializers and connectors defined in the run scope
        if self.initializers_connectors:
            run_dict['initializers_connectors'] = self.initializers_connectors
        # check any inactive objects present for this run
        if run_inactive:
            run_dict['inactive'] = run_inactive
        # append the run_dict that contains all information about the
        # Brian objects defined in the scope of run()
        self.runs.append(run_dict)
        # reset the dict, lists at run_level,
        # so it won't be repeated for other runs
        # TODO: but it doesn't make any diff, should compare and remove
        self.initializers_connectors = []
        run_dict = {}
        run_components = {}
        run_inactive = []
        # check to call build()
        if self.build_on_run:
            # if alread called build() raise error
            if self.has_been_run:
                raise RuntimeError('The network has already been built '
                                   'and run before. Use set_device with '
                                   'build_on_run=False and an explicit '
                                   'device.build call to use multiple run '
                                   'statements with this device.')
            # call build
            self.build(direct_call=False, **self.build_options)

    def get_value(self, var, access_data=True):
        if self.array_cache.get(var, None) is not None:
            return self.array_cache[var]
        else:
            raise NotImplementedError(('Cannot get variable "%s" this way in '
                                       'device mode.') % var.name)

    def variableview_set_with_expression_conditional(self, variableview,
                                                     cond, code,
                                                     run_namespace,
                                                     check_units=True):
        """
        Capture setters with conditioanl expressions,
        for eg. obj.var['i>5'] = 'rand() * -78 * mV'
        """
        # get resolved and clean identifiers
        ident_set = get_identifiers(code)
        ident_dict = variableview.group.resolve_all(ident_set, run_namespace)
        ident_dict = _prepare_identifiers(ident_dict)
        init_dict = {'source': collect_SpikeSource(variableview.group),
                     'variable': variableview.name,
                     'index': cond, 'value': code, 'type': 'initializer'}
        # if identifiers are defined, then add the field
        if ident_dict:
            init_dict.update({'identifiers': ident_dict})
        self.initializers_connectors.append(init_dict)

    def variableview_set_with_expression(self, variableview, item, code,
                                         run_namespace, check_units=True):
        """
        Capture setters with expressions,
        for eg. obj.var[0:2] = 'rand() * -78 * mV' or
        obj.var = 'rand() * -78 * mV'
        """
        # get resolved and clean identifiers
        ident_set = get_identifiers(code)
        ident_dict = variableview.group.resolve_all(ident_set, run_namespace)
        ident_dict = _prepare_identifiers(ident_dict)
        init_dict = {'source': collect_SpikeSource(variableview.group),
                     'variable': variableview.name,
                     'value': code, 'type': 'initializer'}
        if ident_dict:
            init_dict.update({'identifiers': ident_dict})
        # check type is slice and True
        if type(item) == slice and item.start is None and item.stop is None:
            init_dict['index'] = True
        elif ((isinstance(item, int) or (isinstance(item, np.ndarray) and
               item.shape == ()))):
            if self.array_cache.get(variableview.variable, None) is not None:
                self.array_cache[variableview.variable][item] = code
            init_dict['index'] = item
        else:
            # We have to calculate indices. This will not work for synaptic
            # variables
            try:
                init_dict['index'] = np.asarray(variableview.indexing(item,
                                            index_var=variableview.index_var))
            except NotImplementedError:
                raise NotImplementedError(('Cannot set variable "%s" this way'
                                           ' in device mode,try using string '
                                           'expressions') % variableview.name)
        self.initializers_connectors.append(init_dict)

    def variableview_set_with_index_array(self, variableview, item, value,
                                          check_units=True):
        """
        Capture setters with particular,
        for eg. obj.var[0:2] = -78 * mV
        """
        # happens when dimensionless is passed like int/float
        if not isinstance(value, Quantity):
            value = Quantity(value)
        init_dict = {'source': collect_SpikeSource(variableview.group),
                     'variable': variableview.name,
                     'value': value, 'type': 'initializer'}
        # check type is slice and True
        if type(item) == slice and item.start is None and item.stop is None:
            init_dict['index'] = True
        elif ((isinstance(item, int) or (isinstance(item, np.ndarray) and
              item.shape == ())) and value.size == 1):
            if self.array_cache.get(variableview.variable, None) is not None:
                self.array_cache[variableview.variable][item] = value
            init_dict['index'] = item
        else:
            # We have to calculate indices. This will not work for synaptic
            # variables
            try:
                init_dict['index'] = np.asarray(variableview.indexing(item,
                                            index_var=variableview.index_var))
            except NotImplementedError:
                raise NotImplementedError(('Cannot set variable "%s" this way'
                                           'in device mode, '
                                           'try using string '
                                           'expressions') % variableview.name)
        self.initializers_connectors.append(init_dict)

    def synaptic_pathway_before_run(self, pathway, run_namespace):
        """
        Get synaptic pathways and pass it to dictionary
        """
        # handled in the collect_synapses()
        pass

    def synapses_connect(self, synapses, condition=None, i=None,
                         j=None, p=1, n=1, skip_if_invalid=False,
                         namespace=None, level=0):
        """
        Override synapses_connect() to get details from Synapses.connect()
        """
        # if namespace not defined
        if namespace is None:
            namespace = get_local_namespace(level + 2)
        # prepare objects using `before_run()`
        synapses.before_run(namespace)
        if condition is not None:
            if i is not None or j is not None:
                raise ValueError("Cannot combine condition with i or j "
                                 "arguments")
        connect = {}
        # string statements that shall have identifers
        strings_with_identifers = []
        if condition and isinstance(condition, str):
            connect.update({'condition': condition})
            strings_with_identifers.append(condition)
        elif i is not None or j is not None:
            if i is not None:
                connect.update({'i': i})
            if j is not None:
                connect.update({'j': j})
        connect.update({'probability': p, 'n_connections': n,
                        'synapses': synapses.name,
                        'source': collect_SpikeSource(synapses.source),
                        'target': collect_SpikeSource(synapses.target),
                        'type': 'connect'
                        })
        # get resolved and clean identifiers
        strings_with_identifers.append(str(p))
        strings_with_identifers.append(str(n))
        identifers_set = set()
        for string_expr in strings_with_identifers:
            identifers_set = identifers_set | get_identifiers(string_expr)
        ident_dict = synapses.resolve_all(identifers_set, namespace)
        ident_dict = _prepare_identifiers(ident_dict)
        if ident_dict:
            connect.update({'identifiers': ident_dict})
        self.initializers_connectors.append(connect)
        # update `_connect_called` to allow initialization on
        # synaptic variables
        synapses._connect_called = True

    def build(self, direct_call=True, debug=False):
        """
        Collect all run information and export the standard
        dictionary format

        Parameters
        ----------
        direct_call: bool, optional
            To check the call to build() was made directly

        debug: bool, optional
            To build the device in debug mode, which prints out the dictionary
            information
        """
        # buil_on_run = True but called build() directly
        if self.build_on_run and direct_call:
            raise RuntimeError('You used set_device with build_on_run=True '
                               '(the default option), which will '
                               'automatically build the simulation at the '
                               'first encountered run call - do not call '
                               'device.build manually in this case. If you '
                               'want to call it manually, '
                               'e.g. because you have multiple run calls, use'
                               ' set_device with build_on_run=False.')
        # if already built
        if self.has_been_run:
            raise RuntimeError('The network has already been built and run '
                               'before. To build several simulations in '
                               'the same script, call "device.reinit()" '
                               'and "device.activate()". Note that you '
                               'will have to set build options (e.g. the '
                               'directory) and defaultclock.dt again.')
        # change the flag
        self.has_been_run = True
        # if to operate in debug mode
        if debug:
            logger.debug("Building ExportDevice in debug mode")
            # print dictionary format using pprint
            old_threshold = np.get_printoptions()['threshold']
            np.set_printoptions(threshold=10)
            if pprint_available:
                pprint.pprint(self.runs)
            # reset to avoid affecting overall remaining session
            np.set_printoptions(old_threshold)


# instantiate StdDevice object and add to all_devices
std_device = BaseExporter()
all_devices['exporter'] = std_device
