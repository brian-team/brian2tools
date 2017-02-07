import re
import os
import xml.dom.minidom as minidom

from brian2.units.allunits import all_units
from brian2 import get_or_create_dimension


name_to_unit = {u.dispname: u for u in all_units}


def from_string(rep):
    """
    Returns `Quantity` object from text representation of a value.

    Parameters
    ----------
    rep : `str`
        text representation of a value with unit

    Returns
    -------
    q : `Quantity`
        Brian Quantity object
    """
    # match value
    m = re.match('-?[0-9]+\.?([0-9]+)?[eE]?-?([0-9]+)?', rep)
    if m:
        value = rep[0:m.end()]
        rep = rep[m.end():]
    else:
        raise ValueError("Empty value given")
    # match unit
    m = re.match(' ?([a-zA-Z]+)', rep)
    unit = None
    per = None
    if m:
        unit = rep[0:m.end()].strip()
        # special case with per
        if unit == 'per':
            mper = re.match(' ?per_([a-zA-Z]+)', rep)
            per = rep[0:mper.end()].strip()[4:]
            m = mper
        rep = rep[m.end():]
    # match exponent
    m = re.match('-?([0-9]+)?', rep)
    exponent = None
    if len(rep) > 0 and m:
        exponent = rep[0:m.end()]
    if unit:
        if per:
            b2unit = 1. / name_to_unit[per]
        else:
            b2unit = name_to_unit[unit]
        if value and exponent:
            return float(value) * b2unit**float(exponent)
        elif value:
            return float(value) * b2unit
    else:
        return float(value)


def brian_unit_to_lems(valunit):
    """
    Returns string representation of LEMS unit where * is between
    value and unit e.g. "20. mV" -> "20.*mV".

    Parameters
    ----------
    valunit : `Quantity` or `str`
        text or brian2.Quantity representation of a value with unit

    Returns
    -------
    valstr : `str`
        string representation of LEMS unit
    """
    if float(valunit) == 0:
        return '0'
    if type(valunit) != str:
        valunit = str(valunit)
    return valunit.replace(' ', '*')


def read_nml_dims(nmlcdpath=""):
    """
    Read from `NeuroMLCoreDimensions.xml` all supported by LEMS
    dimensions and store it as a Python dict with name as a key
    and Brian2 unit as value.

    Parameters
    ----------
    nmlcdpath : `str`, optional
        Path to 'NeuroMLCoreDimensions.xml'

    Returns
    -------
    lems_dimenssions : `dict`
        Dictionary with LEMS dimensions.
    """
    path = os.path.join(nmlcdpath, "NeuroMLCoreDimensions.xml")
    domtree = minidom.parse(path)
    collection = domtree.documentElement
    dimsCollection = collection.getElementsByTagName("Dimension")
    order_dict = {"m": 1, "l": 0, "t": 2, "i": 3, "k": 4, "n": 5, "j": 6}
    lems_dimensions = dict()
    for dc in dimsCollection:
        name_ = dc.getAttribute("name")
        tmpdim_ = [0]*7  # 7 base dimensions
        for k in order_dict.keys():
            if dc.hasAttribute(k):
                tmpdim_[order_dict[k]] = int(dc.getAttribute(k))
        lems_dimensions[name_] = get_or_create_dimension(tmpdim_)
    return lems_dimensions


def read_nml_units(nmlcdpath=""):
    """
    Read from 'NeuroMLCoreDimensions.xml' all supported by LEMS
    units.

    Parameters
    ----------
    nmlcdpath : `str`, optional
        Path to 'NeuroMLCoreDimensions.xml'

    Returns
    -------
    lems_units : `list`
        List with LEMS units.
    """
    path = os.path.join(nmlcdpath, "NeuroMLCoreDimensions.xml")
    domtree = minidom.parse(path)
    collection = domtree.documentElement
    unitsCollection = collection.getElementsByTagName("Unit")
    lems_units = []
    for uc in unitsCollection:
        if uc.hasAttribute('symbol'):
            lems_units.append(uc.getAttribute('symbol'))
    return lems_units

########################################
# All NeuroML2 syntax creation helpers
########################################


