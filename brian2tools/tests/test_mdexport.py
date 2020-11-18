"""
Test cases to check `mdexport` package
"""
from brian2 import (NeuronGroup, StateMonitor, Network, set_device,
                    SpikeGeneratorGroup, PoissonGroup, Synapses,
                    StateMonitor, SpikeMonitor, EventMonitor, device, run,
                    Equations, array)
from brian2 import (ms, nS, mV, Hz, volt, second, umetre, msiemens, cm,
                    ufarad, siemens)
from brian2tools import mdexport, MdExpander
import pytest
import re


def _markdown_lint(md_str):
    """
    Simple markdown lint to check any syntax errors
    """
    stack = []
    # symbols to consider
    symbols = ['**', '$', '|', '{', '}', '(', ')', '`']

    for char in md_str:
        # check syntax symbols
        if char in symbols:
            if stack:
                if char == stack[-1]:
                    stack = stack[:-1]
                elif char in ['}', ')']:
                    if ((stack[-1] == '{' and char == '}') or
                       (stack[-1] == '(' and char == ')')):
                        stack = stack[:-1]
                else:
                    stack.append(char)
            else:
                stack.append(char)
    if stack:
        raise SyntaxError("Markdown syntax is incorrect")
    return True


def test_simple_syntax():
    """
    Simple example
    """
    set_device('markdown')
    N = 10
    tau = 10 * ms
    v_th = 0.9 * volt
    v_rest = -79 * mV
    eqn = 'dv/dt = (v_th - v)/tau :volt'
    refractory = 'randn() * tau / N'
    rates = 'rand() * 5 * Hz'
    group = NeuronGroup(N, eqn, method='euler', threshold='v > v_th',
                        reset='v = v_rest; v = rand() * v_rest',
                        refractory=refractory,
                        events={'custom': 'v > v_th + 10 * mV',
                        'custom_1': 'v > v_th - 10 * mV'})
    group.run_on_event('custom', 'v = v_rest')
    group.run_on_event('custom_1', 'v = v_rest - 0.001 * mV')
    spikegen = SpikeGeneratorGroup(N, [0, 1, 2], [1, 2, 3] * ms,
                                   period=5 * ms)
    po_grp = PoissonGroup(N - 1, rates=rates)
    syn = Synapses(spikegen, group, model='w :volt',
                   on_pre='v = rand() * w + v_th; v = rand() * w',
                   on_post='v = rand() * w + v_rest; v = rand() * w',
                   delay=tau, method='euler')
    group.v[:] = v_rest
    group.v['i%2 == 0'] = 'rand() * v_rest'
    group.v[0:5] = 'v_rest + 10 * mV'
    condition = 'abs(i-j)<=5'
    syn.connect(condition=condition, p=0.999, n=2)
    syn.w = '1 * mV'
    net = Network(group, spikegen, po_grp, syn)
    mon = StateMonitor(syn, 'w', record=True)
    mon2 = SpikeMonitor(po_grp)
    mon3 = EventMonitor(group, 'custom')
    net.add(mon, mon2, mon3)
    net.run(0.01 * ms)
    md_str = device.md_text
    assert _markdown_lint(md_str)
    check = 'randn({sin({$w$}|$v_rest$ - $v$|/{\tau}})})'
    assert _markdown_lint(check)
    # check invalid strings
    with pytest.raises(SyntaxError):
        check = '**Initializing values at starting:*'
        assert _markdown_lint(check)
        check = '- Variable v$ of with $-79. mV$ to all members'
        assert _markdown_lint(check)
        check = 'randn({sin(})})'
        assert _markdown_lint(check)
        check = 'randn({sin({$w$}|$v_rest$ - $v$|/{\tau})})'
        assert _markdown_lint(check)
    device.reinit()


