from brian2.monitors import SpikeMonitor, StateMonitor, PopulationRateMonitor
from brian2.units.fundamentalunits import Quantity
from brian2.units.stdunits import ms

from .data import plot_raster, plot_state, plot_rate


def brian_plot(brian_obj,
               axes=None, newfigure=False, showplot=True, **kwds):
    '''
    Plot the data of the given object (e.g. a monitor). This function will
    call an adequate plotting function for the object, e.g. `plot_raster` for
    a `SpikeMonitor`. The plotting may apply heuristics to get a generally
    useful plot (e.g. for a `PopulationRateMonitor`, it will plot the rates
    smoothed with a Gaussian window of 1 ms), the exact details are subject to
    change. This function is therefore mostly meant as a quick and easy way to
    plot an object, for full control use one of the specific plotting functions.

    Parameters
    ----------
    brian_obj
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
    if isinstance(brian_obj, SpikeMonitor):
        return plot_raster(brian_obj.t, brian_obj.i,
                    axes=axes, newfigure=newfigure, showplot=showplot, **kwds)
    elif isinstance(brian_obj, StateMonitor):
        if len(brian_obj.record_variables) != 1:
            raise TypeError('brian_plot only works for a StateMonitor that '
                            'records a single variable.')
        values = getattr(brian_obj, brian_obj.record_variables[0]).T
        if 'var_name' not in kwds:
            kwds['var_name'] = brian_obj.record_variables[0]
        if 'var_unit' not in kwds and isinstance(values, Quantity):
            kwds['var_unit'] = values._get_best_unit()
        return plot_state(brian_obj.t, values,
                   axes=axes, newfigure=newfigure, showplot=showplot, **kwds)
    elif isinstance(brian_obj, PopulationRateMonitor):
        smooth_rate = brian_obj.smooth_rate(width=1*ms)
        if 'rate_unit' not in kwds:
            kwds['rate_unit'] = smooth_rate._get_best_unit()
        return plot_rate(brian_obj.t, smooth_rate,
                  axes=axes, newfigure=newfigure, showplot=showplot, **kwds)
    else:
        raise NotImplementedError('Do not know how to plot object of type '
                                  '%s' % type(brian_obj))
