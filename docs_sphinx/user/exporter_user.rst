NeuroML exporter
================

This is a short overview of the `~brian2tools.nmlexport` package, providing
functionality to export Brian 2 models to NeuroML2.

NeuroML is a XML-based description that provides a common data format
for defining and exchanging descriptions of neuronal cell and network models 
(`NML project website <https://neuroml.org/>`_).

.. contents::
    Overview
    :local:

Working example
---------------

As a demonstration, we use a simple unconnected Integrate & Fire neuron model
with refractoriness and given initial values.

.. code:: python

    from brian2 import *
    import brian2tools.nmlexport

    set_device('neuroml2', filename="nml2model.xml")

    n = 100
    duration = 1*second
    tau = 10*ms

    eqs = '''
    dv/dt = (v0 - v) / tau : volt (unless refractory)
    v0 : volt
    '''
    group = NeuronGroup(n, eqs, threshold='v > 10*mV', reset='v = 0*mV',
                        refractory=5*ms, method='linear')
    group.v = 0*mV
    group.v0 = '20*mV * i / (N-1)'

    rec_idx = [2, 63]
    statemonitor = StateMonitor(group, 'v', record=rec_idx)
    spikemonitor = SpikeMonitor(group, record=rec_idx)

    run(duration)

The use of the exporter requires only a few changes to an existing Brian 2
script. In addition to the standard ``brian2`` import at the beginning of your
script, you need to import the `brian2tools.nmlexport` package. You can then set
a "device" called ``neuroml2`` which will generate NeuroML2/LEMS code instead of
executing your model. You will also have to specify a keyword argument
``filename`` with the desired name of the output file.

The above code will result in a file ``nml2model.xml`` and an additional file
``LEMSUnitsConstants.xml`` with units definitions in form of constants
(necessary due to the way units are handled in LEMS equations).

The file ``nml2model.xml`` will look like this:

.. code:: xml

    <Lems>
      <Include file="NeuroML2CoreTypes.xml"/>
      <Include file="Simulation.xml"/>
      <Include file="LEMSUnitsConstants.xml"/>
      <ComponentType extends="baseCell" name="neuron1">
        <Property dimension="voltage" name="v0"/>
        <Property dimension="time" name="tau"/>
        <EventPort direction="out" name="spike"/>
        <Exposure dimension="voltage" name="v"/>
        <Dynamics>
          <StateVariable dimension="voltage" exposure="v" name="v"/>
          <OnStart>
            <StateAssignment value="0" variable="v"/>
          </OnStart>
          <Regime name="refractory">
            <StateVariable dimension="time" name="lastspike"/>
            <OnEntry>
              <StateAssignment value="t" variable="lastspike"/>
            </OnEntry>
            <OnCondition test="t .gt. ( lastspike + 5.*ms )">
              <Transition regime="integrating"/>
            </OnCondition>
          </Regime>
          <Regime initial="true" name="integrating">
            <TimeDerivative value="(v0 - v) / tau" variable="v"/>
            <OnCondition test="v .gt. (10 * mV)">
              <EventOut port="spike"/>
              <StateAssignment value="0*mV" variable="v"/>
              <Transition regime="refractory"/>
            </OnCondition>
          </Regime>
        </Dynamics>
      </ComponentType>
      <ComponentType extends="basePopulation" name="neuron1Multi">
        <Parameter dimension="time" name="tau_p"/>
        <Parameter dimension="none" name="N"/>
        <Constant dimension="voltage" name="mVconst" symbol="mVconst" value="1mV"/>
        <Structure>
          <MultiInstantiate componentType="neuron1" number="N">
            <Assign property="v0" value="20*mVconst * index /  ( N-1 ) "/>
            <Assign property="tau" value="tau_p"/>
          </MultiInstantiate>
        </Structure>
      </ComponentType>
      <network id="neuron1MultiNet">
        <Component N="100" id="neuron1Multipop" tau_p="10. ms" type="neuron1Multi"/>
      </network>
      <Simulation id="sim1" length="1s" step="0.1 ms" target="neuron1MultiNet">
        <Display id="disp0" timeScale="1ms" title="v" xmax="1000" xmin="0" ymax="11" ymin="0">
          <Line id="line3" quantity="neuron1Multipop[3]/v" scale="1mV" timeScale="1ms"/>
          <Line id="line64" quantity="neuron1Multipop[64]/v" scale="1mV" timeScale="1ms"/>
        </Display>
        <OutputFile fileName="recording_nml2model.dat" id="of0">
          <OutputColumn id="3" quantity="neuron1Multipop[3]/v"/>
          <OutputColumn id="64" quantity="neuron1Multipop[64]/v"/>
        </OutputFile>
        <EventOutputFile fileName="recording_nml2model.spikes" format="TIME_ID" id="eof">
          <EventSelection eventPort="spike" id="line3" select="neuron1Multipop[3]"/>
          <EventSelection eventPort="spike" id="line64" select="neuron1Multipop[64]"/>
        </EventOutputFile>
      </Simulation>
      <Target component="sim1"/>
    </Lems>

The exporting device creates a new ``ComponentType`` for each cell definition
implemented as a Brian 2 ``NeuronGroup``. Later that particular ``ComponentType``
is bundled with the initial value assignment into a a new ``ComponentType``
(here called ``neuron1Multi``) by ``MultiInstantiate`` and eventually a network
(``neuron1MultiNet``) is created out of a defined ``Component``
(``neuron1Multipop``).

Note that the integration method does not matter for the NeuroML export,
as NeuroML/LEMS only describes the model not how it is numerically integrated.

To validate the output, you can use the tool `jNeuroML <https://github.com/NeuroML/jNeuroML>`_.
Make sure that ``jnml`` has access to the ``NeuroML2CoreTypes`` folder by
setting the ``JNML_HOME`` environment variable.

With ``jnml`` installed you can run the simulation as follows:

.. code:: bash

    jnml nml2model.xml


Supported Features
------------------

Currently, the NeuroML2 export is restricted to simple neural models and only
supports the following classes (and a single run statement per script):

- ``NeuronGroup`` - The definition of a neuronal model. Mechanisms like
  threshold, reset and refractoriness are taken into account. Moreover, you may
  set the initial values of the model parameters (like ``v0`` above).
- ``StateMonitor`` - If your script uses a ``StateMonitor`` to record variables,
  each recorded variable is transformed into to a ``Line`` tag of the
  ``Display`` in the NeuroML2 simulation and an ``OutputFile`` tag is added to
  the model. The name of the output file is ``recording_<<filename>>.dat``.

- ``SpikeMonitor`` - A ``SpikeMonitor`` is transformed into an
  ``EventOutputFile`` tag, storing the spikes to a file named
  ``recording_<<filename>>.spikes``.

Limitations
-----------

As stated above, the NeuroML2 export is currently quite limited. In particular,
none of the following Brian 2 features are supported:

- Synapses
- Network input (``PoissonGroup``, ``SpikeGeneratorGroup``, etc.)
- Multicompartmental neurons (``SpatialNeuronGroup``)
- Non-standard simulation protocols (multiple runs, ``store``/``restore``
  mechanism, etc.).
