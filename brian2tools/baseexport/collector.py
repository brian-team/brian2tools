"""
The file contains simple functions to collect information
from BrianObjects and represent them in a standard
dictionary format. The parts of the file shall be reused
with standard format exporter.
"""
from brian2.codegen.translation import analyse_identifiers
from brian2.equations.equations import PARAMETER
from brian2.utils.stringtools import get_identifiers
from brian2.groups.neurongroup import StateUpdater
from brian2.groups.group import CodeRunner
from brian2.synapses.synapses import SummedVariableUpdater, SynapticPathway
from brian2.synapses.synapses import StateUpdater as synapse_stateupdater
from brian2.units.fundamentalunits import Quantity
from brian2 import second, Subgroup
import numpy as np
from .helper import _prepare_identifiers


def collect_NeuronGroup(group, run_namespace):
    """
    Collect information from `brian2.groups.neurongroup.NeuronGroup`
    and return them in a dictionary format

    Parameters
    ----------
    group : brian2.groups.neurongroup.NeuronGroup
        NeuronGroup object

    run_namespace : dict
        Namespace dictionary

    Returns
    -------
    neuron_dict : dict
        Dictionary with extracted information
    """
    neuron_dict = {}

    # identifiers belonging to the NeuronGroup
    identifiers = set()

    # get name
    neuron_dict['name'] = group.name

    # get size
    neuron_dict['N'] = group._N

    # get user defined stateupdation method
    if isinstance(group.method_choice, str):
        neuron_dict['user_method'] = group.method_choice
    # if not specified by user
    # TODO collect from run time
    else:
        neuron_dict['user_method'] = None

    # get equations
    neuron_dict['equations'] = collect_Equations(group.user_equations)
    identifiers = identifiers | group.user_equations.identifiers

    # check spike event is defined
    if group.events:
        neuron_dict['events'], event_identifiers = collect_Events(group)
        identifiers = identifiers | event_identifiers

    # check any `run_regularly` / CodeRunner objects associated
    for obj in group.contained_objects:
        # Note: Thresholder, StateUpdater, Resetter are all derived from
        # CodeRunner, so to identify `run_regularly` object we use type()
        if type(obj) == CodeRunner:
            if 'run_regularly' not in neuron_dict:
                neuron_dict['run_regularly'] = []
            neuron_dict['run_regularly'].append({
                                            'name': obj.name,
                                            'code': obj.abstract_code,
                                            'dt': obj.clock.dt,
                                            'when': obj.when,
                                            'order': obj.order
                                            })
            identifiers = identifiers | get_identifiers(obj.abstract_code)

        # check StateUpdater when/order and assign to group level
        if isinstance(obj, StateUpdater):
            neuron_dict['when'] = obj.when
            neuron_dict['order'] = obj.order
    
    # resolve group-specific identifiers
    identifiers = group.resolve_all(identifiers, run_namespace)
    # with the identifiers connected to group, prune away unwanted
    identifiers = _prepare_identifiers(identifiers)
    # check the dictionary is not empty
    if identifiers:
        neuron_dict['identifiers'] = identifiers

    return neuron_dict


def collect_Equations(equations):
    """
    Collect model equations of the NeuronGroup

    Parameters
    ----------
    equations : brian2.equations.equations.Equations
        model equations object

    Returns
    -------
    eqn_dict : dict
        Dictionary with extracted information
    """

    eqn_dict = {}

    # Using the keys of the _equations dictionary makes sure
    # that we go through the equations in the same order
    # in which they were defined
    for name in equations._equations:

        eqs = equations[name]

        eqn_dict[name] = {'unit': eqs.unit,
                          'type': eqs.type,
                          'var_type': eqs.var_type}

        if eqs.type != PARAMETER:
            eqn_dict[name]['expr'] = eqs.expr.code

        if eqs.flags:
            eqn_dict[name]['flags'] = eqs.flags

    return eqn_dict


