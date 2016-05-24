Release notes
=============

Current development version
---------------------------
TODO

Improvements and bug fixes
~~~~~~~~~~~~~~~~~~~~~~~~~~
* Synaptic plots of the "image" type with `~brian2tools.plotting.synapses.plot_synapses` (also the default for
  `~brian2tools.plotting.base.brian_plot` for synapses between small numbers of neurons) where plotting a transposed
  version of the correct connection matrix that was in addition potentially cut off and therefore not showing all
  connections (#6).
* Fix that `~brian2tools.plotting.base.brian_plot` was not always returning the `~matplotlib.axes.Axes` object.
* Enable direct calls of `~brian2tools.plotting.base.brian_plot` with a synaptic variable or an indexed
  `~brian2.monitors.statemonitor.StateMonitor` (to only plot a subset of recorded cells).

Testing, suggestions and bug reports (ordered alphabetically, apologies to anyone we forgot...):

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