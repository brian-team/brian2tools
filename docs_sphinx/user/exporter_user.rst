Brian2NeuroML exporter
======================

This is a short overview of Brian2 supporting package providing functionality of exporting
a model to NeuroML2/LEMS format. 

The NeuroML is a XML based description that provides a common data format 
for defining and exchanging descriptions of neuronal cell and network models 
(`NML project website <https://neuroml.org/>`_).

.. contents::
    Overview
    :local:

Working example
---------------

As a demonstration we use simple unconnected Integrate&Fire neurons model with refractoriness
and given initial values.

.. code:: python

    from brian2 import *
    import brian2lems

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

The use of exporter is pretty straightforward. You need to import a device
parsing brian2 code from module ``brian2lems``.

The next thing is to set the device called ``neuroml2`` which generates NeuroML2/LEMS code.
Note that you need to specify named argument ``filename`` with a name of your model.

.. code:: python

    import brian2lems

    set_device('neuroml2', filename="nml2model.xml")

The result of the above code have form of of file ``filename`` and extra file ``LEMSUnitsConstants.xml``
with units definition in a form of constants (needed to properly parse equations).

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

One important thing to notice is that the exporting device creates a new ``ComponentType`` for each
cell definition implemented as a brian2 ``NeuronGroup``. Later that particular ``ComponentType`` is initialized as a new one
(here called ``neuron1Multi``) by ``MultiInstantiate`` and eventually a network (``neuron1MultiNet``) 
is created out of a defined component (``neuron1Multipop``).

Note also that the integration method does not matter for the NeuroML export,
as NeuroML/LEMS only describes the model not how it is numerically integrated.

To validate the output we recommend to use a tool `jNeuroML <https://github.com/NeuroML/jNeuroML>`_.
Make sure that the ``jnml`` have access to ``NeuroML2CoreTypes`` folder.

After successful installation of the package, type in your terminal:

.. code:: bash

    jnml filename.xml

to run the simulation.


Supported Features
------------------

Currently exporter supports such brian2 objects like:

- ``NeuronGroup`` - Used to specify definition of a cell. Mechanism like threshold, reset or refractoriness are taken into account. Moreover, you may set your model parameters (like ``v0`` above) arbitrary initial values.

- ``StateMonitor`` - If you use StateMonitor to record some variables, it is transformed to ``Line`` at the ``Display`` of  NeuroML2 simulation and an ``OutputFile`` tag is added to the model. A name of the output file is ``recording_<<filename>>.dat``.

- ``SpikeMonitor`` - SpikeMonitor is parsed to ``EventOutputFile`` with name ``recording_<<filename>>.spikes``.

Limitations
-----------

Things to be implemented in the future:

- synapses

- network input

- multiple runs of simulation