def collect_Events(group):

    """
    Collect Events (spiking) of the NeuronGroup

    Parameters
    ----------
    group : brian2.groups.neurongroup.NeuronGroup
        NeuronGroup object

    Returns
    -------
    event_dict : dict
        Dictionary with extracted information

    event_identifiers : set
        Set of identifiers related to events
    """

    event_dict = {}
    event_identifiers = set()

    # loop over the thresholder to check `spike` or custom event
    for event in group.thresholder:
        # for simplicity create subdict variable for particular event
        event_dict[event] = {}
        event_subdict = event_dict[event]
        # add threshold
        event_subdict['threshold'] = {'code': group.events[event],
                                      'when': group.thresholder[event].when,
                                      'order': group.thresholder[event].order,
                                      'dt': group.thresholder[event].clock.dt}
        event_identifiers |= get_identifiers(group.events[event])

        # check reset is defined
        if event in group.event_codes:
            event_subdict['reset'] = {'code': group.event_codes[event],
                                      'when': group.resetter[event].when,
                                      'order': group.resetter[event].order,
                                      'dt': group.resetter[event].clock.dt}
            event_identifiers |= get_identifiers(group.event_codes[event])

    # check refractory is defined (only for spike event)
    if event == 'spike' and group._refractory:
        event_subdict['refractory'] = group._refractory

    return event_dict, event_identifiers


def collect_SpikeGenerator(spike_gen, run_namespace):
    """
    Extract information from
    'brian2.input.spikegeneratorgroup.SpikeGeneratorGroup'and
    represent them in a dictionary format

    Parameters
    ----------
    spike_gen : brian2.input.spikegeneratorgroup.SpikeGeneratorGroup
            SpikeGenerator object

    run_namespace : dict
            Namespace dictionary

    Returns
    -------
    spikegen_dict : dict
                Dictionary with extracted information
    """

    spikegen_dict = {}
    identifiers = set()
    # get name
    spikegen_dict['name'] = spike_gen.name

    # get size
    spikegen_dict['N'] = spike_gen.N

    # get indices of spiking neurons
    spikegen_dict['indices'] = spike_gen._neuron_index[:]

    # get spike times for defined neurons
    spikegen_dict['times'] = Quantity(spike_gen._spike_time[:], second)

    # get spike period (default period is 0*second will be stored if not
    # mentioned by the user)
    spikegen_dict['period'] = spike_gen.period[:]

    # `run_regularly` / CodeRunner objects of spike_gen
    # although not a very popular option
    for obj in spike_gen.contained_objects:
        if type(obj) == CodeRunner:
            if 'run_regularly' not in spikegen_dict:
                spikegen_dict['run_regularly'] = []
            spikegen_dict['run_regularly'].append({
                                            'name': obj.name,
                                            'code': obj.abstract_code,
                                            'dt': obj.clock.dt,
                                            'when': obj.when,
                                            'order': obj.order
                                            })
            identifiers = identifiers | get_identifiers(obj.abstract_code)
    # resolve group-specific identifiers
    identifiers = spike_gen.resolve_all(identifiers, run_namespace)
    # with the identifiers connected to group, prune away unwanted
    identifiers = _prepare_identifiers(identifiers)
    # check the dictionary is not empty
    if identifiers:
        spikegen_dict['identifiers'] = identifiers

    return spikegen_dict


def collect_PoissonGroup(poisson_grp, run_namespace):
    """
    Extract information from 'brian2.input.poissongroup.PoissonGroup'
    and represent them in a dictionary format

    Parameters
    ----------
    poisson_grp : brian2.input.poissongroup.PoissonGroup
            PoissonGroup object

    run_namespace : dict
            Namespace dictionary

    Returns
    -------
    poisson_grp_dict : dict
                Dictionary with extracted information
    """

    poisson_grp_dict = {}
    poisson_identifiers = set()

    # get name
    poisson_grp_dict['name'] = poisson_grp._name

    # get size
    poisson_grp_dict['N'] = poisson_grp._N

    # get rates (can be Quantity or str)
    poisson_grp_dict['rates'] = poisson_grp._rates
    if isinstance(poisson_grp._rates, str):
        poisson_identifiers |= (get_identifiers(poisson_grp._rates))

    # `run_regularly` / CodeRunner objects of poisson_grp
    for obj in poisson_grp.contained_objects:
        if type(obj) == CodeRunner:
            if 'run_regularly' not in poisson_grp_dict:
                poisson_grp_dict['run_regularly'] = []
            poisson_grp_dict['run_regularly'].append({
                                            'name': obj.name,
                                            'code': obj.abstract_code,
                                            'dt': obj.clock.dt,
                                            'when': obj.when,
                                            'order': obj.order
                                            })
            poisson_identifiers = (poisson_identifiers |
                                   get_identifiers(obj.abstract_code))
    # resolve group-specific identifiers
    poisson_identifiers = poisson_grp.resolve_all(poisson_identifiers,
                                                  run_namespace)
    # with the identifiers connected to group, prune away unwanted
    poisson_identifiers = _prepare_identifiers(poisson_identifiers)
    # check the dictionary is not empty
    if poisson_identifiers:
        poisson_grp_dict['identifiers'] = poisson_identifiers

    return poisson_grp_dict


