'''
Test the modelfitting module
'''
from brian2 import *
from brian2tools import *

def test_import():
    fit_traces

def test_fit_traces():
    # Create voltage traces for an activation experiment
    input_traces = zeros((10,5))*volt
    for i in range(5):
        input_traces[5:,i]=i*10*mV
    # Create target current traces
    output_traces = 10*nS*input_traces

    model = Equations('''
    I = g*(v-E) : amp
    g : siemens (constant)
    E : volt (constant)
    ''')
    params, fits, error = fit_traces(model = model, input_var = 'v', output_var = 'I',\
        input = input_traces, output = output_traces,
        dt = 0.1*ms, g = [1*nS, 30*nS], E = [-20*mV,100*mV],
        tol = 1e-6)

if __name__ == '__main__':
    test_import()
    test_fit_traces()
