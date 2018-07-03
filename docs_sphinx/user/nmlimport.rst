NeuroML importer (nmlimport library)
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

As a demonstration, we will use nmlimport library to generate morphology and
extract other related information from the ``pyramidal cell's`` nml file. You
can download it from `here <https://github
.com/OpenSourceBrain/ACnet2/blob/master/neuroConstruct/generatedNeuroML2/pyr_4_sym.cell.nml>`_.


.. code:: python

    from brian2tools.nmlimport.nml import NmlMorphology
    nml_object = NmlMorphology('pyramidal.cell.nml',name_heuristic=True)

This call provides us the ``nml_object`` that contains all the information
extracted from `.nml` file. When ``name_heuristic`` param is set to True
morphology sections will be determined based on the segment names and section
name will be created by combining names of the inner segments of the section
else if set to False, all linearly connected segments combines and form a
section and naming convention `sec{unique integer}` is followed.

|
- To obtain morphology object.

.. code:: python

    morphology=nml_object.morphology_obj
|

- To obtain topology information.

.. code:: python

    print(morphology.topology())

    # Output

    -|  [root]
       `-|  .apical0
          `---|  .apical0.apical2_3_4
          `-|  .apical0.apical1
       `-|  .basal0
          `-|  .basal0.basal1
          `-|  .basal0.basal2
|

- To get the morphology area.

.. code:: python

    print(morphology.area)

    # Output
    [ 1228.36272755] um^2
|

- To get the morphology coordinates.

.. code:: python

    print(morphology.coordinates)

    # Output
    [[  0.   0.   0.]
    [  0.  17.   0.]] um
|

- To get the morphology length.

.. code:: python

    print(morphology.length)

    # Output
    [ 17.] um
|

- To get the morphology distance.

.. code:: python

    print(morphology.distance)

    # Output
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


- To get the resolved group ids of an nml `SegmentGroup`. This returns a
    dictionary that maps `SegmentGroup` ids to its member segment id's.


.. code:: python

    print(nml_object.resolved_grp_ids)

    # Output
    {'soma': [0], 'apical0': [1], 'apical2': [2], 'apical3': [3], 'apical4':
    [4], 'apical1': [5], 'basal0': [6], 'basal1': [7], 'basal2': [8], 'all':
    [0, 1, 2, 3, 4, 5, 6, 7, 8], 'soma_group': [0], 'dendrite_group':
    [1, 2, 3, 4, 5, 6, 7, 8], 'apical_dends': [1, 2, 3, 4, 5],
    'middle_apical_dendrite': [3], 'thalamic_input': [5], 'basal_dends':
    [8, 6, 7], 'basal_gaba_input': [6], 'background_input': [7]}
|

- To get the information of all the child segments of a parent segment. This
  returns a list that maps segment id to its child segments id's.

.. code:: python

    print(nml_object.children)

    # Output
    defaultdict(<class 'list'>, {0: [1, 6], 1: [2, 5], 2: [3], 3: [4],
    6: [7, 8], 4: [], 5: [], 7: [], 8: []})
|

The file ``pyramidal.cell.nml`` will look something like this:

