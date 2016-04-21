import os
from brian2 import *

group = NeuronGroup(100, 'dv/dt = -v / (10*ms) : volt',
                    threshold='v > -50*mV', reset='v = -60*mV')

synapses = Synapses(group, group, 'w : volt', on_pre='v += w')

# Connect to cells with indices no more than +/- 10 from the source index with
# a probability of 50% (but do not create self-connections)
synapses.connect(j='i+k for k in sample(-10, 10, p=0.5) if k != 0',
                 skip_if_invalid=True)  # ignore values outside of the limits
# Set synaptic weights depending on the distance (in terms of indices) between
# the source and target cell and add some randomness
synapses.w = '(exp(-(i - j)**2/10.) + 0.5 * rand())*mV'
# Set synaptic weights randomly
synapses.delay = '1*ms + 2*ms*rand()'

from brian2tools import *
fig_dir = '../../../docs_sphinx/images'
brian_plot(synapses)
plt.savefig(os.path.join(fig_dir, 'brian_plot_synapses.svg'))
close()

plot_synapses(synapses.i, synapses.j, color='gray', marker='s')
plt.savefig(os.path.join(fig_dir, 'plot_synapses_connections.svg'))
close()

subplot(1, 2, 1)
plot_synapses(synapses.i, synapses.j, synapses.w)
subplot(1, 2, 2)
plot_synapses(synapses.i, synapses.j, synapses.delay)
tight_layout()
plt.savefig(os.path.join(fig_dir, 'plot_synapses_weights_delays.svg'))
close()

ax = plot_synapses(synapses.i, synapses.j, synapses.w, var_name='synaptic weights',
              marker='s', cmap='hot')
ax.set_axis_bgcolor('gray')
synapses.connect(j='i+k for k in sample(-10, 10, p=0.5) if k != 0',
                 skip_if_invalid=True)  # ignore values outside of the limits
plt.savefig(os.path.join(fig_dir, 'plot_synapses_weights_custom.svg'))
close()

brian_plot(synapses)
plt.savefig(os.path.join(fig_dir, 'brian_plot_multiple_synapses.svg'))
close()
