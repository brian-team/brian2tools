import re
import os
import shutil
import numpy as np

import lems.api as lems
from brian2.input.poissoninput import PoissonInput
from brian2.units.fundamentalunits import is_dimensionless
from brian2.units import mmetre, ms
from brian2.utils.stringtools import get_identifiers
from brian2.utils.logger import get_logger
from brian2.devices.device import all_devices
from brian2tools.baseexport.device import BaseExporter

from .lemsrendering import *
from .supporting import (read_nml_units, read_nml_dims, brian_unit_to_lems,
                         name_to_unit, NeuroMLSimulation, NeuroMLSimpleNetwork,
                         NeuroMLTarget, NeuroMLPoissonGenerator)

__all__ = []

logger = get_logger(__name__)

SPIKE             = "spike"
LAST_SPIKE        = "lastspike"
NOT_REFRACTORY    = "not_refractory"
INTEGRATING       = "integrating"
REFRACTORY        = "refractory"
UNLESS_REFRACTORY = "unless refractory"
INDEX             = "index"    # iterator in LEMS
BASE_CELL         = "baseCell"
BASE_POPULATION   = "basePopulation"

nmlcdpath = os.path.dirname(__file__)  # path to NeuroMLCoreDimensions.xml file
LEMS_CONSTANTS_XML = "LEMSUnitsConstants.xml"  # path to units constants
LEMS_INPUTS = "Inputs.xml"
nml_dims  = read_nml_dims(nmlcdpath=nmlcdpath)
nml_units = read_nml_units(nmlcdpath=nmlcdpath)

renderer = LEMSRenderer()


def _find_precision(value):
    "Returns precision from a float number eg 0.003 -> 0.001"
    splitted = str(value).split('.')
    if len(splitted[0]) > 1:
        return 10**len(splitted[0])
    else:
        return 10**(-1*len(splitted[1]))


def _determine_dimension(value):
    """
    From *value* with Brian2 unit determines proper LEMS dimension.
    """
    for dim in nml_dims:
        if value.has_same_dimensions(nml_dims[dim]):
            return dim
    else:
        if value == 1:
            # dimensionless
            return "none"
        else:
            raise AttributeError("Dimension not recognized: {}".format(str(value.dim)))


def _to_lems_unit(unit):
    """
    From given unit (and only unit without value!) it returns LEMS unit
    """
    if type(unit) == str:
        strunit = unit
    else:
        strunit = unit.in_best_unit()
        strunit = strunit[3:]               # here we substract '1. '
    strunit = strunit.replace('^', '')  # in LEMS there is no ^
    return strunit


def _equation_separator(equation):
    """
    Separates *equation* (str) to LHS and RHS.
    """
    try:
        lhs, rhs = re.split('<=|>=|==|=|>|<', equation)
    except ValueError:
        return None
    return lhs.strip(), rhs.strip()


def make_lems_unit(newunit):
    """
    Returns from *newunit* to a lems.Unit definition.
    """
    strunit = _to_lems_unit(newunit)
    power = int(np.log10((mmetre**2).base))
    dimension = _determine_dimension(newunit)
    return lems.Unit(strunit, symbol=strunit, dimension=dimension, power=power)


