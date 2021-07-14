from brian2 import (NeuronGroup, SpikeGeneratorGroup,
                    PoissonGroup, Equations, start_scope,
                    numpy, Quantity, StateMonitor, SpikeMonitor,
                    PopulationRateMonitor, EventMonitor, set_device,
                    run, device, Network, Synapses, PoissonInput, TimedArray,
                    Function)
from brian2.core.namespace import get_local_namespace
from brian2.equations.equations import (DIFFERENTIAL_EQUATION,
                                        FLOAT, SUBEXPRESSION,
                                        PARAMETER, parse_string_equations)
from brian2 import (ms, us, mV, Hz, volt, second, umetre, siemens, cm,
                    ufarad, amp, hertz)
from brian2tools import baseexport
from brian2tools.baseexport.collector import *
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
    neuron_dict = collect_NeuronGroup(grp, get_local_namespace(0))

    assert neuron_dict['N'] == size
    assert neuron_dict['user_method'] == 'exact'
    assert neuron_dict['equations']['v']['type'] == DIFFERENTIAL_EQUATION
    assert neuron_dict['equations']['v']['unit'] == volt
    assert neuron_dict['equations']['v']['var_type'] == FLOAT

    with pytest.raises(KeyError):
        neuron_dict['equations']['tau']

    with pytest.raises(KeyError):
        neuron_dict['run_regularly']

    eqn_obj = Equations(eqn)
    assert neuron_dict['equations']['v']['expr'] == eqn_obj['v'].expr.code
    assert neuron_dict['identifiers']['tau'] == 10 * ms
    with pytest.raises(KeyError):
        neuron_dict['identifiers']['size']
    assert neuron_dict['when'] == 'groups'
    assert neuron_dict['order'] == 0

    # example 2
    start_scope()
    area = 100 * umetre ** 2
    g_L = 1e-2 * siemens * cm ** -2 * area
    E_L = 1000
    div_2 = 2
    dim_2 = 0.02 * amp
    Cm = 1 * ufarad * cm ** -2 * area
    grp = NeuronGroup(10, '''dv/dt = I_leak / Cm : volt
                        I_leak = g_L*(E_L - v) : amp''')
    grp.run_regularly('v = v / div_2', dt=20 * ms, name='i_am_run_reg_senior')
    grp.run_regularly('I_leak = I_leak + dim_2', dt=10 * ms,
                      name='i_am_run_reg_junior')

    neuron_dict = collect_NeuronGroup(grp, get_local_namespace(0))

    assert neuron_dict['N'] == 10
    assert neuron_dict['user_method'] is None
    assert neuron_dict['when'] == 'groups'
    assert neuron_dict['order'] == 0
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
    assert neuron_dict['identifiers']['g_L'] == g_L
    assert neuron_dict['identifiers']['Cm'] == Cm
    assert neuron_dict['identifiers']['div_2'] == div_2
    assert neuron_dict['identifiers']['dim_2'] == dim_2

    with pytest.raises(KeyError):
        neuron_dict['events']
    with pytest.raises(KeyError):
        neuron_dict['identifiers']['area']

    assert neuron_dict['run_regularly'][0]['name'] == 'i_am_run_reg_senior'
    assert neuron_dict['run_regularly'][1]['name'] == 'i_am_run_reg_junior'
    assert neuron_dict['run_regularly'][0]['code'] == 'v = v / div_2'
    assert (neuron_dict['run_regularly'][1]['code'] ==
            'I_leak = I_leak + dim_2')
    assert neuron_dict['run_regularly'][0]['dt'] == 20 * ms
    assert neuron_dict['run_regularly'][1]['dt'] == 10 * ms
    assert neuron_dict['run_regularly'][0]['when'] == 'start'
    assert neuron_dict['run_regularly'][1]['when'] == 'start'
    assert neuron_dict['run_regularly'][0]['order'] == 0
    assert neuron_dict['run_regularly'][1]['order'] == 0

    with pytest.raises(IndexError):
        neuron_dict['run_regularly'][2]


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

    neuron_dict = collect_NeuronGroup(grp, get_local_namespace(0))

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

    thresholder = grp.thresholder['spike']
    neuron_events = neuron_dict['events']['spike']
    assert neuron_events['threshold']['code'] == 'v > v_th'
    assert neuron_events['threshold']['when'] == thresholder.when
    assert neuron_events['threshold']['order'] == thresholder.order
    assert neuron_events['threshold']['dt'] == grp.clock.dt

    resetter = grp.resetter['spike']
    assert neuron_events['reset']['code'] == 'v = v_rest'
    assert neuron_events['reset']['when'] == resetter.when
    assert neuron_events['reset']['order'] == resetter.order
    assert neuron_events['reset']['dt'] == resetter.clock.dt

    assert neuron_dict['events']['spike']['refractory'] == Quantity(2 * ms)

    # example 2 with threshold but no reset

    start_scope()
    grp2 = NeuronGroup(size, '''dv/dt = (100 * mV - v) / tau_n : volt''',
                             threshold='v > 800 * mV', reset='v = 0*mV',
                             method='euler')
    tau_n = 10 * ms

    neuron_dict2 = collect_NeuronGroup(grp2, get_local_namespace(0))
    thresholder = grp2.thresholder['spike']
    neuron_events = neuron_dict2['events']['spike']
    assert neuron_events['threshold']['code'] == 'v > 800 * mV'
    assert neuron_events['threshold']['when'] == thresholder.when
    assert neuron_events['threshold']['order'] == thresholder.order
    assert neuron_events['threshold']['dt'] == grp2.clock.dt

    with pytest.raises(KeyError):
        neuron_dict2['events']['spike']['reset']
        neuron_dict2['events']['spike']['refractory']


