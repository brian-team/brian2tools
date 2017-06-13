'''
Module to plot simulation data (raster plots, etc.)
'''
import matplotlib.pyplot as plt

from brian2.units.stdunits import ms, Hz
from brian2.units.fundamentalunits import Quantity

__all__ = ['plot_raster', 'plot_state', 'plot_rate']


def _get_best_unit(value):
    '''
    Helper function to work with older Brian 2 versions and avoid deprecation
    warnings on newer versions.
    '''
    try:
        return value.get_best_unit()
    except AttributeError:
        return value._get_best_unit()


def plot_raster(spike_indices, spike_times, time_unit=ms,
                axes=None, **kwds):
    '''
    Plot a "raster plot", a plot of neuron indices over spike times. The default
    marker used for plotting is ``'.'``, it can be overriden with the ``marker``
    keyword argument.

    Parameters
    ----------
    spike_indices : `~numpy.ndarray`
        The indices of spiking neurons, corresponding to the times given in
        ``spike_times``.
    spike_times : `~brian2.units.fundamentalunits.Quantity`
        A sequence of spike times.
    time_unit : `~brian2.units.fundamentalunits.Unit`, optional
        The unit to use for the time axis. Defaults to ``ms``, but longer
        simulations could use ``second``, for example.
    axes : `~matplotlib.axes.Axes`, optional
        The `~matplotlib.axes.Axes` instance used for plotting. Defaults to
        ``None`` which means that a new `~matplotlib.axes.Axes` will be
        created for the plot.
    kwds : dict, optional
        Any additional keywords command will be handed over to matplotlib's
        `~matplotlib.axes.Axes.plot` command. This can be used to set plot
        properties such as the ``color``.

    Returns
    -------
    axes : `~matplotlib.axes.Axes`
        The `~matplotlib.axes.Axes` instance that was used for plotting. This
        object allows to modify the plot further, e.g. by setting the plotted
        range, the axis labels, the plot title, etc.
    '''
    # Avoid circular import issues
    from brian2tools.plotting.base import _setup_axes_matplotlib
    axes = _setup_axes_matplotlib(axes)
    axes.plot(spike_times/time_unit, spike_indices, '.', **kwds)
    axes.set_xlabel('time (%s)' % time_unit)
    axes.set_ylabel('neuron index')
    return axes


def plot_state(times, values, time_unit=ms, var_unit=None, var_name=None,
               axes=None, **kwds):
    '''

    Parameters
    ----------
    times : `~brian2.units.fundamentalunits.Quantity`
        The array of times for the data points given in ``values``.
    values : `~brian2.units.fundamentalunits.Quantity`, `~numpy.ndarray`
        The values to plot, either a 1D array with the same length as ``times``,
        or a 2D array with ``len(times)`` rows.
    time_unit : `~brian2.units.fundamentalunits.Unit`, optional
        The unit to use for the time axis. Defaults to ``ms``, but longer
        simulations could use ``second``, for example.
    var_unit : `~brian2.units.fundamentalunits.Unit`, optional
        The unit to use to plot the ``values`` (e.g. ``mV`` for a membrane
        potential). If none is given (the default), an attempt is made to
        find a good scale automatically based on the ``values``.
    var_name : str, optional
        The name of the variable that is plotted. Used for the axis label.
    axes : `~matplotlib.axes.Axes`, optional
        The `~matplotlib.axes.Axes` instance used for plotting. Defaults to
        ``None`` which means that a new `~matplotlib.axes.Axes` will be
        created for the plot.
    kwds : dict, optional
        Any additional keywords command will be handed over to matplotlib's
        `~matplotlib.axes.Axes.plot` command. This can be used to set plot
        properties such as the ``color``.

    Returns
    -------
    axes : `~matplotlib.axes.Axes`
        The `~matplotlib.axes.Axes` instance that was used for plotting. This
        object allows to modify the plot further, e.g. by setting the plotted
        range, the axis labels, the plot title, etc.
    '''
    # Avoid circular import issues
    from brian2tools.plotting.base import _setup_axes_matplotlib
    axes = _setup_axes_matplotlib(axes)
    if var_unit is None:
        if isinstance(values, Quantity):
            var_unit = _get_best_unit(values)
    if var_unit is not None:
        values /= var_unit
    axes.plot(times / time_unit, values, **kwds)
    axes.set_xlabel('time (%s)' % time_unit)
    if var_unit is not None:
        axes.set_ylabel('%s (%s)' % (var_name, var_unit))
    else:
        axes.set_ylabel('%s' % var_name)
    return axes


def plot_rate(times, rate, time_unit=ms, rate_unit=Hz, axes=None, **kwds):
    '''

    Parameters
    ----------
    times : `~brian2.units.fundamentalunits.Quantity`
        The time points at which the ``rate`` is measured.
    rate : `~brian2.units.fundamentalunits.Quantity`
        The population rate for each time point in ``times``
    time_unit : `~brian2.units.fundamentalunits.Unit`, optional
        The unit to use for the time axis. Defaults to ``ms``, but longer
        simulations could use ``second``, for example.
    time_unit : `~brian2.units.fundamentalunits.Unit`, optional
        The unit to use for the rate axis. Defaults to ``Hz``.
    axes : `~matplotlib.axes.Axes`, optional
        The `~matplotlib.axes.Axes` instance used for plotting. Defaults to
        ``None`` which means that a new `~matplotlib.axes.Axes` will be
        created for the plot.
    kwds : dict, optional
        Any additional keywords command will be handed over to matplotlib's
        `~matplotlib.axes.Axes.plot` command. This can be used to set plot
        properties such as the ``color``.

    Returns
    -------
    axes : `~matplotlib.axes.Axes`
        The `~matplotlib.axes.Axes` instance that was used for plotting. This
        object allows to modify the plot further, e.g. by setting the plotted
        range, the axis labels, the plot title, etc.
    '''
    # Avoid circular import issues
    from brian2tools.plotting.base import _setup_axes_matplotlib
    axes = _setup_axes_matplotlib(axes)
    axes.plot(times/time_unit, rate/rate_unit, **kwds)
    axes.set_xlabel('time (%s)' % time_unit)
    axes.set_ylabel('population rate (%s)' % rate_unit)
    return axes
