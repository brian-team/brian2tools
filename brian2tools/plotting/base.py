'''
Base module for the plotting facilities.
'''
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from brian2.core.variables import VariableView
from brian2.spatialneuron.morphology import Morphology
from brian2.monitors import SpikeMonitor, StateMonitor, PopulationRateMonitor
from brian2.monitors.statemonitor import StateMonitorView
from brian2.units.fundamentalunits import Quantity
from brian2.units.stdunits import ms
from brian2.utils.logger import get_logger
from brian2.synapses.synapses import Synapses, SynapticPathway

from .data import plot_raster, plot_state, plot_rate, _get_best_unit
from .morphology import plot_dendrogram
from .synapses import plot_synapses

__all__ = ['brian_plot', 'add_background_pattern']

logger = get_logger(__name__)


def _resolve_var_kwds(kwds, var_name, values):
    '''
    Build a per-variable keyword dict, resolving ``var_name`` and ``var_unit``
    that may be plain values (applied to every variable) or dicts keyed by
    variable name.
    '''
    kwds_var = {k: v for k, v in kwds.items()
                if k not in ('var_name', 'var_unit')}

    vn = kwds.get('var_name')
    if isinstance(vn, dict):
        kwds_var['var_name'] = vn.get(var_name, var_name)
    elif vn is not None:
        kwds_var['var_name'] = vn
    else:
        kwds_var['var_name'] = var_name

    vu = kwds.get('var_unit')
    if isinstance(vu, dict):
        unit = vu.get(var_name)
        if unit is not None:
            kwds_var['var_unit'] = unit
        elif isinstance(values, Quantity):
            kwds_var['var_unit'] = _get_best_unit(values)
    elif vu is not None:
        kwds_var['var_unit'] = vu
    elif isinstance(values, Quantity):
        kwds_var['var_unit'] = _get_best_unit(values)

    return kwds_var