class NMLExporter(object):
    """
    Exporter from Brian2 code to NeuroML.
    """
    def __init__(self):
        self._model = lems.Model()
        self._all_params_unit = {}
        self._population = None
        self._model_namespace = {'neuronname': None,
                                 'ct_populationname': None,
                                 'populationname': None,
                                 'networkname': None,
                                 'targetname': None,
                                 'simulname': None,
                                 'poiss_generator': "poiss"}

    def _determine_parameters(self, paramdict):
        """
        Iterator giving `lems.Parameter` for every parameter from *paramdict*.
        """
        for var in paramdict:
            if is_dimensionless(paramdict[var]):
                self._all_params_unit[var] = "none"
                yield lems.Parameter(var, "none")
            else:
                dim = _determine_dimension(paramdict[var])
                self._all_params_unit[var] = dim
                yield lems.Parameter(var, dim)

    def _determine_properties(self, paramdict = {}):
        """
        Iterator giving `lems.Property` for every parameter from *paramdict*.
        """
        for var in paramdict:
            if is_dimensionless(paramdict[var]):
                self._all_params_unit[var] = "none"
                yield lems.Property(var, "none")
            else:
                dim = _determine_dimension(paramdict[var])
                self._all_params_unit[var] = dim
                yield lems.Property(var, dim)

    def _unit_lems_validator(self, value_in_unit):
        """
        Checks if *unit* is in NML supported units and if it is not
        it adds a new definition to model. Eventually returns value
        with unit in string.
        """
        if is_dimensionless(value_in_unit):
            return str(value_in_unit)
        value, unit = value_in_unit.in_best_unit().split(' ')
        lemsunit = _to_lems_unit(unit)
        if lemsunit in nml_units:
            return "{} {}".format(value, lemsunit)
        else:
            self._model.add(make_lems_unit(name_to_unit[unit]))
            return "{} {}".format(value, lemsunit)

    def _event_builder(self, events):
        """
        From events yield lems.OnCondition objects
        """
        # loop ober the events of the group
        for event in events:
            event_out = lems.EventOut(event)  # output (e.g. spike)
            # get threshold condition and add it to on_cond
            on_cond_code = events[event]['threshold']['code']
            on_cond = lems.OnCondition(renderer.render_expr(on_cond_code))
            on_cond.add_action(event_out)
            # if event is not in model ports add it
            if event not in self._component_type.event_ports:
                self._component_type.add(lems.EventPort(name=event, direction='out'))
            # check and add reset equations
            if 'reset' in events[event]:
                reset_code = events[event]['reset']['code']
                # loop over multiple reset codes
                for single_reset_code in re.split(';|\n', reset_code):
                    single_reset_eq = _equation_separator(single_reset_code)
                    on_cond.add_action(lems.StateAssignment(single_reset_eq[0], single_reset_eq[1]))
            # check event is spike
            spike_flag = False
            if event == 'spike':
                spike_flag = True
            yield (spike_flag, on_cond)

    def add_neurongroup(self,neurongrp, index_neurongrp, initializers):
        """
        Add NeuronGroup to self._model

        If number of elements is 1 it adds component of that type, if
        it's bigger, the network is created by calling:
        `make_multiinstantiate`.

        Parameters
        ----------
        neurongrp : dict
            Standard dictionary representation of NeuronGroup object
        index_neurongrp : int
            Index of neurongroup in the network
        initializers : list
            List of initializers defined in the network
        """
        # get name of the neurongrp
        component_name = neurongrp['name']
        self._model_namespace["neuronname"] = component_name
        # add BASE_CELL component
        self._component_type = lems.ComponentType(component_name, extends=BASE_CELL)
        # get identifiers attached to neurongrp and create special_properties dict
        identifiers = []
        special_properties = {}

        if 'identifiers' in neurongrp:
            identifiers = neurongrp['identifiers']

        for initializer in initializers:
            if 'identifiers' in initializer:
                identifiers.update(initializer['identifiers'])

        for identifier in identifiers.keys():
            special_properties.update({identifier: None})

        # add the identifers as properties of the component
        for param in self._determine_properties(identifiers):
            self._component_type.add(param)
        # common things for every neuron definition
        # TODO: Is this same for custom events too?
        self._component_type.add(lems.EventPort(name='spike', direction='out'))

        # dynamics of the network
        dynamics = lems.Dynamics()
        # get neurongrp equations
        equations = neurongrp['equations']
        # loop over the variables
        initializer_vars = []
        for initializer in initializers:
            if initializer['source'] == neurongrp['name']:
                initializer_vars.append(initializer['variable'])

        for var in equations.keys():

            # determine the dimension
            dimension = _determine_dimension(equations[var]['unit'])
            # add to all_params_unit
            self._all_params_unit[var] = dimension
            # identify diff eqns to add Exposure
            if equations[var]['type'] == 'differential equation':
                state_var = lems.StateVariable(var, dimension=dimension, exposure=var)
                self._component_type.add(lems.Exposure(var, dimension=dimension))
                dynamics.add_state_variable(state_var)
            else:
                if var in initializer_vars and 'i' in initializer['value']:
                    self._component_type.add(lems.Property(var, dimension))
                    special_properties[var] = initializer['value']
                    continue
                state_var = lems.StateVariable(var, dimension=dimension)
                dynamics.add_state_variable(state_var)

        # what happens at initialization
        onstart = lems.OnStart()
        # loop over the initializers
        for var in equations.keys():
            if var in (NOT_REFRACTORY, LAST_SPIKE):
                continue
            # check the initializer is connected to this neurongrp
            if var not in initializer_vars:
                continue
            if var in special_properties:
                continue
            for initializer in initializers:
                if initializer['variable'] == var and initializer['source'] == neurongrp['name']:
                    init_value = initializer['value']
            if type(init_value) != str:
                value = brian_unit_to_lems(init_value)
            else:
                value = renderer.render_expr(str(init_value))
            # add to onstart
            onstart.add(lems.StateAssignment(var, value))
        dynamics.add(onstart)

        # check whether refractoriness is defined
        if ('events' in neurongrp and
            'spike' in neurongrp['events'] and
            'refractory' in neurongrp['events']['spike']):
            # if refractoriness, we create separate regimes for integrating
            integr_regime = lems.Regime(INTEGRATING, dynamics, True)  # True -> initial regime
            # check spike event
            # NOTE: isn't refractory only for spike events?
            for spike_flag, on_cond in self._event_builder(neurongrp['events']):
                if spike_flag:
                    # if spike occured we make transition to refractory regime
                    on_cond.add_action(lems.Transition(REFRACTORY))
                integr_regime.add_event_handler(on_cond)
            # add refractory regime
            refrac_regime = lems.Regime(REFRACTORY, dynamics)
            # make lastspike variable and initialize it
            refrac_regime.add_state_variable(lems.StateVariable(LAST_SPIKE, dimension='time'))
            oe = lems.OnEntry()
            oe.add(lems.StateAssignment(LAST_SPIKE, 't'))
            refrac_regime.add(oe)
            # after refractory time we make transition to integrating regime
            refractory_code = neurongrp['events']['spike']['refractory']
            if not _equation_separator(str(refractory_code)):
                # if there is no specific variable given, we assume
                # that this is time condition
                ref_oc = lems.OnCondition('t .gt. ( {0} + {1} )'.format(LAST_SPIKE, brian_unit_to_lems(refractory_code)))
            else:
                ref_oc = lems.OnCondition(renderer.render_expr(refractory_code))
            ref_trans = lems.Transition(INTEGRATING)
            ref_oc.add_action(ref_trans)
            refrac_regime.add_event_handler(ref_oc)
            # identify variables with differential equation
            for var in neurongrp['equations']:
                if neurongrp['equations'][var]['type'] == 'differential equation':
                    diff_var =  neurongrp['equations'][var]
                    # get the expression
                    td = lems.TimeDerivative(var, renderer.render_expr(diff_var['expr']))
                    # check flags for UNLESS_REFRACTORY TODO: is this available in 'flags' key?
                    if 'flags' in diff_var:
                        # if unless refratory we add only do integration regime
                        if UNLESS_REFRACTORY in diff_var['flags']:
                            integr_regime.add_time_derivative(td)
                            continue
                    # add time derivative to both regimes
                    integr_regime.add_time_derivative(td)
                    refrac_regime.add_time_derivative(td)
            # add the regimes to dynamics
            dynamics.add_regime(integr_regime)
            dynamics.add_regime(refrac_regime)

        else:
            # adding events directly to dynamics
            for spike_flag, on_cond in self._event_builder(neurongrp['events']):
                dynamics.add_event_handler(on_cond)
            # get variables with diff eqns
            for var in neurongrp['equations']:
                if neurongrp['equations'][var]['type'] == 'differential equation':
                    diff_var =  neurongrp['equations'][var]
                    td = lems.TimeDerivative(var, renderer.render_expr(diff_var['expr']))
                    # add to dynamics
                    dynamics.add_time_derivative(td)
        # add dynamics to _component_type
        self._component_type.dynamics = dynamics
        # add _component_type to _model
        self._model.add_component_type(self._component_type)
        # get identifiers
        paramdict = dict()
        for ident_name, ident_value in neurongrp['identifiers'].items():
            paramdict[ident_name] = self._unit_lems_validator(ident_value)
        # if more than one neuron use multiinstantiate
        if neurongrp['N'] == 1:
            self._model.add(lems.Component("n{}".format(index_neurongrp),
                                           component_name, **paramdict))
        else:
            self.make_multiinstantiate(special_properties, component_name,
                                       paramdict, neurongrp['N'])

    def make_multiinstantiate(self, special_properties, name, parameters, N):
        """
        Adds ComponentType with MultiInstantiate in order to make
        a population of neurons

        Parameters
        ----------
        initializers : list
            list of initializers passed in the run
        name : str
            MultiInstantiate component name
        parameters : dict
            all extra parameters
        N : int
            size of the population
        """

        PARAM_SUBSCRIPT = "_p"
        # add ComponentType of population
        self._model_namespace["ct_populationname"] = name+"Multi"
        multi_ct = lems.ComponentType(self._model_namespace["ct_populationname"],
                                      extends=BASE_POPULATION)
        # create lems structure and multiinstantiate
        structure = lems.Structure()
        multi_ins = lems.MultiInstantiate(component_type=name,
                                          number="N")
        param_dict = {}
        # number of neurons
        multi_ct.add(lems.Parameter(name="N", dimension="none"))

        for sp in special_properties:
            if special_properties[sp] is None:
                multi_ct.add(lems.Parameter(name=sp+PARAM_SUBSCRIPT, dimension=self._all_params_unit[sp]))
                multi_ins.add(lems.Assign(property=sp, value=sp+PARAM_SUBSCRIPT))
                param_dict[sp] = parameters[sp]
            else:
                # multi_ct.add(lems.Parameter(name=sp, dimension=self._all_params_unit[sp]))
                # check if there are some units in equations
                equation = special_properties[sp]
                # add spaces around brackets to prevent mismatching
                equation = re.sub("\(", " ( ", equation)
                equation = re.sub("\)", " ) ", equation)
                for i in get_identifiers(equation):
                    # iterator is a special case
                    if i == "i":
                        regexp_noletter = "[^a-zA-Z0-9]"
                        equation = re.sub("{re}i{re}".format(re=regexp_noletter),
                                                  " {} ".format(INDEX), equation)
                    # here it's assumed that we don't use Netwton in neuron models
                    elif i in name_to_unit and i != "N":
                        const_i = i+'const'
                        multi_ct.add(lems.Constant(name=const_i, symbol=const_i,
                                     dimension=self._all_params_unit[sp], value="1"+i))
                        equation = re.sub(i, const_i, equation)
                multi_ins.add(lems.Assign(property=sp, value=equation))

        structure.add(multi_ins)
        multi_ct.structure = structure
        self._model.add(multi_ct)
        param_dict = dict([(k+"_p", v) for k, v in param_dict.items()])
        param_dict["N"] = N
        self._model_namespace["populationname"] = self._model_namespace["ct_populationname"] + "pop"
        self._model_namespace["networkname"] = self._model_namespace["ct_populationname"] + "Net"
        self.add_population(self._model_namespace["networkname"],
                            self._model_namespace["populationname"],
                            self._model_namespace["ct_populationname"],
                            **param_dict)

    def add_statemonitor(self, statemonitor, filename="recording", outputfile=False):
        """
        Recording in LEMS simulation, makes a display and recording file
        Make sure before calling that *simulation* object is created.

        Parameters
        ----------
        statemonitor : dict
            Dictionary for statemonitor from baseexport
        filename : str, optional
            name of output file without extension, default 'recording'
        outputfile : dict, optional
            flag sayinf whether to record output to file or only add
            display, default False
        """

        filename += '.dat'
        # get the indices of neurons that are being monitored
        indices = statemonitor['record']
        # if all are monitored else use the array
        if isinstance(indices, bool) and indices == True:
            indices = np.arange(statemonitor['n_indices'])
        else:
            indices = np.asarray(indices).copy()
        # get the variables monitored
        variables = statemonitor['variables']
        # timestep of monitoring
        dt = str(statemonitor['dt'].in_unit(ms))
        # TODO: In the docstring, asked to check the _simulation
        self._simulation.update_simulation_attribute('step', dt)
        # adding display and outputcolumn for each recorded neuron
        for e, var in enumerate(variables):
            self._simulation.add_display("disp{}".format(e), str(var)) #TODO: max, min etc ??? (asked prev)
            if outputfile:
                self._simulation.add_outputfile("of{}".format(e), filename=filename)
            for i in indices:
                #TODO: scale, time_scale ??? (asked prev)
                self._simulation.add_line("line{}".format(i),
                                          "{}[{}]/v".format(self._model_namespace["populationname"], i))
                if outputfile:
                    self._simulation.add_outputcolumn("{}".format(i),
                                                      "{}[{}]/v".format(self._model_namespace["populationname"], i))

    def add_eventmonitor(self, eventmonitor, filename="recording"):
        """
        Recording in LEMS simulation for eventmonitor
        Make sure before calling that *simulation* object is created.

        Parameters
        ----------
        eventmonitor : dict
            Dictionary representation for SpikeMonitor
        filename : str, optional
            name of output file without extension, default 'recording'
        """
        # if event is spike else use .dat
        if eventmonitor['event'] == 'spike':
            filename += '.spikes'
        else:
            filename += '.dat'
        # get the indices of the source
        indices = eventmonitor['record']
        # if record is True use spikemonitor['source_size']
        if isinstance(indices, bool) and indices is True:
            indices = np.arange(eventmonitor['source_size'])
        else:
            indices = np.asarray(indices).copy()
        # get variables #NOTE: no use variables?
        variables = eventmonitor['variables']
        # add event output file
        self._simulation.add_eventoutputfile("eof", filename)
        # adding eventselection for each recorded neuron
        for i in indices:
            self._simulation.add_eventselection("line{}".format(i),
                    "{}[{}]".format(self._model_namespace["populationname"], i),
                    event_port=eventmonitor['event'])

    def add_spikemonitor(self, spikemonitor, filename="recording"):
        """
        Recording in LEMS simulation for spikemonitor
        Make sure before calling that *simulation* object is created.

        Parameters
        ----------
        spikemonitor : dict
            Dictionary representation for SpikeMonitor
        filename : str, optional
            name of output file without extension, default 'recording'
        """
        # pass to eventmonitor
        self.add_eventmonitor(spikemonitor, filename)

    def add_synapses(self, obj):
        """
        TO DO - not ready to use
        Adds synapses to the model.
        Parameters
        ----------
        obj : brian2.Synapse
            Synapse object
        """
        synapse_ct = lems.ComponentType('Synapse')
        dynamics_synapse = lems.Dynamics()
        synapse_ct.add(dynamics_synapse)

    def add_input(self, obj, counter=''):
        """
        Extends DOM model (*self._dommodel*) of Network Input.
        Currently only PoissonInput support.

        Parameters
        ----------
        obj : Standard dict representation of PoissonInput
        counter : str or int, optional
            number of object added to identifier
        """
        if isinstance(obj,PoissonInput):
            name = '{}{}'.format(self._model_namespace['poiss_generator'], str(counter))
            nml_poisson = NeuroMLPoissonGenerator(name, float(obj['rate']))
            nml_poisson = nml_poisson.build()
            self._extend_dommodel(nml_poisson)
        else:
            raise NotImplementedError("Currently only PoissonInput supported.")

    def add_population(self, net_id, component_id, type_, **args):
        """
        Sets population of neurons to resulting file.

        Parameters
        ----------
        net_id : str
            network id
        component_id : str
            component id
        type_ : str
            component type
        args : ...
            all extra keyword arguments
        """
        nmlnetwork = NeuroMLSimpleNetwork(net_id)
        nmlnetwork.add_component(component_id, type_, **args)
        self._population = nmlnetwork.build()

    def add_include(self, includefile):
        """
        Adds file to include *includefile* to model.
        *includefile* -- str

        Parameters
        ----------
        includefile : str
            name of the file to include
        """
        self._model.add(lems.Include(includefile))

    def create_lems_model(self, run_dict, constants_file=None, includes=[],
                          recordingsname='recording'):
        """
        Create lems model using standard dictionary

        Parameters
        ----------
        run_dict : dict
            standard dictionary representation of information required
            for creating lems model
        constants_file : str, optional
            file with units as constants definitions, if None an
            LEMS_CONSTANTS_XML is added automatically
        includes : list of str
            all additional XML files added in preamble
        recordingsname : str, optional
            output of LEMS simulation recordings, values with extension
            .dat and spikes with .spikes, default 'recording'
        """

        # if no constants_file is specified, use LEMS_CONSTANTS_XML
        if not constants_file:
            self._model.add(lems.Include(LEMS_CONSTANTS_XML))
        else:
            self._model.add(lems.Include(constants_file))
        # add includes files
        includes = set(includes)
        for include in INCLUDES:
            includes.add(include)

        # TODO: deal with single run for now
        single_run = run_dict[0]
        # check initializers are defined
        initializers = []
        if 'initializers_connectors' in single_run:
            for item in single_run['initializers_connectors']:
                if item['type'] == 'initializer':
                    initializers.append(item)

        netinputs = []
        if 'poissoninput' in single_run['components'].keys():
            netinputs = single_run['components']['poissoninput']

        if netinputs:
            includes.add(LEMS_INPUTS)
        for include in includes:
            self.add_include(include)

        if 'neurongroup' in single_run['components'].keys():
            neuron_count = 0
            for neurongroup in single_run['components']['neurongroup']:
                self.add_neurongroup(neurongroup, neuron_count, initializers)
                neuron_count += 1

        # DOM structure of the whole model is constructed below
        self._dommodel = self._model.export_to_dom()
        # add input
        input_counter = 0
        for poisson_inp in netinputs:
            self.add_input(poisson_inp, input_counter)
            input_counter += 1
        # A population should be created in `make_multiinstantiate`
        # so we can add it to our DOM structure.
        if self._population:
            self._extend_dommodel(self._population)

        self._model_namespace['simulname'] = "sim1"
        self._simulation = NeuroMLSimulation(self._model_namespace['simulname'],
                                             self._model_namespace['networkname'])

        #loop over components field of single_run
        for (obj_name, obj_list) in single_run['components'].items():

            #check unsupported
            if obj_name == 'synapses':
                raise NotImplementedError("Synapses are not supported yet")

            # check whether StateMonitor
            if obj_name == 'statemonitor':
                # loop over the statemonitors defined
                for statemonitor in obj_list:
                    self.add_statemonitor(statemonitor, filename=recordingsname, outputfile=True)

            # check whether SpikeMonitor
            if obj_name == 'spikemonitor':
                for spikemonitor in obj_list:
                    self.add_spikemonitor(spikemonitor, filename=recordingsname)

            # check whether EventMonitor
            # TODO: is this valid in NML/LEMS?
            if obj_name == 'eventmonitor':
                for eventmonitor in obj_list:
                    self.add_eventmonitor(eventmonitor, filename=recordingsname)

        # build the simulation
        simulation = self._simulation.build()
        self._extend_dommodel(simulation)
        target = NeuroMLTarget(self._model_namespace['simulname'])
        target = target.build()
        self._extend_dommodel(target)

    def export_to_file(self, filename):
        """
        Exports model to file *filename*
        """
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        if len(filename.split(".")) == 1:
            filename += ".xml"
        xmlstring = self._dommodel.toprettyxml("  ", "\n")
        with open(filename, "w") as f:
            f.write(xmlstring)

    def _extend_dommodel(self, child):
        """
        Extends self._dommodel DOM structure with *child*
        """
        self._dommodel.childNodes[0].appendChild(child)

    @property
    def model(self):
        return self._dommodel