def test_common_example():
    """
    Test COBAHH (brian2.readthedocs.io/en/stable/examples/COBAHH.html)
    """

    set_device('markdown')

    # Parameters
    area = 20000*umetre**2
    Cm = (1*ufarad*cm**-2) * area
    gl = (5e-5*siemens*cm**-2) * area

    El = -60*mV
    EK = -90*mV
    ENa = 50*mV
    g_na = (100*msiemens*cm**-2) * area
    g_kd = (30*msiemens*cm**-2) * area
    VT = -63*mV
    # Time constants
    taue = 5*ms
    taui = 10*ms
    # Reversal potentials
    Ee = 0*mV
    Ei = -80*mV
    we = 6*nS  # excitatory synaptic weight
    wi = 67*nS  # inhibitory synaptic weight

    # The model
    eqs = Equations('''
    dv/dt = (gl*(El-v)+ge*(Ee-v)+gi*(Ei-v)-
            g_na*(m*m*m)*h*(v-ENa)-
            g_kd*(n*n*n*n)*(v-EK))/Cm : volt
    dm/dt = alpha_m*(1-m)-beta_m*m : 1
    dn/dt = alpha_n*(1-n)-beta_n*n : 1
    dh/dt = alpha_h*(1-h)-beta_h*h : 1
    dge/dt = -ge*(1./taue) : siemens
    dgi/dt = -gi*(1./taui) : siemens
    alpha_m = 0.32*(mV**-1)*4*mV/exprel((13.0*mV-v+VT)/(4*mV))/ms : Hz
    beta_m = 0.28*(mV**-1)*5*mV/exprel((v-VT-40*mV)/(5*mV))/ms : Hz
    alpha_h = 0.128*exp((17*mV-v+VT)/(18.0*mV))/ms : Hz
    beta_h = 4./(1+exp((40*mV-v+VT)/(5*mV)))/ms : Hz
    alpha_n = 0.032*(mV**-1)*5*mV/exprel((15.*mV-v+VT)/(5.*mV))/ms : Hz
    beta_n = .5*exp((10*mV-v+VT)/(40.*mV))/ms : Hz
    ''')

    P = NeuronGroup(4000, model=eqs, threshold='v>-20*mV', refractory=3*ms,
                    method='exponential_euler')
    Pe = P[:3200]
    Pi = P[3200:]
    Ce = Synapses(Pe, P, on_pre='ge+=we')
    Ci = Synapses(Pi, P, on_pre='gi+=wi')
    Ce.connect(p=0.02)
    Ci.connect(p=0.02)

    # Initialization
    P.v = 'El + (randn() * 5 - 5)*mV'
    P.ge = '(randn() * 1.5 + 4) * 10.*nS'
    P.gi = '(randn() * 12 + 20) * 10.*nS'

    # Record a few traces
    trace = StateMonitor(P, 'v', record=[1, 10, 100])
    run(1 * second)
    md_str = device.md_text
    assert _markdown_lint(md_str)
    device.reinit()