def collect_SpikeSource(source):
    """
    Check SpikeSource and collect details

    Parameters
    ----------
    source : `brian2.core.spikesource.SpikeSource`
        SpikeSource object
    """
    if isinstance(source, Subgroup):
        return {'start': source.start, 'stop': source.stop - 1,
                'group': source.source.name}
    return source.name


def collect_StateMonitor(state_mon):
    """
    Collect details of `brian2.monitors.statemonitor.StateMonitor`
    and return them in dictionary format

    Parameters
    ----------
    state_mon : brian2.monitors.statemonitor.StateMonitor
            StateMonitor object

    Returns
    -------
    state_mon_dict : dict
            Dictionary representation of the collected details
    """

    state_mon_dict = {}

    # get name
    state_mon_dict['name'] = state_mon.name

    # if subgroup extend it
    state_mon_dict['source'] = collect_SpikeSource(state_mon.source)

    # get recorded variables
    state_mon_dict['variables'] = state_mon.record_variables

    # get record indices
    # if all members of the source object are being recorded
    # set 'record_indices' = True, else save indices
    if state_mon.record_all:
        state_mon_dict['record'] = state_mon.record_all
    else:
        state_mon_dict['record'] = state_mon.record

    # get no. of record indices
    state_mon_dict['n_indices'] = state_mon.n_indices

    # get clock dt of the StateMonitor
    state_mon_dict['dt'] = state_mon.clock.dt

    # get when and order of the StateMonitor
    state_mon_dict['when'] = state_mon.when
    state_mon_dict['order'] = state_mon.order

    return state_mon_dict


def collect_SpikeMonitor(spike_mon):
    """
    Collect details of `brian2.monitors.spikemonitor.SpikeMonitor`
    and return them in dictionary format

    Parameters
    ----------
    spike_mon : brian2.monitors.spikemonitor.SpikeMonitor
            SpikeMonitor object

    Returns
    -------
    spike_mon_dict : dict
            Dictionary representation of the collected details
    """
    # pass to EventMonitor as they both are identical
    spike_mon_dict = collect_EventMonitor(spike_mon)
    return spike_mon_dict


def collect_EventMonitor(event_mon):
    """
    Collect details of `EventMonitor` class
    and return them in dictionary format

    Parameters
    ----------
    event_mon : brian2.EventMonitor
            EventMonitor object

    Returns
    -------
    event_mon_dict : dict
            Dictionary representation of the collected details
    """

    event_mon_dict = {}

    # collect name
    event_mon_dict['name'] = event_mon.name

    # collect event name
    event_mon_dict['event'] = event_mon.event

    # get source object name
    event_mon_dict['source'] = collect_SpikeSource(event_mon.source)

    # collect source object size (shall be used for nmlexport)
    event_mon_dict['source_size'] = event_mon.source.N

    # collect record variables, (done same as for SpikeMonitor)
    event_mon_dict['variables'] = list(event_mon.record_variables)

    # collect record indices and time
    # change to list if one member to monitor, to have uniformity as
    # for statemonitor
    if (hasattr(event_mon.record, '__iter__') or
        isinstance(event_mon.record, bool)):
        event_mon_dict['record'] = event_mon.record
    else:
        event_mon_dict['record'] = np.array([event_mon.record])

    # collect time-step
    event_mon_dict['dt'] = event_mon.clock.dt

    # collect when and order
    event_mon_dict['when'] = event_mon.when
    event_mon_dict['order'] = event_mon.order

    return event_mon_dict


def collect_PopulationRateMonitor(poprate_mon):
    """
    Represent required details of PopulationRateMonitor
    in dictionary format

    Parameters
    ----------
    poprate_mon : brian2.monitors.ratemonitor.PopulationRateMonitor
            PopulationRateMonitor class object

    Returns
    -------
    poprate_mon_dict : dict
            Dictionary format of the details collected
    """

    poprate_mon_dict = {}

    # collect name
    poprate_mon_dict['name'] = poprate_mon.name

    # collect source object
    poprate_mon_dict['source'] = collect_SpikeSource(poprate_mon.source)

    # collect time-step
    poprate_mon_dict['dt'] = poprate_mon.clock.dt

    # collect when/order
    poprate_mon_dict['when'] = poprate_mon.when
    poprate_mon_dict['order'] = poprate_mon.order

    return poprate_mon_dict


