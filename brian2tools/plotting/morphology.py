'''
Module to plot Brian `Morphology` objects.
'''
import numpy as np
from brian2.spatialneuron.spatialneuron import FlatMorphology

from matplotlib.colors import colorConverter
from matplotlib.patches import Circle, Polygon
import matplotlib.pyplot as plt

from brian2.units.stdunits import um
from brian2.spatialneuron.morphology import Soma

# Only import the module to avoid circular import issues
import base


def _plot_morphology2D(morpho, axes, colors, show_diameter=False,
                       show_compartments=True, color_counter=0):
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
        coords = morpho.coordinates/um
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
        if show_compartments:
            # dots at the center of the compartments
            if show_diameter:
                color = 'black'
            axes.plot(morpho.x/um, morpho.y/um, 'o', color=color,
                      mec='none', alpha=0.75)

    for child in morpho.children:
        _plot_morphology2D(child, axes=axes,
                           show_compartments=show_compartments,
                           show_diameter=show_diameter,
                           colors=colors, color_counter=color_counter+1)


def _plot_morphology3D(morpho, figure, colors, color_counter=0,
                       show_compartments=False):
    import mayavi.mlab as mayavi
    color = colorConverter.to_rgb(colors[color_counter % len(colors)])
    if isinstance(morpho, Soma):
        mayavi.points3d(morpho.x/um, morpho.y/um, morpho.z/um,
                        morpho.diameter/um, figure=figure,
                        color=color, scale_factor=1.0, resolution=16)
    else:
        coords = morpho.coordinates/um
        mayavi.plot3d(coords[:, 0], coords[:, 1], coords[:, 2],
                      figure=figure, color=color, tube_radius=1)
        # dots at the center of the compartments
        if show_compartments:
            mayavi.points3d(coords[:, 0], coords[:, 1], coords[:, 2],
                            np.ones(coords.shape[0]), color=color,
                            figure=figure, scale_factor=1, opacity=0.25)

    for child in morpho.children:
        _plot_morphology3D(child, figure=figure,
                           show_compartments=show_compartments,
                           colors=colors, color_counter=color_counter+1)


def plot_morphology(morphology, plot_3d=None, show_compartments=False,
                    show_diameter=False, colors=('darkblue', 'darkred'),
                    axes=None, newfigure=False, showplot=True):

    if plot_3d is None:
        # Decide whether to use 2d or 3d plotting based on the coordinates
        flat_morphology = FlatMorphology(morphology)
        plot_3d = any(np.abs(flat_morphology.z) > 1e-12)

    if plot_3d:
        try:
            import mayavi.mlab as mayavi
        except ImportError:
            raise ImportError('3D plotting needs the mayavi library')
        axes = base._setup_axes_mayavi(axes, newfigure)
        axes.scene.disable_render = True
        _plot_morphology3D(morphology, axes, colors=colors,
                           show_compartments=show_compartments)
        axes.scene.disable_render = False
        if showplot:
            mayavi.show()
    else:
        axes = base._setup_axes_matplotlib(axes, newfigure)
        _plot_morphology2D(morphology, axes, colors,
                           show_compartments=show_compartments,
                           show_diameter=show_diameter)
        axes.set_aspect('equal')
        if showplot:
            plt.show()

    return axes