def test_from_papers_example():
    """
    Test Izhikevich_2007 example
    `brian2.readthedocs.io/en/stable/examples/frompapers.Izhikevich_2007.html`
    """
    set_device('markdown', build_on_run=False)
    # Parameters
    simulation_duration = 6 * second
    # Neurons
    taum = 10*ms
    Ee = 0*mV
    vt = -54*mV
    vr = -60*mV
    El = -74*mV
    taue = 5*ms

    # STDP
    taupre = 20*ms
    taupost = taupre
    gmax = .01
    dApre = .01
    dApost = -dApre * taupre / taupost * 1.05
    dApost *= gmax
    dApre *= gmax

    # Dopamine signaling
    tauc = 1000*ms
    taud = 200*ms
    taus = 1*ms
    epsilon_dopa = 5e-3

    # Setting the stage

    # Stimuli section
    input_indices = array([0, 1, 0, 1, 1, 0,
                           0, 1, 0, 1, 1, 0])
    input_times = array([500,  550, 1000, 1010, 1500, 1510,
                         3500, 3550, 4000, 4010, 4500, 4510])*ms
    input = SpikeGeneratorGroup(2, input_indices, input_times)

    neurons = NeuronGroup(2, '''dv/dt = (ge * (Ee-vr) + El - v) / taum : volt
                                dge/dt = -ge / taue : 1''',
                          threshold='v>vt', reset='v = vr',
                          method='exact')
    neurons.v = vr
    neurons_monitor = SpikeMonitor(neurons)

    synapse = Synapses(input, neurons,
                       model='''s: volt''',
                       on_pre='v += s')
    synapse.connect(i=[0, 1], j=[0, 1])
    synapse.s = 100. * mV

    # STDP section
    synapse_stdp = Synapses(neurons, neurons,
                    model='''mode: 1
                            dc/dt = -c / tauc : 1 (clock-driven)
                            dd/dt = -d / taud : 1 (clock-driven)
                            ds/dt = mode * c * d / taus : 1 (clock-driven)
                            dApre/dt = -Apre / taupre : 1 (event-driven)
                            dApost/dt = -Apost / taupost : 1 (event-driven)''',
                    on_pre='''ge += s
                            Apre += dApre
                            c = clip(c + mode * Apost, -gmax, gmax)
                            s = clip(s + (1-mode) * Apost, -gmax, gmax)
                            ''',
                    on_post='''Apost += dApost
                            c = clip(c + mode * Apre, -gmax, gmax)
                            s = clip(s + (1-mode) * Apre, -gmax, gmax)
                            ''',
                    method='euler'
                           )
    synapse_stdp.connect(i=0, j=1)
    synapse_stdp.mode = 0
    synapse_stdp.s = 1e-10
    synapse_stdp.c = 1e-10
    synapse_stdp.d = 0
    synapse_stdp_monitor = StateMonitor(synapse_stdp, ['s', 'c', 'd'],
                                        record=[0])
    # Dopamine signaling section
    dopamine_indices = array([0, 0, 0])
    dopamine_times = array([3520, 4020, 4520])*ms
    dopamine = SpikeGeneratorGroup(1, dopamine_indices, dopamine_times)
    dopamine_monitor = SpikeMonitor(dopamine)
    reward = Synapses(dopamine, synapse_stdp, model='''''',
                      on_pre='''d_post += epsilon_dopa''',
                      method='exact')
    reward.connect()

    # Simulation
    # Classical STDP
    synapse_stdp.mode = 0
    run(simulation_duration/2)
    # Dopamine modulated STDP
    synapse_stdp.mode = 1
    run(simulation_duration/2)
    device.build()
    md_str = device.md_text
    assert _markdown_lint(md_str)
    device.reinit()


def test_custom_expander():
    """
    Test custom expander class
    """
    class Custom(MdExpander):

        def expand_NeuronGroup(self, grp_dict):
            idt = self.expand_identifiers(grp_dict['identifiers'])
            return "This is my custom neurongroup: " + grp_dict['name'] + idt

        def expand_StateMonitor(self, mon_dict):
            return "I monitor " + mon_dict['source']

        def expand_identifiers(self, identifiers):
            return 'Identifiers are not shown'

    custom_expander = Custom(brian_verbose=True, include_monitors=True,
                             keep_initializer_order=True)
    set_device('markdown', expander=custom_expander)
    # check custom expander
    v_rest = -79 * mV
    rate = 10 * Hz
    grp = NeuronGroup(10, 'v = v_rest:volt')
    mon = StateMonitor(grp, 'v', record=True)
    pog = PoissonGroup(10, rates=rate)
    run(0.1*ms)
    text = device.md_text
    assert _markdown_lint(text)
    # brian_verbose check
    assert 'NeuronGroup' in text
    assert 'StateMonitor' in text
    assert 'Activity recorder' not in text
    assert 'Initializing' in text
    assert 'Identifiers are not shown' in text
    assert 'I monitor ' in text
    assert 'This is my custom neurongroup: neurongroup' in text
    device.reinit()


def test_user_options():
    """
    Test user options and error raising
    """
    link = '<img src="https://render.githubusercontent.com/render/math?math='
    my_expander = MdExpander(github_md=True, author='Brian', add_meta=True)
    set_device('markdown', expander=my_expander)
    grp = NeuronGroup(1, 'w :1')
    run(0*ms)
    string = device.md_text
    regex = '_Filename: .*\
             \nAuthor: .*\
             \nDate and localtime: .*\
             \nBrian version: .*'

    assert re.match(regex, string)
    assert _markdown_lint(string)
    assert '$' not in string
    assert link in string
    device.reinit()

    set_device('markdown', filename=10)
    with pytest.raises(Exception):
        run(0*ms)
    device.reinit()

    set_device('markdown', expander=NeuronGroup)
    with pytest.raises(NotImplementedError):
        run(0*ms)
    device.reinit()


if __name__ == '__main__':

    test_simple_syntax()
    test_common_example()
    test_from_papers_example()
    test_custom_expander()
    test_user_options()
