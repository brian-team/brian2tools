from brian2 import Equations
from brian2.equations.equations import PARAMETER
from brian2.monitors.statemonitor import StateMonitor
from brian2.monitors.spikemonitor import SpikeMonitor
from brian2.groups.neurongroup import NeuronGroup
from brian2.core.namespace import get_local_namespace, DEFAULT_UNITS
from brian2.devices.device import RuntimeDevice, all_devices
from brian2.units.fundamentalunits import Quantity
from brian2.core.variables import Constant
from brian2.utils.stringtools import get_identifiers


def get_namespace_dict(identifiers, group, run_namespace):
    variables = group.resolve_all(identifiers, run_namespace)
    namespace = {key: Quantity(value.get_value(),
                               dim=value.unit.dimensions)
                 for key, value in variables.items()
                 if (isinstance(value, Constant) and
                     not key in DEFAULT_UNITS)}
    return namespace


def neurongroup_description(neurongroup, run_namespace):
    description = {}
    identifiers = neurongroup.user_equations.identifiers
    # TODO: Only convert the expression (not the units)
    equations = []
    parameters = []
    for eq in neurongroup.user_equations.values():
        if eq.type == PARAMETER:
            parameters.append(eq)
        else:
            equations.append(eq)
    description['equations'] = str(Equations(equations))
    description['parameters'] = {p.varname: {'unit': str(p.unit)} for p in parameters}
    if 'spike' in neurongroup.events:
        threshold = neurongroup.events['spike']
        identifiers |= get_identifiers(threshold)
        # TODO: Convert to LaTeX
        description['threshold'] = threshold
    if 'spike' in neurongroup.event_codes:
        reset = neurongroup.event_codes['spike']
        identifiers |= get_identifiers(reset)
        # TODO: Convert to LaTeX?
        description['reset'] = reset
    if neurongroup._refractory is not None:
        refractory = neurongroup._refractory
        if isinstance(refractory, basestring):
            identifiers |= get_identifiers(refractory)
        description['refractory period'] = refractory
    namespace = get_namespace_dict(identifiers, neurongroup,
                                   run_namespace)
    return description, namespace
    # TODO: Custom events


def description(brian_obj, run_namespace):
    if isinstance(brian_obj, NeuronGroup):
        return neurongroup_description(brian_obj, run_namespace)
    return '<Description for %s>' % brian_obj.name, {}


class DummyCodeObject(object):
    def __init__(self, *args, **kwds):
        pass

    def __call__(self, **kwds):
        pass


class JSONDevice(RuntimeDevice):
    '''
    The `Device` used for LEMS/NeuroML2 code generation.

    Use ``set_device('neuroml2', filename='myfilename.xml')`` to transform a
    Brian 2 script into a NeuroML2/LEMS description of the model.
    '''
    def __init__(self):
        super(JSONDevice, self).__init__()
        self.runs = []
        self.assignments = []
        self.build_on_run = True
        self.build_options = None
        self.has_been_run = False

    def reinit(self):
        build_on_run = self.build_on_run
        build_options = self.build_options
        self.__init__()
        super(JSONDevice, self).reinit()
        self.build_on_run = build_on_run
        self.build_options = build_options

    # This device does not actually calculate/store any data, so the following
    # are just dummy implementations

    def synaptic_pathway_before_run(self, pathway, run_namespace):
        pass  # No spike queue initialization necessary

    def network_run(self, network, duration, namespace=None, level=0, **kwds):
        network._clocks = {obj.clock for obj in network.objects}
        # Get the local namespace
        if namespace is None:
            namespace = get_local_namespace(level=level+2)
        network.before_run(namespace)

        # Extract all the objects present in the network
        descriptions = []
        merged_namespace = {}
        monitors = []
        for obj in network.objects:
            one_description, one_namespace = description(obj, namespace)
            descriptions.append((obj.name, one_description))
            if type(obj) in [StateMonitor, SpikeMonitor]:
                monitors.append(obj)
            for key, value in one_namespace.items():
                if key in merged_namespace and value != merged_namespace[key]:
                    raise ValueError('name "%s" is used inconsistently')
                merged_namespace[key] = value

        self.network = network
        assignments = list(self.assignments)
        self.assignments[:] = []
        self.runs.append((descriptions, duration, merged_namespace, assignments))
        if self.build_on_run:
            if self.has_been_run:
                raise RuntimeError('The network has already been built and run '
                                   'before. Use set_device with '
                                   'build_on_run=False and an explicit '
                                   'device.build call to use multiple run '
                                   'statements with this device.')
            self.build(direct_call=False, **self.build_options)
        self.has_been_run = True

    def variableview_set_with_expression_conditional(self, variableview, cond, code,
                                                     run_namespace, check_units=True):
        self.assignments.append(('conditional', variableview.group.name, variableview.name, cond, code))

    def variableview_set_with_expression(self, variableview, item, code, run_namespace, check_units=True):
        self.assignments.append(('item', variableview.group.name, variableview.name, item, code))

    def variableview_set_with_index_array(self, variableview, item, value, check_units):
        self.assignments.append(('item', variableview.group.name, variableview.name, item, value))

    def build(self, filename=None, direct_call=True, lems_const_save=True):
        """
        Collecting initializers and namespace from self.runs and passing
        it to the exporter.

        Parameters
        ----------
        filename : str, optional
            filename of exported xml model and recordings
        direct_call : bool, optional
            if call of the method was direct or not, default True
        lems_const_save : bool, optional
            whether to save or not LEMSUnitsConstants.xml alongside with
            output model file, default True
        """
        if self.build_on_run and direct_call:
            raise RuntimeError('You used set_device with build_on_run=True '
                               '(the default option), which will automatically '
                               'build the simulation at the first encountered '
                               'run call - do not call device.build manually '
                               'in this case.')
        # TODO:
        # Constant values
        # NeuronGroup description
            # Number of neurons
            # Equations
            # Parameters
            # Threshold condition
            # Reset statement(s)
            # Refractoriness
            # Assignments
        # Synapses
            # Equations
            # Parameters
            # On-pre / on-post
            # Connections
            # delays
            # Assignments
        # Run
            # Runtime
        if len(self.runs) > 1:
            raise NotImplementedError('Only a single run is supported for now.')

        desc, duration, namespace, assignments = self.runs[0]
        print('Run for {}'.format(str(duration)))
        print('Constants:\n{}'.format(namespace))
        print('Description:\n{}'.format(desc))
        print('Assignments:\n{}'.format(assignments))


all_devices['jsonexport'] = JSONDevice()
