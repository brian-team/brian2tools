'''
Module to plot Brian `Morphology` objects.
'''
from matplotlib.patches import Circle, Polygon
import matplotlib.pyplot as plt
import numpy as np

from brian2.units.stdunits import um
from brian2.spatialneuron.morphology import Soma

# Only import the module to avoid circular import issues
import base


def _plot_morphology2D(morpho, axes, colors, show_diameter=False,
                       color_counter=0):
    color = colors[color_counter % len(colors)]

    if isinstance(morpho, Soma):
        x, y = morpho.x/um, morpho.y/um
        radius = morpho.diameter/um/2
        circle = Circle((x, y), radius=radius, color=color)
        axes.add_artist(circle)
        # FIXME: Ugly workaround to make the auto-scaling work
        axes.plot([x-radius, x, x+radius, x], [y, y-radius, y, y+radius],
                  color='white', alpha=0.)
    else:
        coords = morpho.coordinates
        if show_diameter:
            coords_2d = coords[:, :2]/um
            directions = np.diff(coords_2d, axis=0)
            orthogonal = np.vstack([-directions[:, 1], directions[:, 0]])
            orthogonal = np.vstack([orthogonal.T, orthogonal[:, -1:].T])
            radius = np.hstack([morpho.start_diameter[0]/um/2,
                                morpho.end_diameter/um/2])
            orthogonal /= np.sqrt(np.sum(orthogonal**2, axis=1))[:, np.newaxis]
            points = np.vstack([coords_2d+ orthogonal*radius[:, np.newaxis],
                                (coords_2d - orthogonal*radius[:, np.newaxis])[::-1]])
            patch = Polygon(points, color=color)
            axes.add_artist(patch)
            # FIXME: Ugly workaround to make the auto-scaling work
            axes.plot(points[:, 0], points[:, 1], color='white', alpha=0.)
        else:
            axes.plot(coords[:, 0]/um, coords[:, 1]/um, color='black',
                      lw=2)
        # dots at the center of the compartments
        if show_diameter:
            color = 'black'
        axes.plot(morpho.x/um, morpho.y/um, 'o', color=color,
                  mec='none', alpha=0.75)

    for child in morpho.children:
        _plot_morphology2D(child, axes=axes, show_diameter=show_diameter,
                           colors=colors, color_counter=color_counter+1)


def plot_morphology(morphology, plot_2d=None, show_diameter=False,
                    colors=('darkblue', 'darkred'), axes=None, newfigure=False,
                    showplot=True):
    axes = base._setup_axes(axes, newfigure)
    if plot_2d is None:
        plot_2d = True
    if plot_2d:
        _plot_morphology2D(morphology, axes, colors,
                           show_diameter=show_diameter)
        axes.set_aspect('equal')
    else:
        raise NotImplementedError('3D plotting not implemented yet')
    if showplot:
        plt.show()
    return axes
