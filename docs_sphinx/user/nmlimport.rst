NeuroML importer
================

This is a short overview of the `~brian2tools.nmlimport` package, providing
functionality to import Brian's morphology from a .nml file.

NeuroML is a XML-based description that provides a common data format
for defining and exchanging descriptions of neuronal cell and network models
(`NML project website <https://neuroml.org/>`_).

.. contents::
    Overview
    :local:

Working example
---------------

As a demonstration, we will use the nmlimport library to generate morphology and
extract other related information from the ``pyr_4_sym.cell.nml`` nml file. You
can download it from `here <https://github
.com/OpenSourceBrain/ACnet2/blob/master/neuroConstruct/generatedNeuroML2/pyr_4_sym.cell.nml>`_.


.. code:: python

    from brian2tools.nmlimport.nml import NMLMorphology
    nml_object = NMLMorphology('pyr_4_sym.cell.nml', name_heuristic=True)

This call provides us the ``nml_object`` that contains all the information
extracted from ``.nml`` file. When ``name_heuristic`` param is set to True
morphology sections will be determined based on the segment names. In
this case Section name will be created by combining names of the inner
segments of the section. When set to False, all linearly connected
segments combines to form a section and naming convention
``sec{unique_integer}`` is followed.

|

- To obtain morphology object.

.. code:: python

    >>> morphology = nml_object.morphology_obj

|

With this Morphology object, you can use all of Brian's functions to get information about the cell:

.. code:: python

    >>> print(morphology.topology())
    -|  [root]
       `-|  .apical0
          `---|  .apical0.apical2_3_4
          `-|  .apical0.apical1
       `-|  .basal0
          `-|  .basal0.basal1
          `-|  .basal0.basal2

    >>> print(morphology.area)
    [ 1228.36272755] um^2

    >>> print(morphology.coordinates)
    [[  0.   0.   0.]
    [  0.  17.   0.]] um

    >>> print(morphology.length)
    [ 17.] um

    >>> print(morphology.distance)
    [ 8.5] um

|

- Plot morphology using brian2tool's plot_morphology function.

.. code:: python

    from brian2tools.plotting.morphology import plot_morphology
    plot_morphology(morphology)

.. figure:: ../images/pyramidal_morphology.png
   :scale: 80 %
   :alt: Pyramidal cell's morphology plot.

   Pyramidal cell's Morphology plot.

Handling SegmentGroup
---------------------

SegmentGroup is a method to group multiple segments under single entity.
This can later be used to apply operations on all segments of a SegmentGroup.
To get the resolved group ids of an nml ``SegmentGroup``. This returns a
dictionary that maps ``SegmentGroup`` ids to its member segment id's.


.. code:: python

    >>> print(nml_object.resolved_grp_ids)
    {'soma': [0], 'apical0': [1], 'apical2': [2], 'apical3': [3], 'apical4':
    [4], 'apical1': [5], 'basal0': [6], 'basal1': [7], 'basal2': [8], 'all':
    [0, 1, 2, 3, 4, 5, 6, 7, 8], 'soma_group': [0], 'dendrite_group':
    [1, 2, 3, 4, 5, 6, 7, 8], 'apical_dends': [1, 2, 3, 4, 5],
    'middle_apical_dendrite': [3], 'thalamic_input': [5], 'basal_dends':
    [8, 6, 7], 'basal_gaba_input': [6], 'background_input': [7]}

|

The file ``pyr_4_sym.cell.nml`` will look something like this:

.. code-block:: xml
    :linenos:

    <cell id="pyr_4_sym">
        <morphology id="morphology_pyr_4_sym">
            <segment id="0" name="soma">
                <proximal x="0.0" y="0.0" z="0.0" diameter="23.0"/>
                <distal x="0.0" y="17.0" z="0.0" diameter="23.0"/>
            </segment>
            ..........
            ..........
            ..........

            <segment id="6" name="basal0">
                <parent segment="0" fractionAlong="0.0"/>
                <proximal x="0.0" y="17.0" z="0.0" diameter="4.0"/>
                <distal x="0.0" y="-50.0" z="0.0" diameter="4.0"/>
            </segment>
            ..........
            ..........
            ..........

            <segmentGroup id="apical_dends">
                <include segmentGroup="apical0"/>
                <include segmentGroup="apical2"/>
                <include segmentGroup="apical3"/>
                <include segmentGroup="apical4"/>
                <include segmentGroup="apical1"/>
            </segmentGroup>

            <segmentGroup id="middle_apical_dendrite">
                <include segmentGroup="apical3"/>
            </segmentGroup>
            ........
            ........
            ........
        </morphology>
    </cell>

