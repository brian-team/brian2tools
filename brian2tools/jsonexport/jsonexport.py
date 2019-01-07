import collections

from brian2 import Equations, Synapses
from brian2.equations.equations import PARAMETER, DIFFERENTIAL_EQUATION
from brian2.monitors.statemonitor import StateMonitor
from brian2.monitors.spikemonitor import SpikeMonitor
from brian2.groups.neurongroup import NeuronGroup, Thresholder, Resetter, \
    StateUpdater
from brian2.core.namespace import get_local_namespace, DEFAULT_UNITS
from brian2.devices.device import RuntimeDevice, all_devices
from brian2.synapses.synapses import SynapticPathway
from brian2.units.fundamentalunits import Quantity, DIMENSIONLESS
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


def equation_description(eq):
    if eq.type == DIFFERENTIAL_EQUATION:
        return 'd{}/dt = {}'.format(eq.varname, eq.expr)
    else:
        return '{} = {}'.format(eq.varname, eq.expr)


def group_description(group):
    # Use an indexed form for subgroups
    if hasattr(group, 'source') and hasattr(group, 'start') and hasattr(group, 'stop'):
        return '{}[{}:{}]'.format(group.source.name, group.start, group.stop)
    else:
        return group.name


def neurongroup_description(neurongroup, run_namespace):
    description = collections.OrderedDict()
    identifiers = neurongroup.user_equations.identifiers
    equations = []
    parameters = []
    for eq in neurongroup.user_equations.values():
        if eq.type == PARAMETER:
            parameters.append(eq)
        else:
            equations.append(eq)
    description['number of neurons'] = neurongroup.N
    description['equations'] = {e.varname: {'equation': equation_description(e),
                                            'unit': '1' if e.unit.dim is DIMENSIONLESS else str(e.unit)}
                                for e in equations}
    description['parameters'] = {p.varname: {'unit': str(p.unit)} for p in parameters}
    if 'spike' in neurongroup.events:
        threshold = neurongroup.events['spike']
        identifiers |= get_identifiers(threshold)
        description['threshold'] = threshold
    if 'spike' in neurongroup.event_codes:
        reset = neurongroup.event_codes['spike']
        identifiers |= get_identifiers(reset)
        description['reset'] = reset
    if neurongroup._refractory is not None:
        refractory = neurongroup._refractory
        if isinstance(refractory, basestring):
            identifiers |= get_identifiers(refractory)
        description['refractory period'] = str(refractory)
    namespace = get_namespace_dict(identifiers, neurongroup,
                                   run_namespace)
    return description, namespace
    # TODO: Custom events


def synapses_description(synapses, run_namespace):
    description = collections.OrderedDict()
    identifiers = synapses.equations.identifiers
    equations = []
    parameters = []
    for eq in synapses.equations.values():
        if eq.type == PARAMETER:
            parameters.append(eq)
        else:
            equations.append(eq)
    description['presynaptic group'] = group_description(synapses.source)
    description['postsynaptic group'] = group_description(synapses.target)
    if len(equations):
        description['equations'] = {e.varname: {'equation': equation_description(e),
                                                'unit': '1' if e.unit.dim is DIMENSIONLESS else str(e.unit)}
                                    for e in equations}
    if len(parameters):
        description['parameters'] = {p.varname: {'unit': str(p.unit)} for p in parameters}
    for pathway in synapses._pathways:
        description['on {}synaptic spike'.format(pathway.prepost)] = pathway.code

    # TODO: Document delay if != 0
    namespace = get_namespace_dict(identifiers, synapses,
                                   run_namespace)
    return description, namespace


def description(brian_obj, run_namespace):
    if isinstance(brian_obj, NeuronGroup):
        return neurongroup_description(brian_obj, run_namespace)
    elif isinstance(brian_obj, Synapses):
        return synapses_description(brian_obj, run_namespace)
    elif isinstance(brian_obj, (Thresholder, Resetter, StateUpdater, SynapticPathway)):
        return None, {}
    else:
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
        self.connects = []
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
        descriptions = {}
        merged_namespace = {}
        monitors = []
        for obj in network.objects:
            one_description, one_namespace = description(obj, namespace)
            if one_description is not None:
                descriptions[obj.name] = one_description
            if type(obj) in [StateMonitor, SpikeMonitor]:
                monitors.append(obj)
            for key, value in one_namespace.items():
                if key in merged_namespace and value != merged_namespace[key]:
                    raise ValueError('name "%s" is used inconsistently')
                merged_namespace[key] = value

        for assignment_type, group_name, var_name, index, value in self.assignments:
            if 'initial values' not in descriptions[group_name]:
                descriptions[group_name]['initial values'] = []
            if isinstance(value, basestring):
                value = repr(value)  # include quotation marks
            else:
                value = str(value)
            if index == slice(None) or index is True or index == 'True':
                index = ''
            else:
                index = '[{}]'.format(index)
            descriptions[group_name]['initial values'].append('{}{} = {}'.format(var_name, index, value))

        for synapses, condition, i, j, p, n, skip_if_invalid in self.connects:
            if condition is None and i is None and j is None:
                condition = True
            if 'connections' not in descriptions[synapses]:
                descriptions[synapses]['connections'] = []
            connection = collections.OrderedDict()
            if condition is None:
                if p < 1.0:
                    connection['type'] = 'probabilistic'
                    connection['p'] = p
                else:
                    connection['type'] = 'explicit'
                connection['presynaptic indices'] = list(i)
                connection['postsynaptic indices'] = list(j)
            elif condition is True or condition == 'True':
                if p < 1.0:
                    connection['type'] = 'probabilistic'
                    connection['p'] = p
                else:
                    connection['type'] = 'all-to-all'
            else:
                if p < 1.0:
                    connection['type'] = 'probabilistic'
                    connection['p'] = p
                else:
                    connection['type'] = 'conditional'
                connection['condition'] = condition
            #TODO: Generator expressions
            if n != 1:
                connection['number of synapses per connection'] = n
            descriptions[synapses]['connections'].append(connection)

        self.network = network
        self.assignments[:] = []
        self.connects[:] = []
        self.runs.append((descriptions, duration, merged_namespace))
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

    def synapses_connect(self, synapses, condition=None, i=None, j=None, p=1., n=1,
                    skip_if_invalid=False, namespace=None, level=0):
        self.connects.append((synapses.name, condition, i, j, p, n, skip_if_invalid))

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

        # TODO: Merge constants into object description that uses them

        if len(self.runs) > 1:
            raise NotImplementedError('Only a single run is supported for now.')

        desc, duration, namespace = self.runs[0]
        # print('Run for {}'.format(str(duration)))
        # print('Constants:\n{}'.format(namespace))
        import json
        print(json.dumps(desc))


all_devices['jsonexport'] = JSONDevice()
