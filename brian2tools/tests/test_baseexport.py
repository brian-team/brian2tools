from brian2 import (NeuronGroup, SpikeGeneratorGroup,
                    PoissonGroup, Equations, start_scope,
                    numpy, Quantity, StateMonitor, SpikeMonitor,
                    PopulationRateMonitor)

from brian2.equations.equations import (DIFFERENTIAL_EQUATION,
                                        FLOAT, SUBEXPRESSION,
                                        PARAMETER, parse_string_equations)

from brian2 import (ms, mV, Hz, volt, second, umetre, siemens, cm,
                    ufarad, amp, hertz)

from brian2tools.baseexport.collector import (collect_NeuronGroup,
                                              collect_PoissonGroup,
                                              collect_SpikeGenerator,
                                              collect_StateMonitor,
                                              collect_SpikeMonitor,
                                              collect_PopulationRateMonitor)

import pytest


def test_simple_neurongroup():
    """
    Test dictionary representation of simple NeuronGroup
    """
    # example 1
    eqn = '''dv/dt = (1 - v) / tau : volt'''
    tau = 10 * ms
    size = 1

    grp = NeuronGroup(size, eqn, method='exact')
    neuron_dict = collect_NeuronGroup(grp)

    assert neuron_dict['N'] == size
    assert neuron_dict['user_method'] == 'exact'

    assert neuron_dict['equations']['v']['type'] == DIFFERENTIAL_EQUATION
    assert neuron_dict['equations']['v']['unit'] == volt
    assert neuron_dict['equations']['v']['var_type'] == FLOAT

    with pytest.raises(KeyError):
        neuron_dict['equations']['tau']

    eqn_obj = Equations(eqn)
    assert neuron_dict['equations']['v']['expr'] == eqn_obj['v'].expr.code

    # example 2

    start_scope()
    area = 100 * umetre ** 2
    g_L = 1e-2 * siemens * cm ** -2 * area
    E_L = 1000
    Cm = 1 * ufarad * cm ** -2 * area
    grp = NeuronGroup(10, '''dv/dt = I_leak / Cm : volt
                        I_leak = g_L*(E_L - v) : amp''')

    neuron_dict = collect_NeuronGroup(grp)

    assert neuron_dict['N'] == 10
    assert neuron_dict['user_method'] is None

    eqn_str = '''
    dv/dt = I_leak / Cm : volt
    I_leak = g_L*(E_L - v) : amp
    '''
    assert neuron_dict['equations']['v']['type'] == DIFFERENTIAL_EQUATION
    assert neuron_dict['equations']['v']['unit'] == volt
    assert neuron_dict['equations']['v']['var_type'] == FLOAT

    parsed = parse_string_equations(eqn_str)
    assert neuron_dict['equations']['v']['expr'] == parsed['v'].expr.code

    assert neuron_dict['equations']['I_leak']['type'] == SUBEXPRESSION
    assert neuron_dict['equations']['I_leak']['unit'] == amp
    assert neuron_dict['equations']['I_leak']['var_type'] == FLOAT
    assert neuron_dict['equations']['I_leak']['expr'] == 'g_L*(E_L - v)'

    with pytest.raises(KeyError):
        neuron_dict['events']


