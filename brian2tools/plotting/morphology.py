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
            axes.plot(coords[:, 0], coords[:, 1], color=color, lw=2)
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


def _plot_morphology3D(morpho, figure, colors, show_diameters=True,
                       show_compartments=False):
    import mayavi.mlab as mayavi
    colors = np.vstack(colorConverter.to_rgba(c) for c in colors)
    flat_morpho = FlatMorphology(morpho)
    if isinstance(morpho, Soma):
        start_idx = 1
        # Plot the Soma
        mayavi.points3d(flat_morpho.x[0]/float(um),
                        flat_morpho.y[0]/float(um),
                        flat_morpho.z[0]/float(um),
                        flat_morpho.diameter[0]/float(um),
                        figure=figure, color=tuple(colors[0, :-1]),
                        resolution=16, scale_factor=1)
    else:
        start_idx = 0
    if show_compartments:
        # plot points at center of compartment
        if show_diameters:
            diameters = flat_morpho.diameter[start_idx:]/float(um)/10
        else:
            diameters = np.ones(len(flat_morpho.diameter) - start_idx)
        mayavi.points3d(flat_morpho.x[start_idx:]/float(um),
                        flat_morpho.y[start_idx:]/float(um),
                        flat_morpho.z[start_idx:]/float(um),
                        diameters,
                        figure=figure, color=(0, 0, 0),
                        resolution=16, scale_factor=1)
    # Plot all other compartments
    start_points = np.vstack([flat_morpho.start_x[start_idx:]/float(um),
                              flat_morpho.start_y[start_idx:]/float(um),
                              flat_morpho.start_z[start_idx:]/float(um)]).T
    end_points = np.vstack([flat_morpho.end_x[start_idx:]/float(um),
                            flat_morpho.end_y[start_idx:]/float(um),
                            flat_morpho.end_z[start_idx:]/float(um)]).T
    points = np.empty((2*len(start_points), 3))
    points[::2, :] = start_points
    points[1::2, :] = end_points
    # Create the points at start and end of the compartments
    src = mayavi.pipeline.scalar_scatter(points[:, 0],
                                         points[:, 1],
                                         points[:, 2],
                                         flat_morpho.depth[start_idx:].repeat(2),
                                         scale_factor=1)
    # Create the lines between compartments
    connections = []
    for start, end in zip(flat_morpho.starts[1:], flat_morpho.ends[1:]):
        # we only need the lines within the sections
        new_connections = [((idx-1)*2, (idx-1)*2 + 1)
                           for idx in xrange(start, end)]
        connections.extend(new_connections)
    connections = np.vstack(connections)
    src.mlab_source.dataset.lines = connections
    if show_diameters:
        radii = flat_morpho.diameter[start_idx:].repeat(2)/float(um)/2
        src.mlab_source.dataset.point_data.add_array(radii)
        src.mlab_source.dataset.point_data.get_array(1).name = 'radius'
        src.update()
    lines = mayavi.pipeline.stripper(src)
    if show_diameters:
        lines = mayavi.pipeline.set_active_attribute(lines,
                                                     point_scalars='radius')
        tubes = mayavi.pipeline.tube(lines)
        tubes.filter.vary_radius = 'vary_radius_by_absolute_scalar'
        tubes = mayavi.pipeline.set_active_attribute(tubes,
                                                 point_scalars='scalars')
    else:
        tubes = mayavi.pipeline.tube(lines, tube_radius=1)
    max_depth = max(flat_morpho.depth)
    surf = mayavi.pipeline.surface(tubes, colormap='prism', line_width=1,
                                   opacity=0.5,
                                   vmin=0, vmax=max(flat_morpho.depth))
    surf.module_manager.scalar_lut_manager.lut.number_of_colors = max_depth + start_idx
    cmap = np.int_(np.round(255*colors[np.arange(max_depth + start_idx)%len(colors), :]))
    surf.module_manager.scalar_lut_manager.lut.table = cmap
    src.update()


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
                           show_diameters=show_diameter,
                           show_compartments=show_compartments)
        axes.scene.disable_render = False
        if showplot:
            mayavi.show()
    else:
        axes = base._setup_axes_matplotlib(axes, newfigure)
        _plot_morphology2D(morphology, axes, colors,
                           show_compartments=show_compartments,
                           show_diameter=show_diameter)
        axes.set_xlabel('x (um)')
        axes.set_ylabel('y (um)')
        axes.set_aspect('equal')
        if showplot:
            plt.show()

    return axes