def test_custom_events_neurongroup():

    start_scope()
    grp = NeuronGroup(10, 'dvar/dt = (100 - var) / tau_n : 1',
                      events={'test_event': 'var > 70'}, method='exact')
    tau_n = 10 * ms
    grp.thresholder['test_event'].clock.dt = 10 * ms
    neuron_dict = collect_NeuronGroup(grp, get_local_namespace(0))

    custom_event = neuron_dict['events']['test_event']
    thresholder = custom_event['threshold']

    assert thresholder['code'] == 'var > 70'
    assert thresholder['when'] == grp.thresholder['test_event'].when
    assert thresholder['order'] == grp.thresholder['test_event'].order
    assert thresholder['dt'] == 10 * ms

    with pytest.raises(KeyError):
        neuron_dict['events']['spike']
        custom_event['reset']
        custom_event['refractory']

    # check with reset
    grp.run_on_event('test_event', 'var = -10')
    neuron_dict = collect_NeuronGroup(grp, get_local_namespace(0))
    custom_event = neuron_dict['events']['test_event']
    resetter = custom_event['reset']

    assert resetter['code'] == 'var = -10'
    assert resetter['when'] == grp.resetter['test_event'].when
    assert resetter['order'] == grp.resetter['test_event'].order
    assert resetter['dt'] == thresholder['dt']


def test_spikegenerator():
    """
    Test dictionary representation of SpikeGenerator
    """

    # example 1
    size = 1
    index = [0]
    time = [0.01] * second

    spike_gen = SpikeGeneratorGroup(size, index, time)
    spike_gen_dict = collect_SpikeGenerator(spike_gen, get_local_namespace(0))

    assert spike_gen_dict['N'] == size
    assert spike_gen_dict['indices'] == [0]
    assert spike_gen_dict['indices'].dtype == int

    assert float(spike_gen_dict['times']) == float(time)
    assert spike_gen_dict['times'][:].dimensions == second
    assert spike_gen_dict['times'].dtype == float

    # example 2
    spike_gen2 = SpikeGeneratorGroup(10, index, time, period=20 * ms)
    var = 0.00002
    spike_gen2.run_regularly('var = var + 1', dt=10 * ms, name='spikerr')
    spike_gen_dict = collect_SpikeGenerator(spike_gen2,
                                            get_local_namespace(0))

    assert spike_gen_dict['N'] == 10
    assert spike_gen_dict['period'] == [20] * ms
    assert spike_gen_dict['period'].has_same_dimensions(20 * ms)
    assert spike_gen_dict['period'].dtype == float

    # (check run_regularly)
    assert spike_gen_dict['run_regularly'][0]['name'] == 'spikerr'
    assert spike_gen_dict['run_regularly'][0]['code'] == 'var = var + 1'
    assert spike_gen_dict['run_regularly'][0]['dt'] == 10 * ms
    assert spike_gen_dict['run_regularly'][0]['when'] == 'start'
    assert spike_gen_dict['run_regularly'][0]['order'] == 0
    assert spike_gen_dict['identifiers']['var'] == var
    with pytest.raises(IndexError):
        spike_gen_dict['run_regularly'][1]


