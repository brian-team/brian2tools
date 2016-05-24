import os
import matplotlib
matplotlib.use('Agg')

from brian2 import *

eqs = '''dv/dt  = (ge+gi-(v + 49*mV))/(20*ms) : volt (unless refractory)
         dge/dt = -ge/(5*ms) : volt
         dgi/dt = -gi/(10*ms) : volt
      '''
P = NeuronGroup(4000, eqs, threshold='v>-50*mV', reset='v = -60*mV',
                refractory=5 * ms,
                method='linear')
P.v = '-60*mV + rand() * (-50*mV + 60*mV)'
P.ge = 0 * mV
P.gi = 0 * mV

we = (60 * 0.27 / 10) * mV  # excitatory synaptic weight (voltage)
wi = (-20 * 4.5 / 10) * mV  # inhibitory synaptic weight
Ce = Synapses(P[:3200], P, on_pre='ge += we')
Ci = Synapses(P[3200:], P, on_pre='gi += wi')
Ce.connect(p=0.02)
Ci.connect(p=0.02)

spike_mon = SpikeMonitor(P)
rate_mon = PopulationRateMonitor(P)
state_mon = StateMonitor(P, 'v', record=[0, 100, 1000])  # record three cells

run(1 * second)

from brian2tools import *
fig_dir = '../../../docs_sphinx/images'
brian_plot(spike_mon)
plt.savefig(os.path.join(fig_dir, 'brian_plot_spike_mon.png'))
close()
plot_raster(spike_mon.i, spike_mon.t, time_unit=second, marker=',', color='k')
plt.savefig(os.path.join(fig_dir, 'plot_raster.png'))
close()
brian_plot(rate_mon)
plt.savefig(os.path.join(fig_dir, 'brian_plot_rate_mon.svg'))
close()
plot_rate(rate_mon.t, rate_mon.smooth_rate(window='flat', width=10.1*ms),
          linewidth=3, color='gray')
plt.savefig(os.path.join(fig_dir, 'plot_rate.svg'))
close()
brian_plot(state_mon)
plt.savefig(os.path.join(fig_dir, 'brian_plot_state_mon.svg'))
close()
brian_plot(state_mon[1000])
plt.savefig(os.path.join(fig_dir, 'brian_plot_state_mon_view.svg'))
close()
ax = plot_state(state_mon.t, state_mon.v.T, var_name='membrane potential', lw=2)
ax.legend(['neuron 0', 'neuron 100', 'neuron 1000'], frameon=False, loc='best')
plt.savefig(os.path.join(fig_dir, 'plot_state.svg'))
close()