class NeuroMLSimulation(object):
    '''
    NeuroMLSimulation class representing Simulation tag in NeuroML
    syntax as a XML DOM representation.
    '''
    def __init__(self, simid, target, length="1s", step="0.1ms"):
        '''
        NeuroMLSimulation object constructor.

        Parameters
        ----------
        simid : str
            simulation id.
        target : str
            target NeuroML object: component or network
        length : str, optional
            length of simulation, default 1 sec
        step : str, optional
            step of integration, default 0.1 ms
        '''
        self.doc = minidom.Document()
        self.create_simulation(simid, target, length, step)
        self.lines = {}
        self.displays = {}
        self._disp_idx = -1
        self.outcolumns = {}
        self.output_files = {}
        self._output_idx = -1
        self.eventselections = {}
        self.event_output_files = {}
        self._event_output_idx = -1

    def create_simulation(self, simid, target, length, step):
        """
        Adds a Simulation element to DOM structure at init.

        Parameters
        ----------
        simid : str
            simulation id.
        target : str
            target NeuroML object: component or network
        length : str, optional
            length of simulation, default 1 sec
        step : str, optional
            step of integration, default 0.1 ms
        """
        self.simulation = self.doc.createElement('Simulation')
        attributes = [("id", simid), ("target", target),
                      ("length", length), ("step", step)]
        for attr_name, attr_value in attributes:
            self.simulation.setAttribute(attr_name, attr_value)

    def update_simulation_attribute(self, attr_name, attr_value):
        """
        Updates simulation attributes.

        Parameters
        ----------
        attr_name : str
            attribute name
        attr_value : str or int or float
            attribute value
        """
        if not type(attr_value) is str:
            attr_value = str(attr_value)
        self.simulation.setAttribute(attr_name, attr_value)

    def add_display(self, dispid, title="", time_scale="1ms", xmin="0",
                                  xmax="1000", ymin="0", ymax="11"):
        """
        Adds a Display element to Simulation.

        Parameters
        ----------
        dispid : str
            display id
        title : str
            title printed on display window
        time_scale : str
            time scale of a plot
        xmin, xmax, ymin, ymax : str
            limits of plot
        """
        self._disp_idx += 1
        self.displays[self._disp_idx] = self.doc.createElement('Display')
        self.lines[self._disp_idx] = []
        attributes = [("id", dispid), ("title", title),
                      ("timeScale", time_scale), ("xmin", xmin),
                      ("xmax", xmax), ("ymin", ymin), ("ymax", ymax)]
        for attr_name, attr_value in attributes:
            self.displays[self._disp_idx].setAttribute(attr_name, attr_value)

    def add_line(self, linid, quantity, scale="1mV", time_scale="1ms"):
        """
        Adds a Line element to a recently added Display.

        Parameters
        ----------
        linid : str
            line id
        quantity : str
            measure to plot
        scale : str
            scale of a function
        time_scale : str
            time scale of a line
        """
        assert self.displays, "You need to add display first"
        line = self.doc.createElement('Line')
        attributes = [("id", linid), ("quantity", quantity),
                      ("scale", scale), ("timeScale", time_scale)]
        for attr_name, attr_value in attributes:
            line.setAttribute(attr_name, attr_value)
        self.lines[self._disp_idx].append(line)

    def add_outputfile(self, outfileid, filename="recordings.dat"):
        """
        Adds an OutputFile to Simulation.

        Parameters
        ----------
        outfileid : str
            OutputFile id
        filename : str
            name of an output file
        """
        self._output_idx += 1
        self.output_files[self._output_idx] = self.doc.createElement('OutputFile')
        self.outcolumns[self._output_idx] = []
        attributes = [("id", outfileid), ("fileName", filename)]
        for attr_name, attr_value in attributes:
            self.output_files[self._output_idx].setAttribute(attr_name, attr_value)

    def add_outputcolumn(self, ocid, quantity):
        """
        Adds an OutputColumn element to a recently added OutputFile tag.

        Parameters
        ----------
        ocid : str
            OutputColumn id
        quantity : str
            measure to store in a column
        """
        assert self.output_files, "You need to add output_files first"
        outputcolumn = self.doc.createElement('OutputColumn')
        attributes = [("id", ocid), ("quantity", quantity)]
        for attr_name, attr_value in attributes:
            outputcolumn.setAttribute(attr_name, attr_value)
        self.outcolumns[self._output_idx].append(outputcolumn)

    def add_eventoutputfile(self, outfileid, filename="recordings.spikes", format_="TIME_ID"):
        """
        Adds an EventOutputFile element to a recently added Display.

        Parameters
        ----------
        outfileid : str
            EventOutputFile id
        filename : str
            name of an output file
        format : str, optional
            format of data storage, default TIME_ID
        """
        self._event_output_idx += 1
        self.event_output_files[self._event_output_idx] = self.doc.createElement('EventOutputFile')
        self.eventselections[self._event_output_idx] = []
        attributes = [("id", outfileid), ("fileName", filename),
                      ("format", format_)]
        for attr_name, attr_value in attributes:
            self.event_output_files[self._event_output_idx].setAttribute(attr_name, attr_value)

    def add_eventselection(self, esid, select, event_port="spike"):
        """
        Adds an EventSelection element to a recently added EventOutputFile.

        Parameters
        ----------
        esid : str
            EventSelection id
        select : str
            index of selected neuron
        event_port : str
            event port name, default 'spike'
        """
        assert self.event_output_files, "You need to add EventOutputFile first"
        eventselection = self.doc.createElement('EventSelection')
        attributes = [("id", esid), ("select", select),
                      ("eventPort", event_port)]
        for attr_name, attr_value in attributes:
            eventselection.setAttribute(attr_name, attr_value)
        self.eventselections[self._event_output_idx].append(eventselection)

    def build(self):
        '''
        Builds NeuroML DOM structure of Simulation. It returns DOM
        object or it can be accessed by *object.simulation*.

        Returns
        -------
        simulation : xml.minidom.dom
            DOM representation of simulation.
        '''
        for k in self.displays:
            for line in self.lines[k]:
                self.displays[k].appendChild(line)
            self.simulation.appendChild(self.displays[k])
        for k in self.output_files:
            for outcol in self.outcolumns[k]:
                self.output_files[k].appendChild(outcol)
            self.simulation.appendChild(self.output_files[k])
        for k in self.event_output_files:
            for evsel in self.eventselections[k]:
                self.event_output_files[k].appendChild(evsel)
            self.simulation.appendChild(self.event_output_files[k])
        return self.simulation

    def __repr__(self):
        return self.simulation.toprettyxml('  ', '\n')