def _plot_state_variables(brian_obj, record_variables, axes, **kwds):
    '''
    Plot one or more recorded state variables.  When more than one variable
    is present a column of subplots sharing the time axis is created
    automatically (unless the caller supplies a matching array of axes).
    '''
    n_vars = len(record_variables)

    if n_vars == 1:
        var_name = record_variables[0]
        values = getattr(brian_obj, var_name).T
        kwds_var = _resolve_var_kwds(kwds, var_name, values)
        return plot_state(brian_obj.t, values, axes=axes, **kwds_var)

    if axes is None:
        fig, axes_arr = plt.subplots(n_vars, 1, sharex=True)
    else:
        axes_arr = np.asarray(axes).ravel()
        if len(axes_arr) != n_vars:
            raise TypeError(
                f"If multiple variables are recorded, 'axes' must be an "
                f"array-like of Axes with length {n_vars} (got {len(axes_arr)})."
            )

    ret_axes = []
    for ax, var_name in zip(axes_arr, record_variables):
        values = getattr(brian_obj, var_name).T
        kwds_var = _resolve_var_kwds(kwds, var_name, values)
        ret_axes.append(
            plot_state(brian_obj.t, values, axes=ax, **kwds_var))
    return ret_axes


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

    When a `~brian2.monitors.statemonitor.StateMonitor` that records several
    variables is given, a column of subplots sharing the time axis is created
    automatically.

    Parameters
    ----------
    brian_obj : object
        The Brian object to plot.
    axes : `~matplotlib.axes.Axes` or array-like of Axes, optional
        The `~matplotlib.axes.Axes` instance used for plotting. Defaults to
        ``None`` which means that a new `~matplotlib.axes.Axes` will be
        created for the plot. For a multi-variable
        `~brian2.monitors.statemonitor.StateMonitor`, pass an array-like of
        `~matplotlib.axes.Axes` with one entry per recorded variable.
    kwds : dict, optional
        Any additional keywords command will be handed over to matplotlib's
        `~matplotlib.axes.Axes.plot` command. This can be used to set plot
        properties such as the ``color``.

        For multi-variable `~brian2.monitors.statemonitor.StateMonitor`
        objects, ``var_name`` and ``var_unit`` may be dictionaries keyed by
        variable name, e.g.
        ``var_name={'v': 'membrane potential', 'I': 'input current'}``.

    Returns
    -------
    axes : `~matplotlib.axes.Axes` or list of `~matplotlib.axes.Axes`
        The `~matplotlib.axes.Axes` instance(s) used for plotting. A list is
        returned when multiple state variables are plotted.
    '''
    if isinstance(brian_obj, SpikeMonitor):
        return plot_raster(brian_obj.i, brian_obj.t, axes=axes, **kwds)
    elif isinstance(brian_obj, StateMonitor):
        return _plot_state_variables(brian_obj,
                                     brian_obj.record_variables,
                                     axes, **kwds)
    elif isinstance(brian_obj, StateMonitorView):
        return _plot_state_variables(brian_obj,
                                     brian_obj.monitor.record_variables,
                                     axes, **kwds)
    elif isinstance(brian_obj, PopulationRateMonitor):
        smooth_rate = brian_obj.smooth_rate(width=1*ms)
        if 'rate_unit' not in kwds:
            kwds['rate_unit'] = _get_best_unit(smooth_rate)
        return plot_rate(brian_obj.t, smooth_rate, axes=axes, **kwds)
    elif isinstance(brian_obj, Morphology):
        return plot_dendrogram(brian_obj, axes=axes, **kwds)
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
        return plot_synapses(brian_obj.i, brian_obj.j, plot_type=plot_type,
                             axes=axes)
    # brian_obj.group can be a weak proxy, we can therefore not use isinstance
    elif (isinstance(brian_obj, VariableView) and
          issubclass(brian_obj.group.__class__, (Synapses, SynapticPathway))):
        # synaptic variable
        synapses = brian_obj.group
        sources = synapses.i[:]
        targets = synapses.j[:]
        min_sources, max_sources = np.min(sources), np.max(sources)
        min_targets, max_targets = np.min(targets), np.max(targets)
        source_range = max_sources - min_sources
        target_range = max_targets - min_targets
        if source_range < 1000 and target_range < 1000:
            plot_type = 'image'
        elif len(brian_obj) < 10000:
            plot_type = 'scatter'
        else:
            plot_type = 'hexbin'
        values = brian_obj[:]
        if 'var_name' not in kwds:
            kwds['var_name'] = brian_obj.name
        if 'var_unit' not in kwds and isinstance(values, Quantity):
            kwds['var_unit'] = _get_best_unit(values)
        return plot_synapses(sources, targets, values, plot_type=plot_type,
                             axes=axes, **kwds)
    else:
        raise NotImplementedError('Do not know how to plot object of type '
                                  '%s' % type(brian_obj))


def add_background_pattern(axes, hatch='xxx', fill=True, fc=(0.9, 0.9, 0.9),
                           ec=(0.8, 0.8, 0.8), zorder=-10, **kwds):
    '''
    Add a "hatching" pattern to the background of the axes (can be useful to
    make a difference between "no value" and a value mapped to a color value
    that is identical to the background color). By default, it uses a cross
    hatching pattern in gray which can be changed by providing the respective
    arguments. All additional keyword arguments are passed on to the
    `~matplotlib.patches.Rectangle` initializer.

    Parameters
    ----------
    axes : `matplotlib.axes.Axes`
        The axes where the background pattern should be added.
    hatch : str, optional
        See `matplotlib.patches.Patch.set_hatch`. Defaults to `'xxx'`.
    fill : bool, optional
        See `matplotlib.patches.Patch.set_fill`. Defaults to `True`.
    fc : mpl color spec or None or 'none'
        See `matplotlib.patches.Patch.set_facecolor`. Defaults to
        `(0.9, 0.9, 0.9)`.
    ec : mpl color spec or None or 'none'
        See `matplotlib.patches.Patch.set_edgecolor`. Defaults to
        `(0.8, 0.8, 0.8)`.
    zorder : int
        See `matplotlib.artist.Artist.set_zorder`. Defaults to `-10`.
    '''
    xmin, xmax = axes.get_xlim()
    ymin, ymax = axes.get_ylim()
    xy = (xmin, ymin)
    width = xmax - xmin
    height = ymax - ymin
    p = patches.Rectangle(xy, width, height, hatch=hatch, fill=fill, fc=fc,
                          ec=ec, zorder=zorder, **kwds)
    axes.add_patch(p)
