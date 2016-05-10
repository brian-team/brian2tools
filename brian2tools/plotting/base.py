'''
Base module for the plotting facilities.
'''
import matplotlib.pyplot as plt
import numpy as np

from brian2.spatialneuron.morphology import Morphology
from brian2.monitors import SpikeMonitor, StateMonitor, PopulationRateMonitor
from brian2.units.fundamentalunits import Quantity
from brian2.units.stdunits import ms
from brian2.utils.logger import get_logger
from brian2.synapses.synapses import Synapses

from .data import plot_raster, plot_state, plot_rate
from .morphology import plot_dendrogram
from .synapses import plot_synapses

__all__ = ['brian_plot']

logger = get_logger(__name__)


def _setup_axes_matplotlib(axes):
    '''
    Helper function to create new figures/axes for matplotlib, depending on
    arguments provided by the user.
    '''
    if axes is None:
        axes = plt.gca()
    return axes


def _setup_axes_mayavi(axes):
    '''
    Helper function to create new figures/axes for mayavi, depending on
    arguments provided by the user.
    '''
    import mayavi.mlab as mayavi
    if axes is None:
        axes = mayavi.figure(bgcolor=(0.95, 0.95, 0.95))
    return axes


def brian_plot(brian_obj,
               axes=None, **kwds):
    '''
    Plot the data of the given object (e.g. a monitor). This function will
    call an adequate plotting function for the object, e.g. `plot_raster` for
    a `~brian2.monitors.spikemonitor.SpikeMonitor`. The plotting may apply
    heuristics to get a generally useful plot (e.g. for a
    `~brian2.monitors.ratemonitor.PopulationRateMonitor`, it will plot the rates
    smoothed with a Gaussian window of 1 ms), the exact details are subject to
    change. This function is therefore mostly meant as a quick and easy way to
    plot an object, for full control use one of the specific plotting functions.

    Parameters
    ----------
    brian_obj : object
        The Brian object to plot.
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
    if isinstance(brian_obj, SpikeMonitor):
        return plot_raster(brian_obj.i, brian_obj.t, axes=axes, **kwds)
    elif isinstance(brian_obj, StateMonitor):
        if len(brian_obj.record_variables) != 1:
            raise TypeError('brian_plot only works for a StateMonitor that '
                            'records a single variable.')
        values = getattr(brian_obj, brian_obj.record_variables[0]).T
        if 'var_name' not in kwds:
            kwds['var_name'] = brian_obj.record_variables[0]
        if 'var_unit' not in kwds and isinstance(values, Quantity):
            kwds['var_unit'] = values._get_best_unit()
        return plot_state(brian_obj.t, values, axes=axes, **kwds)
    elif isinstance(brian_obj, PopulationRateMonitor):
        smooth_rate = brian_obj.smooth_rate(width=1*ms)
        if 'rate_unit' not in kwds:
            kwds['rate_unit'] = smooth_rate._get_best_unit()
        return plot_rate(brian_obj.t, smooth_rate, axes=axes, **kwds)
    elif isinstance(brian_obj, Morphology):
        if kwds:
            logger.warn('plot_dendrogram does not take any additional keyword '
                        'arguments, ignoring them.')
        plot_dendrogram(brian_obj, axes=axes)
    elif isinstance(brian_obj, Synapses):
        if len(brian_obj) == 0:
            raise TypeError('Synapses object does not have any synapses.')
        min_sources, max_sources = np.min(brian_obj.i[:]), np.max(brian_obj.i[:])
        min_targets, max_targets = np.min(brian_obj.j[:]), np.max(brian_obj.j[:])
        source_range = max_sources - min_sources
        target_range = max_targets - min_targets
        if source_range < 1000 and target_range < 1000:
            plot_type = 'image'
        elif len(brian_obj) < 10000:
            plot_type = 'scatter'
        else:
            plot_type = 'hexbin'
        plot_synapses(brian_obj.i, brian_obj.j, plot_type=plot_type, axes=axes)
    else:
        raise NotImplementedError('Do not know how to plot object of type '
                                  '%s' % type(brian_obj))
