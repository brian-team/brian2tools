"""
The file contains simple functions to collect information
from BrianObjects and represent them in a standard
dictionary format. The parts of the file shall be reused
with standard format exporter.
"""
from brian2.equations.equations import PARAMETER


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
    
    return poisson_grp_dict