class NeuroMLSimpleNetwork(object):
    '''
    NeuroMLSimpleNetwork class representing network tag in NeuroML
    syntax as a XML DOM representation.
    '''
    def __init__(self, id_):
        '''
        NeuroMLSimpleNetwork object constructor.

        Parameters
        ----------
        simid : str
            network id.
        '''
        self.doc = minidom.Document()
        self.network = self.doc.createElement('network')
        self.network.setAttribute("id", id_)
        self.components = []

    def add_component(self, id_, type_, **attributes):
        '''
        Adds a component to a network.

        Parameters
        ----------
        id_ : str
            component id
        type_ : str
            type of component
        attributes : ..., optional
            more attributes
        '''
        component = self.doc.createElement('Component')
        component.setAttribute("id", id_)
        component.setAttribute("type", type_)
        for attr_name, attr_value in attributes.items():
            component.setAttribute(str(attr_name), str(attr_value))
        self.components.append(component)

    def build(self):
        '''
        Builds NeuroML DOM structure of network. It returns DOM
        object.

        Returns
        -------
        network : xml.minidom.dom
            DOM representation of network.
        '''
        for comp in self.components:
            self.network.appendChild(comp)
        return self.network

    def __repr__(self):
        return self.network.toprettyxml('  ', '\n')


class NeuroMLPoissonGenerator(object):
    '''
    Makes XML of spikeGeneratorPoisson for NeuroML2/LEMS simulation.
    '''
    def __init__(self, poissid, average_rate):
        '''
        NeuroMLPoissonGenerator object constructor.

        Parameters
        ----------
        poissid : str
            generator id
        average_rate : str or int
            average rate of firing in Hz
        '''
        self.doc = minidom.Document()
        self.generator = self.doc.createElement('spikeGeneratorPoisson')
        self.generator.setAttribute("id", poissid)
        if type(average_rate) == int:
            average_rate = str(average_rate) + ' Hz'
        if type(average_rate) == str:
            if not average_rate.split(' ')[-1] == 'Hz':
                average_rate += ' Hz'
        self.generator.setAttribute("averageRate", average_rate)

    def build(self):
        '''
        Builds NeuroML DOM structure of spikeGeneratorPoisson and returns it.

        Returns
        -------
        generator : xml.minidom.dom
            DOM representation of generator.
        '''
        return self.generator

    def __repr__(self):
        return self.generator.toprettyxml('  ', '\n')


class NeuroMLTarget(object):
    '''
    Makes XML of target of NeuroML2/LEMS simulation.
    '''
    def __init__(self, component):
        '''
        NeuroMLTarget object constructor.

        Parameters
        ----------
        component : str
            target component
        '''
        self.doc = minidom.Document()
        self.target = self.doc.createElement('Target')
        self.target.setAttribute("component", component)

    def build(self):
        '''
        Builds NeuroML DOM structure of target and returns it.

        Returns
        -------
        target : xml.minidom.dom
            DOM representation of target.
        '''
        return self.target

    def __repr__(self):
        return self.target.toprettyxml('  ', '\n')
