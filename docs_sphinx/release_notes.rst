Release notes
=============

brian2tools 0.1.2
-----------------
This is mostly a bug-fix release but also adds a few new features and improvements around the plotting of synapses
(see below).

Improvements and bug fixes
~~~~~~~~~~~~~~~~~~~~~~~~~~
* Synaptic plots of the "image" type with `~brian2tools.plotting.synapses.plot_synapses` (also the default for
  `~brian2tools.plotting.base.brian_plot` for synapses between small numbers of neurons) where plotting a transposed
  version of the correct connection matrix that was in addition potentially cut off and therefore not showing all
  connections (#6).
* Fix that `~brian2tools.plotting.base.brian_plot` was not always returning the `~matplotlib.axes.Axes` object.
* Enable direct calls of `~brian2tools.plotting.base.brian_plot` with a synaptic variable or an indexed
  `~brian2.monitors.statemonitor.StateMonitor` (to only plot a subset of recorded cells).
* Do not plot `0` as a value for non-existing synapses in `image` and `hexbin`-style plots.
* A new function `~brian2tools.plotting.base.add_background_pattern` to add a hatching pattern to the figure background
  (for colormaps that include the background color).

Testing, suggestions and bug reports:

* Ibrahim Ozturk

brian2tools 0.1
---------------
This is the first release of the `brian2tools` package (a collection of optional tools for the
`Brian 2 simulator <http://briansimulator.org>`), providing several plotting functions to plot model properties
(such as synapses or morphologies) and simulation results (such as raster plots or voltage traces). It also introduces
a convenience function `~brian2tools.plotting.base.brian_plot` which takes a Brian 2 object as an argument and produces
a plot based on it. See :doc:`user/plotting` for details.

Contributions
~~~~~~~~~~~~~
The code in this first release has been written by Marcel Stimberg (`@mstimberg <https://github.com/mstimberg>`_).