Handling sections not connected at the distal end
-------------------------------------------------

If you look at the ``line 12`` in above .nml file, you can see
``fractionAlong=0.0``. fractionAlong value defines the point at which the
given segment is connected with its parent segment. So a fractionAlong value
of 1 means the segment is connected to bottom (distal) of its parent segment, 0
means it is connected to the top (proximal) of its parent segment. Similarly a
value of 0.5 would mean the segment is connected to the middle point of its parent
segment. Currently ``nmlimport`` library supports ``fractionAlong`` value to be
0 or 1 only, as there is no predefined way to connect a segment at
some inbetween point of its parent segment in ``Brian``.


Extracting channel properties and Equations
-------------------------------------------

The generated ``nml_object`` contains dictionary that have biophysical
information like threshold, refractory, Ri and Cm etc.

With this ``nml_object``, you can view all the properties extracted:

.. code:: python

    >>> print(nml_object.properties) # threshold, refractory etc.
    {'threshold': 'v > 0*mV', 'refractory': 'v > 0*mV',
    'Cm': 2.84 * ufarad / cmetre2,'Ri': 0.2 * kohm * cmetre}

    >>> print(nml_object.erevs) # erev property
    {'Ca_pyr': {'soma_group': 80. * mvolt}, 'Kahp_pyr': {'soma_group': -75. *
     mvolt}, 'Kdr_pyr': {'soma_group': -75. * mvolt}, 'LeakConductance_pyr':
     {'all': -66. * mvolt}, 'Na_pyr': {'soma_group': 55. * mvolt}}

    >>> print(nml_object.cond_densities) # cond_density property
    {'Ca_pyr': {'soma_group': 10. * msiemens / cmetre2}, 'Kahp_pyr':
    {'soma_group': 25. * siemens / meter ** 2}, 'Kdr_pyr':  {'soma_group': 80
    . * msiemens / cmetre2}, 'LeakConductance_pyr': {'all': 1.420051 *
    siemens / meter ** 2},  'Na_pyr': {'soma_group': 120. * msiemens / cmetre2}}

|

To get channel equations for a particular channel, ex. ``Na_pyr``:

.. code:: python

    >>> print(nml_object.get_channel_equations("Na_pyr"))
    alpha_m_Na_pyr = (1.28 * khertz) * (v - (-46.9 * mvolt)) / (4. * mvolt) / (1 - exp(- (v - (-46.9 * mvolt)) / (4. * mvolt))) : hertz
    alpha_h_Na_pyr = (128. * hertz) * exp((v - (-43. * mvolt))/(-18. * mvolt)) : hertz
    beta_m_Na_pyr = (1.4 * khertz) * (v - (-19.9 * mvolt)) / (-5. * mvolt) / (1 - exp(- (v - (-19.9 * mvolt)) / (-5. * mvolt))) : hertz
    beta_h_Na_pyr = (4. * khertz) / (1 + exp(0 - (v - (-20. * mvolt))/(5. * mvolt))) : hertz
    I_Na_pyr = g_Na_pyr*m_Na_pyr**2*h_Na_pyr*((55. * mvolt) - v) : amp / meter ** 2
    dm_Na_pyr/dt = alpha_m_Na_pyr*(1-m_Na_pyr) - beta_m_Na_pyr*m_Na_pyr : 1
    dh_Na_pyr/dt = alpha_h_Na_pyr*(1-h_Na_pyr) - beta_h_Na_pyr*h_Na_pyr : 1
    g_Na_pyr : siemens / meter ** 2


.. note::

    If your ``.nml file`` includes other .nml files, make sure they
    are present in the same folder as your main .nml file. If the files are
    not present, a warning will be thrown and execution will proceed as normal.