def test_poissongroup():
    """
    Test standard dictionary representation of PoissonGroup
    """

    # example1
    N = 10
    rates = numpy.arange(1, 11, step=1) * Hz

    poisongrp = PoissonGroup(N, rates)
    poisson_dict = collect_PoissonGroup(poisongrp, get_local_namespace(0))

    assert poisson_dict['N'] == N

    assert (poisson_dict['rates'] == rates).all()
    assert poisson_dict['rates'].has_same_dimensions(5 * Hz)
    assert poisson_dict['rates'].dtype == float

    with pytest.raises(KeyError):
        assert poisson_dict['run_regularly']

    # example2
    F = 10 * Hz
    three = 3 * Hz
    two = 2 * Hz
    poisongrp = PoissonGroup(N, rates='F + two')
    poisongrp.run_regularly('F = F + three', dt=10 * ms,
                            name="Run_at_0_01")
    poisson_dict = collect_PoissonGroup(poisongrp, get_local_namespace(0))

    assert poisson_dict['rates'] == 'F + two'
    assert poisson_dict['run_regularly'][0]['name'] == 'Run_at_0_01'
    assert poisson_dict['run_regularly'][0]['code'] == 'F = F + three'
    assert poisson_dict['run_regularly'][0]['dt'] == 10 * ms
    assert poisson_dict['run_regularly'][0]['when'] == 'start'
    assert poisson_dict['run_regularly'][0]['order'] == 0

    assert poisson_dict['identifiers']['three'] == three
    assert poisson_dict['identifiers']['two'] == two

    with pytest.raises(IndexError):
        poisson_dict['run_regularly'][1]


def test_poissoninput():
    """
    Test collect_PoissonInput()
    """
    # test 1
    start_scope()
    v_th = 1 * volt
    grp = NeuronGroup(10, 'dv/dt = (v_th - v)/(10*ms) :volt', method='euler',
                      threshold='v>100*mV', reset='v=0*mV')
    poi = PoissonInput(grp, 'v', 10, 1*Hz, 'v_th * rand() + 1*mV')
    poi_dict = collect_PoissonInput(poi, get_local_namespace(0))
    assert poi_dict['target'] == grp.name
    assert poi_dict['rate'] == 1*Hz
    assert poi_dict['N'] == 10
    assert poi_dict['target_var'] == 'v'
    assert poi_dict['when'] == poi.when
    assert poi_dict['order'] == poi.order
    assert poi_dict['dt'] == poi.clock.dt
    assert poi_dict['identifiers']['v_th'] == v_th
    # test 2
    grp2 = NeuronGroup(10, 'dv_1_2_3/dt = (v_th - v_1_2_3)/(10*ms) :volt',
                       method='euler', threshold='v_1_2_3>v_th',
                       reset='v_1_2_3=-v_th')
    poi2 = PoissonInput(grp2, 'v_1_2_3', 0, 0*Hz, v_th)
    poi_dict = collect_PoissonInput(poi2, get_local_namespace(0))
    assert poi_dict['target'] == grp2.name
    assert poi_dict['rate'] == 0*Hz
    assert poi_dict['N'] == 0
    assert poi_dict['target_var'] == 'v_1_2_3'
    with pytest.raises(KeyError):
        poi_dict['identifiers']


