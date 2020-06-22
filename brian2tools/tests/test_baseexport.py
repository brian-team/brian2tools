from brian2 import (NeuronGroup, SpikeGeneratorGroup,
                    PoissonGroup, Equations, start_scope, 
                    numpy, Quantity)

from brian2.equations.equations import (DIFFERENTIAL_EQUATION,
                                        FLOAT, Expression, SUBEXPRESSION,
                                        PARAMETER, parse_string_equations)

from brian2 import (ms, mV, Hz, volt, second, umetre, siemens, cm,
                    ufarad, amp, hertz)
import pytest

from brian2tools import (collect_NeuronGroup, collect_PoissonGroup,
                        collect_SpikeGenerator)

def test_simple_neurongroup():
    """
    Test dictionary representation of simple NeuronGroup 
    """
    # example 1
    eqn = ''' dv/dt = (1 - v) / tau : volt'''
    tau = 10 * ms
    size = 1
    grp = NeuronGroup(size, eqn, method = 'exact')

    neuron_dict = collect_NeuronGroup(grp)

    assert neuron_dict['N'] == size
    assert neuron_dict['user_method'] == 'exact'

    assert neuron_dict['equations']['v']['type'] == DIFFERENTIAL_EQUATION
    assert neuron_dict['equations']['v']['unit'] == volt
    assert neuron_dict['equations']['v']['var_type'] == FLOAT

    with pytest.raises(KeyError):
        neuron_dict['equations']['tau']

    assert neuron_dict['equations']['v']['expr'] == Equations(eqn)['v'].expr
    
    #example 2

    start_scope()
    
    area = 100 * umetre ** 2
    g_L = 1e-2 * siemens * cm ** -2 * area
    E_L = 1000
    Cm = 1 * ufarad * cm ** -2 * area
    grp = NeuronGroup(10, '''dv/dt = I_leak / Cm : volt
                        I_leak = g_L*(E_L - v) : amp''')

    neuron_dict = collect_NeuronGroup(grp)

    assert neuron_dict['N'] == 10
    assert neuron_dict['user_method'] == None
    
    eqn_str = '''
    dv/dt = I_leak / Cm : volt
    I_leak = g_L*(E_L - v) : amp
    '''
    assert neuron_dict['equations']['v']['type'] == DIFFERENTIAL_EQUATION
    assert neuron_dict['equations']['v']['unit'] == volt
    assert neuron_dict['equations']['v']['var_type'] == FLOAT
    assert neuron_dict['equations']['v']['expr'] == parse_string_equations(eqn_str)['v'].expr

    assert neuron_dict['equations']['I_leak']['type'] == SUBEXPRESSION
    assert neuron_dict['equations']['I_leak']['unit'] == amp
    assert neuron_dict['equations']['I_leak']['var_type'] == FLOAT
    assert neuron_dict['equations']['I_leak']['expr'] == Expression('g_L*(E_L - v)')

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
    grp = NeuronGroup(size, eqn, threshold = 'v > v_th', reset = 'v = v_rest', refractory = 2 * ms)
    
    neuron_dict = collect_NeuronGroup(grp)

    assert neuron_dict['N'] == size
    assert neuron_dict['user_method'] == None

    assert neuron_dict['equations']['v']['type'] == DIFFERENTIAL_EQUATION
    assert neuron_dict['equations']['v']['unit'] == volt
    assert neuron_dict['equations']['v']['var_type'] == FLOAT
    assert neuron_dict['equations']['v']['expr'] == Equations(eqn)['v'].expr

    assert neuron_dict['equations']['v_th']['type'] == SUBEXPRESSION
    assert neuron_dict['equations']['v_th']['unit'] == volt
    assert neuron_dict['equations']['v_th']['var_type'] == FLOAT
    assert neuron_dict['equations']['v_th']['expr'] == Equations(eqn)['v_th'].expr
    
    assert neuron_dict['equations']['v_rest']['type'] == SUBEXPRESSION
    assert neuron_dict['equations']['v_rest']['unit'] == volt
    assert neuron_dict['equations']['v_rest']['var_type'] == FLOAT
    assert neuron_dict['equations']['v_rest']['expr'] == Equations(eqn)['v_rest'].expr

    assert neuron_dict['equations']['tau']['type'] == PARAMETER
    assert neuron_dict['equations']['tau']['unit'] == second
    assert neuron_dict['equations']['tau']['var_type'] == FLOAT
    assert neuron_dict['equations']['tau']['flags'][0] == 'constant'

def test_spikegenerator():
    """
    Test dictionary representation of SpikeGenerator
    """
    
    #example 1
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

    #example 2
    spike_gen2 = SpikeGeneratorGroup(10, index, time, period = 20 * ms)
    spike_gen_dict = collect_SpikeGenerator(spike_gen2)

    assert spike_gen_dict['N'] == 10
    assert spike_gen_dict['period'] == [20] * ms
    assert spike_gen_dict['period'].has_same_dimensions(20 * ms)
    assert spike_gen_dict['period'].dtype == float 
    
def test_poissongroup():
    """
    Test standard dictionary representation of PoissonGroup
    """

    #example1
    N = 10
    rates = numpy.arange(1, 11, step = 1) * Hz

    poisongrp = PoissonGroup(N, rates)
    poisson_dict = collect_PoissonGroup(poisongrp)
    
    assert poisson_dict['N'] == N
    
    assert (poisson_dict['rates'] == rates).all()
    assert poisson_dict['rates'].has_same_dimensions(5 * Hz)
    assert poisson_dict['rates'].dtype == float


    #example2
    F = 10 * Hz
    poisongrp = PoissonGroup(N, rates = 'F + 2 * Hz')
    poisson_dict = collect_PoissonGroup(poisongrp) 

    assert poisson_dict['rates'] == Expression('F + 2 * Hz').code

if __name__ == '__main__':

    test_simple_neurongroup()
    test_spike_neurongroup()
    test_spikegenerator()
    test_poissongroup()
