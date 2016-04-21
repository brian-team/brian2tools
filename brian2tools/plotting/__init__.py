"""
Package containing plotting modules.
"""
# It is a bit annoying, but otherwise `from brian2tools import *` will import
# names such as `synapses`.
from .base import brian_plot
from .data import plot_raster, plot_state, plot_rate
from .morphology import plot_morphology, plot_dendrogram
from .synapses import plot_synapses

__all__ = ['brian_plot', 'plot_raster', 'plot_state', 'plot_rate',
           'plot_morphology', 'plot_dendrogram', 'plot_synapses']