.. code-block:: xml
    :linenos:

    <cell id="pyr_4_sym">
        <morphology id="morphology_pyr_4_sym">
            <segment id="0" name="soma">
                <proximal x="0.0" y="0.0" z="0.0" diameter="23.0"/>
                <distal x="0.0" y="17.0" z="0.0" diameter="23.0"/>
            </segment>

            <segment id="1" name="apical0">
                <parent segment="0"/>
                <proximal x="0.0" y="17.0" z="0.0" diameter="6.0"/>
                <distal x="0.0" y="77.0" z="0.0" diameter="6.0"/>
            </segment>

            <segment id="2" name="apical2">
                <parent segment="1"/>
                <proximal x="0.0" y="77.0" z="0.0" diameter="4.4"/>
                <distal x="0.0" y="477.0" z="0.0" diameter="4.4"/>
            </segment>

            <segment id="3" name="apical3">
                <parent segment="2"/>
                <proximal x="0.0" y="477.0" z="0.0" diameter="2.9"/>
                <distal x="0.0" y="877.0" z="0.0" diameter="2.9"/>
            </segment>

            <segment id="4" name="apical4">
                <parent segment="3"/>
                <proximal x="0.0" y="877.0" z="0.0" diameter="2.0"/>
                <distal x="0.0" y="1127.0" z="0.0" diameter="2.0"/>
            </segment>

            <segment id="5" name="apical1">
                <parent segment="1"/>
                <proximal x="0.0" y="77.0" z="0.0" diameter="3.0"/>
                <distal x="-150.0" y="77.0" z="0.0" diameter="3.0"/>
            </segment>

            <segment id="6" name="basal0">
                <parent segment="0" fractionAlong="0.0"/>
                <proximal x="0.0" y="17.0" z="0.0" diameter="4.0"/>
                <distal x="0.0" y="-50.0" z="0.0" diameter="4.0"/>
            </segment>

            <segment id="7" name="basal1">
                <parent segment="6"/>
                <proximal x="0.0" y="-50.0" z="0.0" diameter="5.0"/>
                <distal x="106.07" y="-156.07" z="0.0" diameter="5.0"/>
            </segment>

            <segment id="8" name="basal2">
                <parent segment="6"/>
                <proximal x="0.0" y="-50.0" z="0.0" diameter="5.0"/>
                <distal x="-106.07" y="-156.07" z="0.0" diameter="5.0"/>
            </segment>

            <segmentGroup id="soma" neuroLexId="sao864921383">

                <member segment="0"/>
            </segmentGroup>

            <segmentGroup id="apical0" neuroLexId="sao864921383">

                <member segment="1"/>
            </segmentGroup>

            <segmentGroup id="apical2" neuroLexId="sao864921383">

                <member segment="2"/>
            </segmentGroup>

            <segmentGroup id="apical3" neuroLexId="sao864921383">

                <member segment="3"/>
            </segmentGroup>

            <segmentGroup id="apical4" neuroLexId="sao864921383">

                <member segment="4"/>
            </segmentGroup>

            <segmentGroup id="apical1" neuroLexId="sao864921383">

                <member segment="5"/>
            </segmentGroup>

            <segmentGroup id="basal0" neuroLexId="sao864921383">

                <member segment="6"/>
            </segmentGroup>

            <segmentGroup id="basal1" neuroLexId="sao864921383">

                <member segment="7"/>
            </segmentGroup>

            <segmentGroup id="basal2" neuroLexId="sao864921383">

                <member segment="8"/>
            </segmentGroup>

            <segmentGroup id="all">
                <include segmentGroup="soma"/>
                <include segmentGroup="apical0"/>
                <include segmentGroup="apical2"/>
                <include segmentGroup="apical3"/>
                <include segmentGroup="apical4"/>
                <include segmentGroup="apical1"/>
                <include segmentGroup="basal0"/>
                <include segmentGroup="basal1"/>
                <include segmentGroup="basal2"/>
            </segmentGroup>

            <segmentGroup id="soma_group" neuroLexId="GO:0043025">

                <include segmentGroup="soma"/>
            </segmentGroup>

            <segmentGroup id="dendrite_group" neuroLexId="GO:0030425">

                <include segmentGroup="apical0"/>
                <include segmentGroup="apical2"/>
                <include segmentGroup="apical3"/>
                <include segmentGroup="apical4"/>
                <include segmentGroup="apical1"/>
                <include segmentGroup="basal0"/>
                <include segmentGroup="basal1"/>
                <include segmentGroup="basal2"/>
            </segmentGroup>

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

            <segmentGroup id="thalamic_input">
                <include segmentGroup="apical1"/>
            </segmentGroup>

            <segmentGroup id="basal_dends">
                <include segmentGroup="basal0"/>
                <include segmentGroup="basal1"/>
                <include segmentGroup="basal2"/>
            </segmentGroup>

            <segmentGroup id="basal_gaba_input">
                <include segmentGroup="basal0"/>
            </segmentGroup>

            <segmentGroup id="background_input">
                <include segmentGroup="basal1"/>
            </segmentGroup>
        </morphology>
    </cell>

Handling FractionAlong value
--------------------------------

If you look at the ``line 39`` in above .nml file, you can see
``fractionAlong=0.0``. fractionAlong value defines the point at which the
given segment is connected with its parent segment. So a fractionAlong value
of 1 means the segment is connected to bottom (distal) of its parent segment, 0
means it is connected to the top (proximal) of its parent segment. Similarly a
value of 0.5 would mean the segment is connected to the middle point of its parent
segment. Currently `nmlimport` library supports `fractionAlong` value to be
0 or 1 only, as there is no predefined way to connect a segment at
some inbetween point of its parent segment in `Brian`.