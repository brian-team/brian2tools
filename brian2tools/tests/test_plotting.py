'''
Test the brian2tools package
'''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pytest

# We avoid "from brian2 import *", as this would also import Brian's test
# function which will then be collected by py.test
from brian2 import (NeuronGroup, SpikeMonitor, PopulationRateMonitor,
                    StateMonitor, Synapses, run, set_device, SpatialNeuron, DimensionMismatchError, meter)
from brian2 import Cylinder, Soma, Section
from brian2 import ms, mV, um

# Same here for brian2tools -- we don't want to import brian2tools.test()
from brian2tools import (brian_plot, plot_synapses, plot_raster, plot_state,
                         plot_rate, add_background_pattern, plot_dendrogram,
                         plot_morphology)

def test_plot_monitors():
    set_device('runtime')
    group = NeuronGroup(10, 'dv/dt = -v/(10*ms) : volt', threshold='False',
                        reset='', method='linear')
    group.v = np.linspace(0, 1, 10)*mV
    spike_mon = SpikeMonitor(group)
    rate_mon = PopulationRateMonitor(group)
    state_mon = StateMonitor(group, 'v', record=[3, 5])
    run(10*ms)

    # Just checking whether the plotting does not fail with an error and that
    # it retuns an Axis object as promised
    ax = brian_plot(spike_mon)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_raster(spike_mon.i, spike_mon.t)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = brian_plot(rate_mon)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_rate(rate_mon.t, rate_mon.rate)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = brian_plot(state_mon)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_state(state_mon.t, state_mon.v.T)
    assert isinstance(ax, matplotlib.axes.Axes)


def test_plot_synapses():
    set_device('runtime')
    group = NeuronGroup(10, 'dv/dt = -v/(10*ms) : volt', threshold='False',
                        reset='')
    group.v = np.linspace(0, 1, 10)*mV
    synapses = Synapses(group, group, 'w : volt', on_pre='v += w')
    synapses.connect('i != j')
    synapses.w = 'i*0.1*mV'
    # Just checking whether the plotting does not fail with an error and that
    # it retuns an Axis object as promised
    ax = brian_plot(synapses)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = brian_plot(synapses.w)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = brian_plot(synapses.delay)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_synapses(synapses.i, synapses.j)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_synapses(synapses.i, synapses.j, plot_type='scatter')
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_synapses(synapses.i, synapses.j, plot_type='image')
    add_background_pattern(ax)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_synapses(synapses.i, synapses.j, plot_type='hexbin')
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_synapses(synapses.i, synapses.j, synapses.w)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_synapses(synapses.i, synapses.j, synapses.w, plot_type='scatter')
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_synapses(synapses.i, synapses.j, synapses.w, plot_type='image')
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_synapses(synapses.i, synapses.j, synapses.w, plot_type='hexbin')
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()

    synapses.connect('i > 5')  # More than one synapse per connection
    brian_plot(synapses)
    plt.close()
    # It should be possible to plot synaptic variables for multiple connections
    # with hexbin
    ax = plot_synapses(synapses.i, synapses.j, synapses.w, plot_type='hexbin')
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()


def test_plot_morphology():
    set_device('runtime')
    # Only testing 2D plotting for now
    morpho = Soma(diameter=30*um)
    morpho.axon = Cylinder(diameter=10*um, n=10, length=100*um)
    morpho.dend = Section(diameter=np.linspace(10, 1, 11)*um, n=10,
                          length=np.ones(10)*5*um)
    morpho = morpho.generate_coordinates()

    # Just checking whether the plotting does not fail with an error and that
    # it retuns an Axis object as promised
    ax = brian_plot(morpho)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_dendrogram(morpho)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_morphology(morpho)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_morphology(morpho, show_diameter=True)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_morphology(morpho, show_compartments=True)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()
    ax = plot_morphology(morpho, show_diameter=True,
                         show_compartments=True)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()

def test_plot_morphology_values():
    set_device('runtime')
    # Only testing 2D plotting for now
    morpho = Soma(diameter=30*um)
    morpho.axon = Cylinder(diameter=10*um, n=10, length=100*um)
    morpho.dend = Section(diameter=np.linspace(10, 1, 11)*um, n=10,
                          length=np.ones(10)*5*um)
    morpho = morpho.generate_coordinates()

    neuron = SpatialNeuron(morpho, 'Im = 0*amp/meter**2 : amp/meter**2')

    # Just checking whether the plotting does not fail with an error and that
    # it retuns an Axis object as promised
    ax = plot_morphology(morpho, values=neuron.distance, plot_3d=False)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()

    ax = plot_morphology(morpho, values=neuron.distance,
                         show_diameter=True, plot_3d=False)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()

    ax = plot_morphology(morpho, values=neuron.distance,
                         show_compartments=True, plot_3d=False)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()

    ax = plot_morphology(morpho, values=neuron.distance,
                         show_diameter=True,
                         show_compartments=True, plot_3d=False)
    assert isinstance(ax, matplotlib.axes.Axes)
    plt.close()

    # Check a few wrong usages
    with pytest.raises(DimensionMismatchError):
        plot_morphology(morpho, values=neuron.distance, value_unit=mV, plot_3d=False)
    with pytest.raises(DimensionMismatchError):
        plot_morphology(morpho, values=neuron.distance, value_norm=(-65*mV, None),
                        plot_3d=False)
    with pytest.raises(DimensionMismatchError):
        plot_morphology(morpho, values=neuron.distance, value_norm=(None, -60*mV),
                        plot_3d=False)
    with pytest.raises(TypeError):
        plot_morphology(morpho, values=neuron.distance, value_norm=(0*meter,
                                                             1*meter,
                                                             2*meter),
                        plot_3d=False)


def test_plot_morphology_values_per_compartment_2d():
    set_device('runtime')
    morpho = Soma(diameter=20*um)
    morpho.axon = Cylinder(diameter=2*um, n=3, length=30*um)
    morpho = morpho.generate_coordinates()

    # one value for the soma and three different values for the axon compartments
    values = np.array([0., 1., 2., 3.])
    ax = plot_morphology(morpho, values=values, plot_3d=False,
                         show_compartments=False, show_diameter=False)

    # For the axon (n=3) we expect one plotted line segment per compartment.
    section_lines = [line for line in ax.lines if line.get_linewidth() == 2]
    assert len(section_lines) == 3

    # Compartment values differ, therefore at least two colors should differ.
    section_colors = [tuple(line.get_color()) for line in section_lines]
    assert len(set(section_colors)) > 1
    plt.close()


if __name__ == '__main__':
    test_plot_monitors()
    test_plot_synapses()
    test_plot_morphology()