def test_Subgroup():
    """
    Test Subgroup
    """
    eqn = '''
    dv/dt = (1 - v) / tau :1
    '''
    tau = 10 * ms
    group = NeuronGroup(10, eqn, threshold='v>10', reset='v=0',
                        method='euler')
    sub_a = group[0:5]
    sub_b = group[0:10]
    syn = Synapses(sub_a, sub_b)
    syn.connect(p=0.8)
    mon = StateMonitor(group[0:7], 'v', record=1)
    sub_a.v = 1
    sub_b.v = -1
    mon_dict = collect_StateMonitor(mon)
    assert mon_dict['source']['group'] == group.name
    assert mon_dict['source']['start'] == 0
    assert mon_dict['source']['stop'] == 6
    syn_dict = collect_Synapses(syn, get_local_namespace(0))
    assert syn_dict['source']['group'] == group.name
    assert syn_dict['target']['start'] == 0
    assert syn_dict['source']['stop'] == 4


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
    assert statemon_dict['when'] == 'start'
    assert statemon_dict['order'] == 0

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
    assert statemon_dict3['when'] == 'start'
    assert statemon_dict3['order'] == 0


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
    assert mon_dict['when'] == 'thresholds'
    assert mon_dict['order'] == 1

    # example 2
    pos = PoissonGroup(5, rates=100 * Hz)
    smon = SpikeMonitor(pos, record=[0, 1, 2, 3, 4])
    smon_dict = collect_SpikeMonitor(smon)

    assert smon_dict['source'] == pos.name
    assert 'i' in smon_dict['variables']

    assert smon_dict['record'] == [0, 1, 2, 3, 4]
    assert smon_dict['when'] == 'thresholds'
    assert smon_dict['order'] == 1

    # example 3
    spk = SpikeGeneratorGroup(10, [2, 6, 8], [5 * ms, 10 * ms, 15 * ms])
    spkmon = SpikeMonitor(spk, ['t', 'i'], record=0)
    smon_dict = collect_SpikeMonitor(spkmon)

    assert smon_dict['record'] == np.array([0])
    assert 't' in smon_dict['variables']
    assert smon_dict['source'] == spk.name
    assert smon_dict['when'] == 'thresholds'
    assert smon_dict['order'] == 1


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
    assert pop_dict['when'] == 'end'
    assert pop_dict['order'] == 0


def test_EventMonitor():
    """
    Test collect_EventMonitor()
    """
    grp = NeuronGroup(10, 'dvar/dt = (100 - var) / tau_n : 1',
                      events={'test_event': 'var > 70'}, method='exact')

    event_mon = EventMonitor(grp, 'test_event', 'var', record=True)
    event_mon_dict = collect_EventMonitor(event_mon)

    assert event_mon_dict['name'] == event_mon.name
    assert event_mon_dict['source'] == grp.name
    assert event_mon_dict['record']
    assert event_mon_dict['variables'].sort() == ['i', 'var', 't'].sort()
    assert event_mon_dict['when'] == 'after_thresholds'
    assert event_mon_dict['order'] == 1
    assert event_mon_dict['event'] == 'test_event'


def test_timedarray_customfunc():
    """
    Test TimedArray and Custom Functions
    """
    # simple timedarray test
    ta = TimedArray([1, 2, 3, 4] * mV, dt=0.1*ms)
    eqn = 'v = ta(t) :volt'
    G = NeuronGroup(1, eqn, method='euler')
    neuro_dict = collect_NeuronGroup(G, get_local_namespace(0))
    ta_dict = neuro_dict['identifiers']['ta']
    assert ta_dict['name'] == ta.name
    assert (ta_dict['values'] == [1, 2, 3, 4] * mV).all()
    assert float(ta_dict['dt']) == float(ta.dt)
    assert ta_dict['ndim'] == 1
    assert ta_dict['type'] == 'timedarray'

    # test 2
    ta2d = TimedArray([[1, 2], [3, 4], [5, 6]]*mV, dt=1*ms)
    G2 = NeuronGroup(4, 'v = ta2d(t, i%2) : volt')
    neuro_dict = collect_NeuronGroup(G2, get_local_namespace(0))
    ta_dict = neuro_dict['identifiers']['ta2d']
    assert ta_dict['name'] == ta2d.name
    assert (ta_dict['values'] == [[1, 2], [3, 4], [5, 6]] * mV).all()
    assert float(ta_dict['dt']) == float(ta2d.dt)
    assert ta_dict['ndim'] == 2
    assert ta_dict['type'] == 'timedarray'

    # test 3
    def da(x1, x2):
        return (x1 - x2)
    a = 1*mV
    b = 1*mV
    da = Function(da, arg_units=[volt, volt],
                  return_unit=volt)
    grp = NeuronGroup(1, 'v = da(a, b) :volt', method='euler')
    neuro_dict = collect_NeuronGroup(grp, get_local_namespace(0))
    identi = neuro_dict['identifiers']['da']
    assert identi['type'] == 'custom_func'
    assert identi['arg_units'] == da._arg_units
    assert identi['arg_types'] == da._arg_types
    assert identi['return_unit'] == da._return_unit
    assert identi['return_type'] == da._return_type


