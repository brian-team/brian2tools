import os
import matplotlib
matplotlib.use('Agg')
from brian2 import *

morpho = Morphology.from_file('51-2a.CNG.swc')

from brian2tools import *

fig_dir = '../../../docs_sphinx/images'
import mayavi.mlab as mayavi

brian_plot(morpho)
savefig(os.path.join(fig_dir, 'plot_dendrogram.svg'))
close()
plot_morphology(morpho)  # 3d plot
mayavi.show()
figure()
plot_morphology(morpho, plot_3d=False)
savefig(os.path.join(fig_dir, 'plot_morphology_2d.svg'))
close()

# Value plots
neuron = SpatialNeuron(morpho, 'Im = 0*amp/meter**2 : amp/meter**2')

figure()
plot_morphology(neuron.morphology, values=neuron.distance,
                plot_3d=False)
savefig(os.path.join(fig_dir, 'plot_morphology_values_2d.svg'))
close()

figure()
plot_morphology(neuron.morphology, values=neuron.distance,
                value_norm=(50*um, 200*um),
                value_colormap='viridis', value_unit=mm,
                value_colorbar={'label': 'distance from soma in mm',
                                'extend': 'both'},
                plot_3d=False)
savefig(os.path.join(fig_dir, 'plot_morphology_values_2d_custom.svg'))
close()

plot_morphology(morpho, plot_3d=True, show_compartments=True,
                show_diameter=True, colors=('darkblue',))
mayavi.show()

neuron = SpatialNeuron(morpho, 'Im = 0*amp/meter**2 : amp/meter**2')
plot_morphology(morpho, values=neuron.distance, plot_3d=True)
mayavi.show()