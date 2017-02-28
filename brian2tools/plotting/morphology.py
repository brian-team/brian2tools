'''
Module to plot Brian `~brian2.spatialneuron.morphology.Morphology` objects.
'''
import numpy as np
from brian2.spatialneuron.spatialneuron import FlatMorphology

from matplotlib.colors import colorConverter
from matplotlib.patches import Circle, Polygon
import matplotlib.pyplot as plt

from brian2.units.stdunits import um
from brian2.spatialneuron.morphology import Soma

__all__ = ['plot_morphology', 'plot_dendrogram']


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
            coords_2d = coords[:, :2]
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
                           for idx in range(start, end)]
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
                    axes=None):
    '''
    Plot a given `~brian2.spatialneuron.morphology.Morphology` in 2D or 3D.

    Parameters
    ----------
    morphology : `~brian2.spatialneuron.morphology.Morphology`
        The morphology to plot
    plot_3d : bool, optional
        Whether to plot the morphology in 3D or in 2D. If not set (the default)
        a morphology where all z values are 0 is plotted in 2D, otherwise it is
        plot in 3D.
    show_compartments : bool, optional
        Whether to plot a dot at the center of each compartment. Defaults to
        ``False``.
    show_diameter : bool, optional
        Whether to plot the compartments with the diameter given in the
        morphology. Defaults to ``False``.
    colors : sequence of color specifications
        A list of colors that is cycled through for each new section. Can be
        any color specification that matplotlib understands (e.g. a string such
        as ``'darkblue'`` or a tuple such as `(0, 0.7, 0)`.
    axes : `~matplotlib.axes.Axes` or `~mayavi.core.api.Scene`, optional
        A matplotlib `~matplotlib.axes.Axes` (for 2D plots) or mayavi
        `~mayavi.core.api.Scene` ( for 3D plots) instance, where the plot will
        be added.

    Returns
    -------
    axes : `~matplotlib.axes.Axes` or `~mayavi.core.api.Scene`
        The `~matplotlib.axes.Axes` or `~mayavi.core.api.Scene` instance that
        was used for plotting. This object allows to modify the plot further,
        e.g. by setting the plotted range, the axis labels, the plot title, etc.
    '''
    # Avoid circular import issues
    from brian2tools.plotting.base import (_setup_axes_matplotlib,
                                           _setup_axes_mayavi)
    if plot_3d is None:
        # Decide whether to use 2d or 3d plotting based on the coordinates
        flat_morphology = FlatMorphology(morphology)
        plot_3d = any(np.abs(flat_morphology.z) > 1e-12)

    if plot_3d:
        try:
            import mayavi.mlab as mayavi
        except ImportError:
            raise ImportError('3D plotting needs the mayavi library')
        axes = _setup_axes_mayavi(axes)
        axes.scene.disable_render = True
        _plot_morphology3D(morphology, axes, colors=colors,
                           show_diameters=show_diameter,
                           show_compartments=show_compartments)
        axes.scene.disable_render = False
    else:
        axes = _setup_axes_matplotlib(axes)
        _plot_morphology2D(morphology, axes, colors,
                           show_compartments=show_compartments,
                           show_diameter=show_diameter)
        axes.set_xlabel('x (um)')
        axes.set_ylabel('y (um)')
        axes.set_aspect('equal')

    return axes


def plot_dendrogram(morphology, axes=None):
    '''
    Plot a "dendrogram" of a morphology, i.e. an abstract representation which
    visualizes the branching structure and the length of each section.

    Parameters
    ----------
    morphology : `~brian2.spatialneuron.morphology.Morphology`
        The morphology to visualize.
    axes : `~matplotlib.axes.Axes`, optional
        The `~matplotlib.axes.Axes` instance used for plotting. Defaults to
        ``None`` which means that a new `~matplotlib.axes.Axes` will be
        created for the plot.

    Returns
    -------
    axes : `~matplotlib.axes.Axes`
        The `~matplotlib.axes.Axes` instance that was used for plotting. This
        object allows to modify the plot further, e.g. by setting the plotted
        range, the axis labels, the plot title, etc.
    '''
    # Avoid circular import issues
    from brian2tools.plotting.base import _setup_axes_matplotlib
    axes = _setup_axes_matplotlib(axes)
    # Get some information from the flattened morphology
    flat_morpho = FlatMorphology(morphology)
    section_depth = flat_morpho.depth[flat_morpho.starts]
    section_distance = flat_morpho.end_distance/float(um)
    n_sections = flat_morpho.sections
    max_depth = max(flat_morpho.depth)
    max_children = max(flat_morpho.morph_children_num)
    children = flat_morpho.morph_children

    length_metric = section_distance

    # Each point should be in the middle of its two outermost terminal points
    # We go backwards through the tree, noting for each point all terminal
    # indices in its subtree
    terminals = [set() for _ in range(n_sections)]
    terminal_counter = 0
    for d in range(max_depth, -1, -1):
        for idx in np.nonzero(section_depth == d)[0]:
            child_start_idx = (idx+1)*max_children
            num_children = flat_morpho.morph_children_num[idx+1]
            if num_children == 0:
                terminals[idx] = {terminal_counter}
                terminal_counter += 1
            else:
                child_indices = children[child_start_idx:child_start_idx+num_children]
                terminals[idx].update(*[terminals[c-1] for c in child_indices])

    # Now we make sure that subtrees starting at a lower x value will be left
    # of other subtrees
    # This is probably not the most efficient algorithm, but it seems to work
    order_strings = [[] for _ in range(terminal_counter)]
    for idx in np.argsort(length_metric):
        child_terminals = terminals[idx]
        for t, order_string in enumerate(order_strings):
            if t in child_terminals:
                order_string.extend('A')
            else:
                order_string.extend('B')
    order_strings = [''.join(s) for s in order_strings]
    terminal_x_values = np.argsort(np.argsort(order_strings))
    # Use the re-arranged values to calculate the actual x value for the tree
    min_index = [min(terminal_x_values[np.array(list(ts), dtype=int)])
                 for ts in terminals]
    max_index = [max(terminal_x_values[np.array(list(ts), dtype=int)])
                 for ts in terminals]

    x_values = (np.array(min_index) + np.array(max_index)) / 2.0

    # Plot the dendogram with lengths of the vertical lines representing the
    # total distance to the root
    plt.plot(x_values[0], length_metric[0], 'ko', clip_on=False)
    for sec, (x, depth) in enumerate(zip(x_values, length_metric)):
        child_start_idx = (sec+1)*max_children
        num_children = flat_morpho.morph_children_num[sec+1]
        if num_children > 0:
            child_indices = children[child_start_idx:child_start_idx+num_children]
            child_depth = length_metric[child_indices-1]
            child_x = x_values[child_indices-1]
            axes.vlines(child_x, depth, child_depth, clip_on=False, lw=2)
            axes.hlines(depth, min(child_x), max(child_x), lw=2)
    axes.set_xticks([])
    axes.set_ylabel('distance from root (um)')
    axes.set_xlim(-1, terminal_counter)
    return axes
