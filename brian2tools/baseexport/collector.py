"""
The file contains simple functions to collect information
from BrianObjects and represent them in a standard
dictionary format. The parts of the file shall be reused
with standard format exporter.
"""
from brian2.equations.equations import PARAMETER
from brian2.groups.group import CodeRunner


def collect_NeuronGroup(group):
    """
    Collect information from `brian2.groups.neurongroup.NeuronGroup`
    and return them in a dictionary format

    Parameters
    ----------
    group : brian2.groups.neurongroup.NeuronGroup
        NeuronGroup object

    Returns
    -------
    neuron_dict : dict
        Dictionary with extracted information
    """
    neuron_dict = {}

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

    # check spike event is defined
    if group.events:
        neuron_dict['events'] = collect_Events(group)

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
                                                'dt': obj.clock.dt
                                                })
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

    for name in (equations.diff_eq_names | equations.subexpr_names |
                 equations.parameter_names):

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
    """

    event_dict = {}

    # add threshold
    event_dict['spike'] = {'threshold': group.events['spike']}

    # check reset is defined
    if group.event_codes:
        event_dict['spike'].update({'reset': group.event_codes['spike']})

    # check refractory is defined
    if group._refractory:
        event_dict['spike'].update({'refractory': group._refractory})

    return event_dict


def collect_SpikeGenerator(spike_gen):
    """
    Extract information from
    'brian2.input.spikegeneratorgroup.SpikeGeneratorGroup'and
    represent them in a dictionary format

    Parameters
    ----------
    spike_gen : brian2.input.spikegeneratorgroup.SpikeGeneratorGroup
            SpikeGenerator object

    Returns
    -------
    spikegen_dict : dict
                Dictionary with extracted information
    """

    spikegen_dict = {}

    # get name
    spikegen_dict['name'] = spike_gen.name

    # get size
    spikegen_dict['N'] = spike_gen.N

    # get indices of spiking neurons
    spikegen_dict['indices'] = spike_gen._neuron_index[:]

    # get spike times for defined neurons
    spikegen_dict['times'] = spike_gen.spike_time[:]

    # get spike period (default period is 0*second will be stored if not
    # mentioned by the user)
    spikegen_dict['period'] = spike_gen.period[:]

    return spikegen_dict


def collect_PoissonGroup(poisson_grp):
    """
    Extract information from 'brian2.input.poissongroup.PoissonGroup'
    and represent them in a dictionary format

    Parameters
    ----------
    poisson_grp : brian2.input.poissongroup.PoissonGroup
            PoissonGroup object

    Returns
    -------
    poisson_grp_dict : dict
                Dictionary with extracted information
    """

    poisson_grp_dict = {}

    # get name
    poisson_grp_dict['name'] = poisson_grp._name

    # get size
    poisson_grp_dict['N'] = poisson_grp._N

    # get rates (can be Quantity or str)
    poisson_grp_dict['rates'] = poisson_grp._rates

    # `run_regularly` / CodeRunner objects of poisson_grp
    for obj in poisson_grp.contained_objects:
        if type(obj) == CodeRunner:
            if 'run_regularly' not in poisson_grp_dict:
                poisson_grp_dict['run_regularly'] = []
            poisson_grp_dict['run_regularly'].append({
                                                'name': obj.name,
                                                'code': obj.abstract_code,
                                                'dt': obj.clock.dt
                                                })

    return poisson_grp_dict


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

    # get source object name
    state_mon_dict['source'] = state_mon.source.name

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

    spike_mon_dict = {}

    # collect name
    spike_mon_dict['name'] = spike_mon.name

    # collect source object name
    spike_mon_dict['source'] = spike_mon.source.name

    # collect record variables
    # by default spike_mon.record_variables is set() so change to list
    spike_mon_dict['variables'] = list(spike_mon.record_variables)

    # collect record indices and time
    # when `record = True`, `spike_mon.record` stores
    # the bool value without making it to a list unlike StateMonitor
    spike_mon_dict['record'] = spike_mon.record

    # collect name of the event
    spike_mon_dict['event'] = spike_mon.event

    # collect time-step
    spike_mon_dict['dt'] = spike_mon.clock.dt

    return spike_mon_dict


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
    poprate_mon_dict['source'] = poprate_mon.source.name

    # collect time-step
    poprate_mon_dict['dt'] = poprate_mon.clock.dt

    return poprate_mon_dict
