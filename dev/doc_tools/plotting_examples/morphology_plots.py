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
plot_morphology(morpho, plot_3d=True, show_compartments=True,
                show_diameter=True, colors=('darkblue',))
mayavi.show()
