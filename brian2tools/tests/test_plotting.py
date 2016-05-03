'''
Test the brian2tools package
'''
import matplotlib
matplotlib.use('Agg')

from brian2 import *
from brian2tools import *

def test_import():
    # Make sure that the expected names are there
    brian_plot
    plot_raster
    plot_state
    plot_rate
    plot_synapses
    plot_dendrogram
    plot_morphology

def test_plot_monitors():
    group = NeuronGroup(10, 'dv/dt = -v/(10*ms) : volt', threshold='False',
                        method='linear')
    group.v = linspace(0, 1, 10)*mV
    spike_mon = SpikeMonitor(group)
    rate_mon = PopulationRateMonitor(group)
    state_mon = StateMonitor(group, 'v', record=[3, 5])
    run(10*ms)

    # Just checking whether the plotting does not fail with an error
    brian_plot(spike_mon)
    close()
    plot_raster(spike_mon.i, spike_mon.t)
    close()
    brian_plot(rate_mon)
    close()
    plot_rate(rate_mon.t, rate_mon.rate)
    close()
    brian_plot(state_mon)
    close()
    plot_state(state_mon.t, state_mon.v.T)


def test_plot_synapses():
    group = NeuronGroup(10, 'dv/dt = -v/(10*ms) : volt', threshold='False')
    group.v = linspace(0, 1, 10)*mV
    synapses = Synapses(group, group, 'w : volt', on_pre='v += w')
    synapses.connect('i != j')
    synapses.w = 'i*0.1*mV'
    # Just checking whether the plotting does not fail with an error
    brian_plot(synapses)
    close()
    plot_synapses(synapses.i, synapses.j)
    close()
    plot_synapses(synapses.i, synapses.j, plot_type='scatter')
    close()
    plot_synapses(synapses.i, synapses.j, plot_type='image')
    close()
    plot_synapses(synapses.i, synapses.j, plot_type='hexbin')
    close()
    plot_synapses(synapses.i, synapses.j, synapses.w)
    close()
    plot_synapses(synapses.i, synapses.j, synapses.w, plot_type='scatter')
    close()
    plot_synapses(synapses.i, synapses.j, synapses.w, plot_type='image')
    close()
    plot_synapses(synapses.i, synapses.j, synapses.w, plot_type='hexbin')
    close()

    synapses.connect('i > 5')  # More than one synapse per connection
    brian_plot(synapses)
    close()
    # It should be possible to plot synaptic variables for multiple connections
    # with hexbin
    plot_synapses(synapses.i, synapses.j, synapses.w, plot_type='hexbin')
    close()


def test_plot_morphology():
    # Only testing 2D plotting for now
    morpho = Soma(diameter=30*um)
    morpho.axon = Cylinder(diameter=10*um, n=10, length=100*um)
    morpho.dend = Section(diameter=np.linspace(10, 1, 11)*um, n=10,
                          length=np.ones(10)*5*um)
    morpho = morpho.generate_coordinates()

    # Just checking whether the plotting does not fail with an error
    brian_plot(morpho)
    close()
    plot_dendrogram(morpho)
    close()
    plot_morphology(morpho)
    close()


if __name__ == '__main__':
    test_import()
    test_plot_monitors()
    test_plot_synapses()
    test_plot_morphology()