def collect_Synapses(synapses, run_namespace):
    """
    Collect information from `brian2.synapses.synapses.Synapses`
    and represent them in dictionary format

    Parameters
    ----------
    synapses : brian2.synapses.synapses.Synapses
        Synapses object

    run_namespace : dict
        Namespace dictionary

    Returns
    -------
    synapse_dict : dict
        Standard dictionary format with collected information
    """
    identifiers = set()
    synapse_dict = {}
    # get synapses object name
    synapse_dict['name'] = synapses.name

    # get source and target groups
    synapse_dict['source'] = collect_SpikeSource(synapses.source)
    synapse_dict['target'] = collect_SpikeSource(synapses.target)

    # get governing equations
    synapse_equations = collect_Equations(synapses.equations)
    # get identifiers from equations
    identifiers = identifiers | synapses.equations.identifiers
    if synapses.event_driven:
        synapse_equations.update(collect_Equations(synapses.event_driven))
        identifiers = identifiers | synapses.event_driven.identifiers
    # check equations is not empty
    if synapse_equations:
        synapse_dict['equations'] = synapse_equations
    # check state updaters
    if (synapses.state_updater and
        isinstance(synapses.state_updater.method_choice, str)):
        synapse_dict['user_method'] = synapses.state_updater.method_choice
    # loop over the contained objects
    summed_variables = []
    pathways = []
    for obj in synapses.contained_objects:
        # check summed variables
        if isinstance(obj, SummedVariableUpdater):
            summed_var = {'code': obj.expression,
                          'target': collect_SpikeSource(obj.target),
                          'name': obj.name, 'dt': obj.clock.dt,
                          'when': obj.when, 'order': obj.order
                         }
            summed_variables.append(summed_var)
        # check synapse pathways
        if isinstance(obj, SynapticPathway):
            path = {'prepost': obj.prepost, 'event': obj.event,
                    'code': obj.code,
                    'source': collect_SpikeSource(obj.source),
                    'target': collect_SpikeSource(obj.target),
                    'name': obj.name,
                    'dt': obj.clock.dt, 'order': obj.order,
                    'when': obj.when
                   }
            # check delay is defined
            if obj.variables['delay'].scalar:
               path.update({'delay': obj.delay[:]})
            pathways.append(path)
            # check any identifiers specific to pathway expression
            _, _, unknown = analyse_identifiers(obj.code, obj.variables)
            identifiers = identifiers | unknown

    # check any summed variables are used
    if summed_variables:
        synapse_dict['summed_variables'] = summed_variables
    # check any pathways are defined
    if pathways:
        synapse_dict['pathways'] = pathways
    # resolve identifiers and add to dict
    identifiers = synapses.resolve_all(identifiers, run_namespace)
    identifiers = _prepare_identifiers(identifiers)
    if identifiers:
        synapse_dict['identifiers'] = identifiers

    return synapse_dict


def collect_PoissonInput(poinp, run_namespace):
    """
    Collect details of `PoissonInput` and represent them in dictionary

    Parameters
    ----------
    poinp : brian2.input.poissoninput.PoissonInput
            PoissonInput object

    run_namespace : dict
            Namespace dictionary

    Returns
    -------
    poinp_dict : dict
            Dictionary representation of the collected details
    """
    poinp_dict = {}
    poinp_dict['target'] = poinp._group.name
    poinp_dict['rate'] = poinp.rate
    poinp_dict['N'] = poinp.N
    poinp_dict['when'] = poinp.when
    poinp_dict['order'] = poinp.order
    poinp_dict['dt'] = poinp.clock.dt
    poinp_dict['weight'] = poinp._weight
    poinp_dict['target_var'] = poinp._target_var
    # collect identifiers, resolve and prune
    if isinstance(poinp_dict['weight'], str):
        identifiers = get_identifiers(poinp_dict['weight'])
        identifiers = poinp._group.resolve_all(identifiers, run_namespace)
        identifiers = _prepare_identifiers(identifiers)
        if identifiers:
            poinp_dict['identifiers'] = identifiers

    return poinp_dict
