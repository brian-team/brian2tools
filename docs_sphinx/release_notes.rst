Release notes
=============

brian2tools 0.3
---------------
This release adds a number of major new features to the package. In particular:

* the ability to :doc:`import neuronal morphologies from NeuroML descriptions <user/nmlimport>`,
  including information about channel types, channel densities, and general
  biophysical properties. This feature has been developed by Kapil Kumar
  (`@kapilkd13 <https://github.com/kapilkd13>`_) as part of the
  `Google Summer of Code <https://summerofcode.withgoogle.com/>`_ 2018.
* improved support for :doc:`exporting neuronal models to NeuroML <user/nmlexporter>,
  and a new :doc:`general framework to export model descriptions <user/baseexporter>`.
  As a demonstration of this framework, it is now possible to export a Brian model
  description as :doc:`human-readable markdown <user/mdexporter>`. This feature has
  been developed by Vigneswaran C (`@Vigneswaran-Chandrasekaran <https://github.com/Vigneswaran-Chandrasekaran>`_)
  as part of 2020's Google Summer of Code.
* improved support for :doc:`plotting morphologies <user/plotting>`. It is now possible to
  plot a morphology and color code a value that varies across the neuron (e.g. the membrane
  potential) on top of it. Thanks to `@mqcapelle <https://github.com/mqcapelle>`_ for
  contributing this feature.

Contributions
~~~~~~~~~~~~~
* Kapil Kumar (`@kapilkd13 <https://github.com/kapilkd13>`_)
* Vigneswaran C (`@Vigneswaran-Chandrasekaran <https://github.com/Vigneswaran-Chandrasekaran>`_)
* `@mqcapelle <https://github.com/mqcapelle>`_
* Marcel Stimberg (`@mstimberg <https://github.com/mstimberg>`_)

We also acknowledge the support of the `INCF <https://www.incf.org/>`_ in the organization of
the Google Summer of Code internships.

brian2tools 0.2.1.1
-------------------
A maintenance release that adds conda packages for Python 3.6. Also fixes a
small bug in morphology plotting.

brian2tools 0.2.1
-----------------
This release adds initial support to export Brian 2 simulations to the
`NeuroML2 <https://neuroml.org/neuromlv2>`_ and
`LEMS <http://lems.github.io/LEMS/>`_ format. This feature has been added by
Dominik Krzemiński (`@dokato <https://github.com/dokato>`_) as part of the
`Google Summer of Code <https://summerofcode.withgoogle.com/>`_ 2016 under the
umbrella of the `INCF <https://www.incf.org/>`_ organization. It currently
allows to export neuronal models (with threshold, reset and refractory
definition), but not synaptic models or multi-compartmental neurons. See the
:doc:`user/nmlexporter` documentation for details.

Contributions
~~~~~~~~~~~~~
* Dominik Krzemiński (`@dokato <https://github.com/dokato>`_)
* Marcel Stimberg (`@mstimberg <https://github.com/mstimberg>`_)

We also thank Padraig Gleeson (`@pgleeson <https://github.com/pgleeson/>`_) for
help and guidance concerning NeuroML2 and LEMS.


brian2tools 0.1.2
-----------------
This is mostly a bug-fix release but also adds a few new features and improvements around the plotting of synapses
(see below).

Improvements and bug fixes
~~~~~~~~~~~~~~~~~~~~~~~~~~
* Synaptic plots of the "image" type with `~brian2tools.plotting.synapses.plot_synapses` (also the default for
  `~brian2tools.plotting.base.brian_plot` for synapses between small numbers of neurons) where plotting a transposed
  version of the correct connection matrix that was in addition potentially cut off and therefore not showing all
  connections (:issue:`6`).
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