def test_spike_neurongroup():
    """
    Test dictionary representation of spiking neuron
    """
    eqn = ''' dv/dt = (v_th - v) / tau : volt
              v_th = 900 * mV :volt
              v_rest = -70 * mV :volt
              tau :second (constant)'''

    tau = 10 * ms
    size = 10

    grp = NeuronGroup(size, eqn, threshold='v > v_th',
                      reset='v = v_rest',
                      refractory=2 * ms)

    neuron_dict = collect_NeuronGroup(grp)

    assert neuron_dict['N'] == size
    assert neuron_dict['user_method'] is None

    eqns = Equations(eqn)
    assert neuron_dict['equations']['v']['type'] == DIFFERENTIAL_EQUATION
    assert neuron_dict['equations']['v']['unit'] == volt
    assert neuron_dict['equations']['v']['var_type'] == FLOAT
    assert neuron_dict['equations']['v']['expr'] == eqns['v'].expr.code

    assert neuron_dict['equations']['v_th']['type'] == SUBEXPRESSION
    assert neuron_dict['equations']['v_th']['unit'] == volt
    assert neuron_dict['equations']['v_th']['var_type'] == FLOAT
    assert neuron_dict['equations']['v_th']['expr'] == eqns['v_th'].expr.code

    assert neuron_dict['equations']['v_rest']['type'] == SUBEXPRESSION
    assert neuron_dict['equations']['v_rest']['unit'] == volt
    assert neuron_dict['equations']['v_rest']['var_type'] == FLOAT

    assert neuron_dict['equations']['tau']['type'] == PARAMETER
    assert neuron_dict['equations']['tau']['unit'] == second
    assert neuron_dict['equations']['tau']['var_type'] == FLOAT
    assert neuron_dict['equations']['tau']['flags'][0] == 'constant'

    assert neuron_dict['events']['spike']['threshold'] == 'v > v_th'
    assert neuron_dict['events']['spike']['reset'] == 'v = v_rest'
    assert neuron_dict['events']['spike']['refractory'] == Quantity(2 * ms)

    # example 2 with threshold but no reset

    start_scope()

    grp2 = NeuronGroup(size, '''dv/dt = (100 * mV - v) / tau_n : volt''',
                             threshold='v > 800 * mV',
                             method='euler')
    tau_n = 10 * ms

    neuron_dict2 = collect_NeuronGroup(grp2)
    assert neuron_dict2['events']['spike']['threshold'] == 'v > 800 * mV'

    with pytest.raises(KeyError):
        neuron_dict2['events']['spike']['reset']
    with pytest.raises(KeyError):
        neuron_dict2['events']['spike']['refractory']


def test_spikegenerator():
    """
    Test dictionary representation of SpikeGenerator
    """

    # example 1
    size = 1
    index = [0]
    time = [10] * ms

    spike_gen = SpikeGeneratorGroup(size, index, time)
    spike_gen_dict = collect_SpikeGenerator(spike_gen)

    assert spike_gen_dict['N'] == size
    assert spike_gen_dict['indices'] == [0]
    assert spike_gen_dict['indices'].dtype == int

    assert spike_gen_dict['times'] == time
    assert spike_gen_dict['times'].has_same_dimensions(10 * ms)
    assert spike_gen_dict['times'].dtype == float

    # example 2
    spike_gen2 = SpikeGeneratorGroup(10, index, time, period=20 * ms)
    spike_gen_dict = collect_SpikeGenerator(spike_gen2)

    assert spike_gen_dict['N'] == 10
    assert spike_gen_dict['period'] == [20] * ms
    assert spike_gen_dict['period'].has_same_dimensions(20 * ms)
    assert spike_gen_dict['period'].dtype == float


def test_poissongroup():
    """
    Test standard dictionary representation of PoissonGroup
    """

    # example1
    N = 10
    rates = numpy.arange(1, 11, step=1) * Hz

    poisongrp = PoissonGroup(N, rates)
    poisson_dict = collect_PoissonGroup(poisongrp)

    assert poisson_dict['N'] == N

    assert (poisson_dict['rates'] == rates).all()
    assert poisson_dict['rates'].has_same_dimensions(5 * Hz)
    assert poisson_dict['rates'].dtype == float

    # example2
    F = 10 * Hz
    poisongrp = PoissonGroup(N, rates='F + 2 * Hz')
    poisson_dict = collect_PoissonGroup(poisongrp)

    assert poisson_dict['rates'] == 'F + 2 * Hz'