########################################################################
# Code Generation Mechanism
########################################################################

INCLUDES = ["Simulation.xml", "NeuroML2CoreTypes.xml"]


class DummyCodeObject(object):
    def __init__(self, *args, **kwds):
        pass

    def __call__(self, **kwds):
        pass


class LEMSDevice(BaseExporter):
    """
    The `Device` used for LEMS/NeuroML2 export of the Brian models
    Use `set_device('neuroml2', filename='myfilename.xml')` to inform Brian
    to run in this mode. It derives from BaseExporter and use `self.runs`
    dictionary for exporting. It has only build() as other RunDevice methods
    are defined in BaseExporter
    """

    def build(self, filename=None, direct_call=True, lems_const_save=True):
        """
        Get information from BaseExport to start lems/neuroml2 export and create
        output files
        """
        # get directory and filename
        dirname, filename = os.path.split(filename)
        dirname = os.path.abspath(dirname)
        # TODO: should be extended to multiple runs
        if len(self.runs) > 1:
            raise NotImplementedError("Currently only single run is supported.")
        # get filename without extension
        if len(filename.split(".")) != 1:
            filename_ = os.path.join(dirname, 'recording_' + filename.split(".")[0])
        else:
            filename_ = os.path.join(dirname, 'recording_' + filename)
        # create object for exporter class
        exporter = NMLExporter()
        # prepare lems model using dictionary of baseexport
        exporter.create_lems_model(self.runs, recordingsname=filename_)
        exporter.export_to_file(os.path.join(dirname, filename))
        # currently NML2/LEMS model requires units stored as constants
        # in a separate file
        if lems_const_save:
            shutil.copyfile(os.path.join(nmlcdpath, LEMS_CONSTANTS_XML),
                            os.path.join(dirname, LEMS_CONSTANTS_XML))

lems_device = LEMSDevice()
all_devices['neuroml2'] = lems_device
