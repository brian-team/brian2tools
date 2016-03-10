'''
Module to plot simulation data (raster plots, etc.)
'''
import matplotlib.pyplot as plt

from brian2.units.stdunits import ms, Hz
from brian2.units.fundamentalunits import Quantity

# Only import the module to avoid circular import issues
import base


def plot_raster(spike_times, spike_indices, time_unit=ms,
                axes=None, newfigure=False, showplot=True, **kwds):
    '''
    Plot a "raster plot", a plot of neuron indices over spike times. The default
    marker used for plotting is `'.'`, it can be overriden with the `marker`
    keyword argument.

    Parameters
    ----------
    spike_times : `Quantity`
        A sequence of spike times.
    spike_indices : `ndarray`
        The indices of spiking neurons, corresponding to the times given in
        ``spike_times``.
    time_unit : `Unit`, optional
        The unit to use for the time axis. Defaults to ``ms``, but longer
        simulations could use ``second``, for example.
    axes : `~matplotlib.axes.Axes`, optional
        The `~matplotlib.axes.Axes` instance used for plotting. Defaults to
        ``None`` which means that a new `~matplotlib.axes.Axes` will be
        created for the plot. Note that this will override previous plots,
        if a new figure should be created, set ``newfigure`` to ``True``.
    newfigure : bool, optional
        Whether to create a new `~matplotlib.figure.Figure` for this plot.
        Defaults to ``False`.
    showplot : bool, optional
        Display the figure using matplotlib's `~matplotlib.pyplot.show`
        command. Defaults to ``True``. Set it to ``False`` if you create
        several figures and want to have them displayed at once. This setting
        is not relevant for interactive plotting environments such as
        jupyter notebooks.
    kwds : dict, optional
        Any additional keywords command will be handed over to matplotlib's
        `~matplotlib.axes.Axes.plot` command. This can be used to set plot
        properties such as the ``color``.

    Returns
    -------
    axes : `~matplotlib.axes.Axes`
        The `~matplotlib.axes.Axes` instance that was used for plotting. This
        object allows to modify the plot further (if ``showplot`` was not set),
        e.g. by setting the plotted range, the axis labels, the plot title,
        etc.
    '''
    axes = base._setup_axes_matplotlib(axes, newfigure)
    axes.plot(spike_times/time_unit, spike_indices, '.', **kwds)
    axes.set_xlabel('time (%s)' % time_unit)
    axes.set_ylabel('neuron index')
    if showplot:
        plt.show()
    return axes


def plot_state(times, values, time_unit=ms, var_unit=None, var_name=None,
               axes=None, newfigure=False, showplot=True, **kwds):
    '''

    Parameters
    ----------
    times : `Quantity`
        The array of times for the data points given in ``values``.
    values : `Quantity`, `ndarray`
        The values to plot, either a 1D array with the same length as ``times``,
        or a 2D array with ``len(times)`` rows.
    time_unit : `Unit`, optional
        The unit to use for the time axis. Defaults to ``ms``, but longer
        simulations could use ``second``, for example.
    var_unit : `Unit`, optional
        The unit to use to plot the ``values`` (e.g. ``mV`` for a membrane
        potential). If none is given (the default), an attempt is made to
        find a good scale automatically based on the ``values``.
    var_name : str, optional
        The name of the variable that is plotted. Used for the axis label.
    axes : `~matplotlib.axes.Axes`, optional
        The `~matplotlib.axes.Axes` instance used for plotting. Defaults to
        ``None`` which means that a new `~matplotlib.axes.Axes` will be
        created for the plot. Note that this will override previous plots,
        if a new figure should be created, set ``newfigure`` to ``True``.
    newfigure : bool, optional
        Whether to create a new `~matplotlib.figure.Figure` for this plot.
        Defaults to ``False`.
    showplot : bool, optional
        Display the figure using matplotlib's `~matplotlib.pyplot.show`
        command. Defaults to ``True``. Set it to ``False`` if you create
        several figures and want to have them displayed at once. This setting
        is not relevant for interactive plotting environments such as
        jupyter notebooks.
    kwds : dict, optional
        Any additional keywords command will be handed over to matplotlib's
        `~matplotlib.axes.Axes.plot` command. This can be used to set plot
        properties such as the ``color``.

    Returns
    -------
    axes : `~matplotlib.axes.Axes`
        The `~matplotlib.axes.Axes` instance that was used for plotting. This
        object allows to modify the plot further (if ``showplot`` was not set),
        e.g. by setting the plotted range, the axis labels, the plot title,
        etc.
    '''
    axes = base._setup_axes_matplotlib(axes, newfigure)
    if var_unit is None:
        if isinstance(values, Quantity):
            var_unit = values._get_best_unit()
    if var_unit is not None:
        values /= var_unit
    axes.plot(times / time_unit, values, **kwds)
    axes.set_xlabel('time (%s)' % time_unit)
    if var_unit is not None:
        axes.set_ylabel('%s (%s)' % (var_name, var_unit))
    else:
        axes.set_ylabel('%s' % var_name)
    if showplot:
        plt.show()
    return axes


def plot_rate(times, rate, time_unit=ms, rate_unit=Hz,
              axes=None, newfigure=False, showplot=True, **kwds):
    '''

    Parameters
    ----------
    times : `Quantity`
        The time points at which the ``rate`` is measured.
    rate : `Quantity`
        The population rate for each time point in ``times``
    time_unit : `Unit`, optional
        The unit to use for the time axis. Defaults to ``ms``, but longer
        simulations could use ``second``, for example.
    time_unit : `Unit`, optional
        The unit to use for the rate axis. Defaults to ``Hz``.
    axes : `~matplotlib.axes.Axes`, optional
        The `~matplotlib.axes.Axes` instance used for plotting. Defaults to
        ``None`` which means that a new `~matplotlib.axes.Axes` will be
        created for the plot. Note that this will override previous plots,
        if a new figure should be created, set ``newfigure`` to ``True``.
    newfigure : bool, optional
        Whether to create a new `~matplotlib.figure.Figure` for this plot.
        Defaults to ``False`.
    showplot : bool, optional
        Display the figure using matplotlib's `~matplotlib.pyplot.show`
        command. Defaults to ``True``. Set it to ``False`` if you create
        several figures and want to have them displayed at once. This setting
        is not relevant for interactive plotting environments such as
        jupyter notebooks.
    kwds : dict, optional
        Any additional keywords command will be handed over to matplotlib's
        `~matplotlib.axes.Axes.plot` command. This can be used to set plot
        properties such as the ``color``.

    Returns
    -------
    axes : `~matplotlib.axes.Axes`
        The `~matplotlib.axes.Axes` instance that was used for plotting. This
        object allows to modify the plot further (if ``showplot`` was not set),
        e.g. by setting the plotted range, the axis labels, the plot title,
        etc.
    '''
    axes = base._setup_axes_matplotlib(axes, newfigure)
    axes.plot(times/time_unit, rate/rate_unit, **kwds)
    axes.set_xlabel('time (%s)' % time_unit)
    axes.set_ylabel('population rate (%s)' % rate_unit)
    if showplot:
        plt.show()
    return axes