def test_Synapses():
    """
    Test cases to verify standard export on Synapses
    """
    # check simple Synapses
    eqn = 'dv/dt = (1 - v)/tau :1'
    tau = 1 * ms
    P = NeuronGroup(1, eqn, method='euler', threshold='v>0.7', reset='v=0')
    Q = NeuronGroup(1, eqn, method='euler')
    w = 1
    S = Synapses(P, Q, on_pre='v += w')
    syn_dict = collect_Synapses(S, get_local_namespace(0))

    assert syn_dict['name'] == S.name

    pathways = syn_dict['pathways'][0]
    assert pathways['dt'] == S._pathways[0].clock.dt
    assert pathways['prepost'] == 'pre'
    assert pathways['source'] == P.name
    assert pathways['target'] == Q.name
    assert pathways['order'] == -1
    assert pathways['when'] == 'synapses'
    assert pathways['code'] == 'v += w'
    assert pathways['event'] == 'spike'
    with pytest.raises(KeyError):
        syn_dict['equations']
        syn_dict['user_method']
        syn_dict['summed_variables']
        syn_dict['identifiers']
        pathways['delay']

    # test 2: check pre, post, eqns, identifiers and summed variables
    start_scope()
    eqn = '''
    dv/dt = (1 - v)/tau :1
    summ_v :1
    '''
    tau = 1 * ms
    P = NeuronGroup(1, eqn, method='euler', threshold='v>0.7', reset='v=0')
    Q = NeuronGroup(1, eqn, method='euler', threshold='v>0.9', reset='v=0')
    eqn = '''
    dvar/dt = -var/tau :1 (event-driven)
    dvarr/dt = -varr/tau :1 (clock-driven)
    w = 1 :1
    summ_v_pre = kiki :1 (summed)
    '''
    kiki = 0.01
    preki = 0
    postki = -0.01
    S = Synapses(P, Q, eqn, on_pre='v += preki', on_post='v -= w + postki',
                 delay=2*ms, method='euler')
    syn_dict = collect_Synapses(S, get_local_namespace(0))

    var = syn_dict['equations']['var']
    assert var['type'] == 'differential equation'
    assert var['var_type'] == 'float'
    assert var['expr'] == '-var/tau'
    assert var['flags'][0] == 'event-driven'
    varr = syn_dict['equations']['varr']
    assert varr['type'] == 'differential equation'
    assert varr['var_type'] == 'float'
    assert varr['expr'] == '-varr/tau'
    assert varr['flags'][0] == 'clock-driven'
    assert syn_dict['equations']['w']['type'] == 'subexpression'
    assert syn_dict['equations']['w']['expr'] == '1'
    assert syn_dict['equations']['w']['var_type'] == 'float'
    assert syn_dict['summed_variables'][0]['target'] == P.name
    pre_path = syn_dict['pathways'][0]
    post_path = syn_dict['pathways'][1]
    assert pre_path['delay'] == 2*ms
    assert pre_path['prepost'] == 'pre'
    assert pre_path['code'] == 'v += preki'
    assert post_path['prepost'] == 'post'
    assert post_path['code'] == 'v -= w + postki'
    with pytest.raises(KeyError):
        post_path['delay']
    assert syn_dict['user_method'] == 'euler'
    assert syn_dict['identifiers']['preki'] == 0
    assert syn_dict['identifiers']['postki'] == -0.01


def test_ExportDevice_options():
    """
    Test the run and build options of ExportDevice
    """
    # test1
    set_device('exporter')
    grp = NeuronGroup(10, 'eqn = 1:1', method='exact')
    run(100 * ms)
    _ = StateMonitor(grp, 'eqn', record=False)
    with pytest.raises(RuntimeError):
        run(100 * ms)

    # test2
    device.reinit()
    with pytest.raises(RuntimeError):
        device.build()

    # test3
    start_scope()
    net = Network()
    set_device('exporter', build_on_run=False)
    grp = NeuronGroup(10, 'eqn = 1:1', method='exact')
    net.add(grp)
    net.run(10 * ms)
    pogrp = PoissonGroup(10, rates=10 * Hz)
    net.add(pogrp)
    net.run(10 * ms)
    mon = StateMonitor(grp, 'eqn', record=False)
    net.add(mon)
    net.run(10 * ms)
    device.build()
    device.reinit()


