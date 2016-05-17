'''
Main module for model fitting

TODO:
* Initialization of state variables
* Vectorization of differential evolution
* Error calculation without monitoring
* Deal with variable duration traces
* User-defined error
* Maybe no need to define parameters in equations
* Callback to stop after a given time
* Split over multiple cores
* Symbolic gradient calculation
* Extend to IF models (threshold, reset etc)
'''

from brian2.equations import Equations
from brian2.input import TimedArray
from brian2 import NeuronGroup, StateMonitor, store, restore, run
from scipy.optimize import differential_evolution
from numpy import mean

__all__=['fit_traces']

def fit_traces(model = None,
               input_var = None,
               input = None,
               output_var = None,
               output = None,
               dt = None, tol = 1e-9, **params):
    '''
    Fits a model to a set of traces.

    Parameters
    ----------
    model : `~brian2.equations.Equations` or string
        The equations describing the model.

    input_var : string
        Input variable name.

    output_var : string
        Output variable name.

    input : input data as a 2D array

    output : output data as a 2D array

    dt : time step

    tol : float, optional
        Stop criterion of the differential evolution algorithm.

    Returns
    -------
    A dictionary of parameter values.

    '''

    # Check parameter names
    for param in params.keys():
        if (param not in model.parameter_names):
            raise Exception("Parameter %s must be defined as a parameter in the model" % param)
    for param in model.parameter_names:
        if (param not in params):
            raise Exception("Bounds must be set for parameter %s" % param)

    # dt must be set
    if dt is None:
        raise Exception('dt (sampling frequency of the input) must be set')

    # Check input variable
    if input_var not in model.identifiers:
        raise Exception("%s is not an identifier in the model" % input_var)
    Nsteps, Ntraces = input.shape
    duration = Nsteps*dt

    # Check output variable
    if output_var not in model.names:
        raise Exception("%s is not a model variable" % output_var)
    if output.shape!=input.shape:
        raise Exception("Input and output must have the same size")

    # Replace input variable by TimedArray
    input_traces = TimedArray(input, dt = dt)
    input_unit = input.dim
    model = model + Equations(input_var + "= input_var(t,i) : % s" % repr(input_unit))

    # Add criterion with TimedArray
    output_traces = TimedArray(output, dt = dt)
    error_unit = output.dim**2
    model = model + Equations('error = (' + output_var + '-output_var(t,i))**2 : %s' % repr(error_unit))

    neurons = NeuronGroup(Ntraces, model)
    neurons.namespace['input_var'] = input_traces
    neurons.namespace['output_var'] = output_traces
    M = StateMonitor(neurons, 'error', record = True)
    store()

    # Error function
    def error_function(params):
        # Set parameter values with units
        d = dict()
        for name, value in zip(model.parameter_names, params):
            d[name] = value * model.units[name]

        # Run the model
        restore()
        neurons.set_states(d)
        run(duration)
        e = mean(M.error)
        return float(e)

    # Set parameter bounds
    bounds = []
    for name in model.parameter_names:
        bounds.append(params[name])

    res = differential_evolution(error_function,bounds, tol = tol)
    d = dict()
    for name, value in zip(model.parameter_names, res.x):
        d[name] = value * model.units[name]

    return d
