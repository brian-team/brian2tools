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
plt.savefig(os.path.join(fig_dir, 'brian_plot_synapses.png'))
close()

plot_synapses(synapses.i, synapses.j, plot_type='scatter', color='gray', marker='s')
plt.savefig(os.path.join(fig_dir, 'plot_synapses_connections.svg'))
close()

subplot(1, 2, 1)
brian_plot(synapses.w)
subplot(1, 2, 2)
brian_plot(synapses.delay)
tight_layout()
plt.savefig(os.path.join(fig_dir, 'plot_synapses_weights_delays.svg'))
close()

ax = plot_synapses(synapses.i, synapses.j, synapses.w, var_name='synaptic weights',
                   plot_type='scatter', cmap='hot')
add_background_pattern(ax)
ax.set_title('Recurrent connections')
synapses.connect(j='i+k for k in sample(-10, 10, p=0.5) if k != 0',
                 skip_if_invalid=True)  # ignore values outside of the limits
plt.savefig(os.path.join(fig_dir, 'plot_synapses_weights_custom.png'))
close()

brian_plot(synapses)
plt.savefig(os.path.join(fig_dir, 'brian_plot_multiple_synapses.png'))
close()

big_group = NeuronGroup(10000, '')
many_synapses = Synapses(big_group, big_group)
many_synapses.connect(j='i+k for k in range(-2000, 2000) if rand() < exp(-(k/1000.)**2)',
                      skip_if_invalid=True)
brian_plot(many_synapses)
plt.savefig(os.path.join(fig_dir, 'brian_plot_synapses_big.png'))
close()