def test_ExportDevice_basic():
    """
    Test the components and structure of the dictionary exported
    by ExportDevice
    """
    start_scope()
    set_device('exporter')

    grp = NeuronGroup(10, 'dv/dt = (1-v)/tau :1', method='exact',
                      threshold='v > 0.5', reset='v = 0', refractory=2 * ms)
    tau = 10 * ms
    rate = '1/tau'
    grp.v['i > 2 and i < 5'] = -0.2
    pgrp = PoissonGroup(10, rates=rate)
    smon = SpikeMonitor(pgrp)
    smon.active = False
    netobj = Network(grp, pgrp, smon)
    netobj.run(100*ms)
    dev_dict = device.runs
    # check the structure and components in dev_dict
    assert dev_dict[0]['duration'] == 100 * ms
    assert dev_dict[0]['inactive'][0] == smon.name
    components = dev_dict[0]['components']
    assert components['spikemonitor'][0]
    assert components['poissongroup'][0]
    assert components['neurongroup'][0]
    initializers = dev_dict[0]['initializers_connectors']
    assert initializers[0]['source'] == grp.name
    assert initializers[0]['variable'] == 'v'
    assert initializers[0]['index'] == 'i > 2 and i < 5'
    # TODO: why not a Quantity type?
    assert initializers[0]['value'] == '-0.2'
    with pytest.raises(KeyError):
        initializers[0]['identifiers']
    device.reinit()

    start_scope()
    set_device('exporter', build_on_run=False)
    tau = 10 * ms
    v0 = -70 * mV
    vth = 800 * mV
    grp = NeuronGroup(10, 'dv/dt = (v0-v)/tau :volt', method='exact',
                      threshold='v > vth', reset='v = v0', refractory=2 * ms)
    v0 = -80 * mV
    grp.v[:] = 'v0 + 2 * mV'
    smon = StateMonitor(grp, 'v', record=True)
    smon.active = False
    net = Network(grp, smon)
    net.run(10 * ms)  # first run
    v0 = -75 * mV
    grp.v[3:8] = list(range(3, 8)) * mV
    smon.active = True
    net.run(20 * ms)  # second run
    v_new = -5 * mV
    grp.v['i >= 5'] = 'v0 + v_new'
    v_new = -10 * mV
    grp.v['i < 5'] = 'v0 - v_new'
    spikemon = SpikeMonitor(grp)
    net.add(spikemon)
    net.run(5 * ms)  # third run
    dev_dict = device.runs
    # check run1
    assert dev_dict[0]['duration'] == 10 * ms
    assert dev_dict[0]['inactive'][0] == smon.name
    components = dev_dict[0]['components']
    assert components['statemonitor'][0]
    assert components['neurongroup'][0]
    initializers = dev_dict[0]['initializers_connectors']
    assert initializers[0]['source'] == grp.name
    assert initializers[0]['variable'] == 'v'
    assert initializers[0]['index']
    assert initializers[0]['value'] == 'v0 + 2 * mV'
    assert initializers[0]['identifiers']['v0'] == -80 * mV
    with pytest.raises(KeyError):
        initializers[0]['identifiers']['mV']
    # check run2
    assert dev_dict[1]['duration'] == 20 * ms
    initializers = dev_dict[1]['initializers_connectors']
    assert initializers[0]['source'] == grp.name
    assert initializers[0]['variable'] == 'v'
    assert (initializers[0]['index'] == grp.indices[slice(3, 8, None)]).all()
    assert (initializers[0]['value'] == list(range(3, 8)) * mV).all()
    with pytest.raises(KeyError):
        dev_dict[1]['inactive']
        initializers[1]['identifiers']
    # check run3
    assert dev_dict[2]['duration'] == 5 * ms
    with pytest.raises(KeyError):
        dev_dict[2]['inactive']
    assert dev_dict[2]['components']['spikemonitor']
    initializers = dev_dict[2]['initializers_connectors']
    assert initializers[0]['source'] == grp.name
    assert initializers[0]['variable'] == 'v'
    assert initializers[0]['index'] == 'i >= 5'
    assert initializers[0]['value'] == 'v0 + v_new'
    assert initializers[0]['identifiers']['v0'] == -75 * mV
    assert initializers[0]['identifiers']['v_new'] == -5 * mV
    assert initializers[1]['index'] == 'i < 5'
    assert initializers[1]['value'] == 'v0 - v_new'
    assert initializers[1]['identifiers']['v_new'] == -10 * mV
    with pytest.raises(IndexError):
        initializers[2]
        dev_dict[3]
    device.reinit()