def test_statemonitor():
    """
    Test collect_StateMonitor dictionary representation
    """

    # example 1
    grp = NeuronGroup(10, model='dv/dt = (1 - v) / tau :1',
                      method='euler')
    mon = StateMonitor(grp, 'v', record=True)
    statemon_dict = collect_StateMonitor(mon)

    assert statemon_dict['source'] == grp.name
    assert statemon_dict['record']
    assert statemon_dict['n_indices'] == 10
    assert statemon_dict['variables'] == ['v']

    # exmaple 2
    eqn = '''dvar1/dt = (var1 + 1) / tau :1
    var2 = var1 + 3 :1
    var3 = 2 + var1 :1
    '''
    grp2 = NeuronGroup(10, eqn, method='euler')
    mon2 = StateMonitor(grp2, ['var1', 'var3'], record=[2, 4, 6, 8],
                        dt=1 * second)
    statemon_dict2 = collect_StateMonitor(mon2)

    assert statemon_dict2['source'] == grp2.name
    assert statemon_dict2['variables'].sort() == ['var1', 'var3'].sort()
    assert 'var2' not in statemon_dict2['variables']
    assert not statemon_dict2['record'] is True
    assert (statemon_dict2['record'] == [2, 4, 6, 8]).all()
    assert statemon_dict2['dt'] == 1 * second

    # example 3
    mon3 = StateMonitor(grp, 'v', record=False)
    statemon_dict3 = collect_StateMonitor(mon3)

    assert not statemon_dict3['record'].size


def test_spikemonitor():
    """
    Test collector function for SpikeMonitor
    """

    # example 1
    grp = NeuronGroup(5, '''dv/dt = (v0 - v)/tau :volt''', method='exact',
                      threshold='v > v_th', reset='v = v0',
                      name="My_Neurons")
    tau = 10 * ms
    v0 = -70 * mV
    v_th = 800 * mV
    mon = SpikeMonitor(grp, 'v', record=[0, 4])
    mon_dict = collect_SpikeMonitor(mon)

    assert mon_dict['source'] == 'My_Neurons'
    assert mon_dict['variables'].sort() == ['i', 't', 'v'].sort()
    assert mon_dict['record'] == [0, 4]
    assert mon_dict['event'] == 'spike'

    # example 2
    pos = PoissonGroup(5, rates=100 * Hz)
    smon = SpikeMonitor(pos, record=[0, 1, 2, 3, 4])
    smon_dict = collect_SpikeMonitor(smon)

    assert smon_dict['source'] == pos.name
    assert 'i' in smon_dict['variables']

    assert smon_dict['record'] == [0, 1, 2, 3, 4]

    # example 3
    spk = SpikeGeneratorGroup(10, [2, 6, 8], [5 * ms, 10 * ms, 15 * ms])
    spkmon = SpikeMonitor(spk, record=True)
    smon_dict = collect_SpikeMonitor(spkmon)

    assert smon_dict['record']
    assert 't' in smon_dict['variables']
    assert smon_dict['source'] == spk.name


def test_PopulationRateMonitor():
    """
    Test collect_PopulationRateMonitor()
    """

    # /examples/frompapers.Brunel_Hakim_1999.html
    N = 50
    tau = 20*ms
    muext = 25*mV
    sigmaext = 1*mV
    Vr = 10*mV
    theta = 20*mV
    taurefr = 2*ms
    eqs = """
    dV/dt = (-V+muext + sigmaext * sqrt(tau) * xi)/tau : volt
    """
    group = NeuronGroup(N, eqs, threshold='V>theta',
                        reset='V=Vr', refractory=taurefr, method='euler')
    LFP = PopulationRateMonitor(group)
    pop_dict = collect_PopulationRateMonitor(LFP)

    assert pop_dict['name'] == LFP.name
    assert pop_dict['source'] == group.name
    assert pop_dict['dt'] == LFP.clock.dt


if __name__ == '__main__':

    test_simple_neurongroup()
    test_spike_neurongroup()
    test_spikegenerator()
    test_poissongroup()
    test_statemonitor()
    test_spikemonitor()
    test_PopulationRateMonitor()
