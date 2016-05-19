'''
Main module for model fitting

TODO:
* Deal with variable duration traces
* User-defined error
(* Maybe no need to define parameters in equations)
* Callback to stop after a given time
* Split over multiple cores
* Symbolic gradient calculation
* Extend to IF models (threshold, reset etc)
'''

from brian2.equations import Equations
from brian2.input import TimedArray
from brian2 import NeuronGroup, StateMonitor, store, restore, run, defaultclock, second
from .differential_evolution import differential_evolution
from numpy import mean, ones, array

__all__=['fit_traces']

def fit_traces(model = None,
               input_var = None,
               input = None,
               output_var = None,
               output = None,
               dt = None, tol = 1e-9,
               maxiter = None,
               popsize = 15,
               method = ('linear', 'exponential_euler', 'euler'),
               t_start = 0*second,
               **params):
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

    maxiter : int, optional
        Maximum number of iterations.

    popsize : int, optional
        Number of population samples per parameter.

    method: string, optional
        Integration method

    t_start: starting time of error measurement.

    Returns
    -------
    A dictionary of parameter values, fits as a 2D array, and error (RMS).

    '''

    parameter_names = model.parameter_names

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
    defaultclock.dt = dt

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
    model = model + Equations(input_var + '= input_var(t,i % Ntraces) : '+ "% s" % repr(input_unit))

    # Add criterion with TimedArray
    output_traces = TimedArray(output, dt = dt)
    error_unit = output.dim**2
    model = model + Equations('total_error : %s' % repr(error_unit))

    # Population size for differential evolution
    # (actually in scipy's algorithm this is popsize * nb params)
    N = popsize * len(parameter_names)

    neurons = NeuronGroup(Ntraces*N, model, method = method)
    neurons.namespace['input_var'] = input_traces
    neurons.namespace['output_var'] = output_traces
    neurons.namespace['t_start'] = t_start

    # Record error
    neurons.run_regularly('total_error +=  (' + output_var + '-output_var(t,i % Ntraces))**2 * (t>=t_start)')

    # Store for reinitialization
    store()

    # Vectorized error function
    def error_function(params):
        # Set parameter values, duplicated over traces
        # params is a list of vectors (vector = value for population)
        d = dict()
        for name, value in zip(parameter_names, params.T):
            d[name] = (value * ones((Ntraces,N))).T.flatten()

        # Run the model
        restore()
        neurons.set_states(d, units = False)
        run(duration)

        e = neurons.total_error/int((duration-t_start)/defaultclock.dt)
        e = mean(e.reshape((N,Ntraces)),axis=1)
        return array(e)

    # Set parameter bounds
    bounds = []
    for name in parameter_names:
        bounds.append(params[name])

    res = differential_evolution(error_function,bounds, tol = tol, maxiter = maxiter, popsize = popsize)
    d = dict()
    for name, value in zip(parameter_names, res.x):
        d[name] = value

    # Run once with the optimized parameters to get model outputs
    restore()
    M_out = StateMonitor(neurons, output_var, record = range(Ntraces))
    neurons.set_states(d, units = False)
    run(duration)
    fits = M_out.get_states()[output_var]

    error = (res.fun)**.5 * model.units[output_var]

    return d, fits, error