def test_synapse_init():
    # check initializations validity for synapse variables
    start_scope()
    set_device('exporter')
    eqn = 'dv/dt = -v/tau :1'
    tau = 1 * ms
    w = 1
    P = NeuronGroup(5, eqn, method='euler')
    Q = NeuronGroup(10, eqn, method='euler')
    S = Synapses(P, Q, 'g :1')
    S.connect()
    # allowable
    S.g['i>10'] = 10
    S.g[-1] = -1
    S.g[10000] = 'rand() + w + w'
    mon = StateMonitor(S, 'g', record=[0, 1])
    run(1*ms)
    # not allowable
    with pytest.raises(NotImplementedError):
        S.g[0:1000] = -1
        run(0.5*ms)
    with pytest.raises(NotImplementedError):
        S.g[0:1] = 'rand() + 10'
        run(0.25*ms)
    with pytest.raises(NotImplementedError):
        _ = StateMonitor(S, 'g', S.g[0:10])
    device.reinit()


def test_synapse_connect_cond():
    # check connectors
    start_scope()
    set_device('exporter')
    eqn = 'dv/dt = (1 - v)/tau :1'
    tau = 1 * ms
    P = NeuronGroup(5, eqn, method='euler')
    Q = NeuronGroup(10, eqn, method='euler')
    w = 1
    tata = 2
    bye = 2
    my_prob = -1
    S = Synapses(P, Q)
    S.connect('tata > bye', p='my_prob', n=5)
    run(1*ms)
    connect = device.runs[0]['initializers_connectors'][0]
    assert connect['probability'] == 'my_prob'
    assert connect['n_connections'] == 5
    assert connect['type'] == 'connect'
    assert connect['identifiers']['tata'] == bye
    with pytest.raises(KeyError):
        connect['i']
        connect['j']
    device.reinit()


def test_synapse_connect_ij():
    # connector test 2
    start_scope()
    set_device('exporter', build_on_run=False)
    tau = 10 * ms
    eqn = 'dv/dt = (1 - v)/tau :1'
    my_prob = -1
    Source = NeuronGroup(10, eqn, method='exact')
    S1 = Synapses(Source, Source)
    nett = Network(Source, S1)
    S1.connect(i=[0, 1], j=[1, 2], p='my_prob')
    nett.run(1*ms)
    connect2 = device.runs[0]['initializers_connectors'][0]
    assert connect2['i'] == [0, 1]
    assert connect2['j'] == [1, 2]
    assert connect2['identifiers']['my_prob'] == -1
    with pytest.raises(KeyError):
        connect2['condition']
    device.reinit()


def test_synapse_connect_generator():
    # connector test 3
    start_scope()
    set_device('exporter', build_on_run=False)
    tau = 1 * ms
    eqn = 'dv/dt = (1 - v)/tau :1'
    Source = NeuronGroup(10, eqn, method='exact')
    S1 = Synapses(Source, Source)
    nett2 = Network(Source, S1)
    S1.connect(j='k for k in range(0, i+1)')
    nett2.run(1*ms)
    connect3 = device.runs[0]['initializers_connectors'][0]
    assert connect3['j'] == 'k for k in range(0, i+1)'
    device.reinit()


def test_ExportDevice_unsupported():
    """
    Test whether unsupported objects for standard format export
    are raising Error
    """
    start_scope()
    set_device('exporter')
    eqn = '''
    v = 1 :1
    g :1
    '''
    G = NeuronGroup(1, eqn)
    _ = PoissonInput(G, 'g', 1, 1 * Hz, 1)
    # with pytest.raises(NotImplementedError):
    run(10 * ms)


if __name__ == '__main__':

    test_simple_neurongroup()
    test_spike_neurongroup()
    test_spikegenerator()
    test_poissongroup()
    test_poissoninput()
    test_Subgroup()
    test_statemonitor()
    test_spikemonitor()
    test_PopulationRateMonitor()
    test_EventMonitor()
    test_timedarray_customfunc()
    test_custom_events_neurongroup()
    test_Synapses()
    test_ExportDevice_options()
    test_ExportDevice_basic()
    test_ExportDevice_unsupported()  # TODO: not checking anything
    test_synapse_init()
    test_synapse_connect_cond()
    test_synapse_connect_generator()
    test_synapse_connect_ij()
