import os, inspect, datetime
import brian2
from markdown_strings import (header, horizontal_rule, 
                              italics, unordered_list, bold)
from brian2.devices.device import all_devices
from brian2tools.baseexport.device import BaseExporter
from brian2.equations.equations import str_to_sympy
from sympy.printing import latex
from sympy.abc import *
from sympy import Derivative, symbols
import re
from expander import *

endl = '\n'

class MdExporter():
    """
    Build Markdown texts from run dictionary
    """
    def get_monitor_details(self, monitor):
        name = "- Name: " + ' ' + monitor['name'] + endl
        source = "- Monitor object: " + ' ' + monitor['source'] + endl
        var_mon = "- Monitor variables: " + ' ' + ','.join([self.render_expression(str_to_sympy(var)) for var in monitor['variables']]) + endl
        indices = "- Monitor indices: " + ' '
        if type(monitor['record']) == bool:
            if monitor['record'] == True:
                indices += " All indices" + endl
            else:
                indices += "No indices" + endl
        else:
            indices += ','.join([str(ind) for ind in monitor['record']]) + endl
        time_step = "- Time step of monitoring: " + ' ' + str(monitor['dt']) + endl
        monitor_details = name + source + var_mon + indices + time_step
        return monitor_details

    def expand_initializers(initializers):
        source = ''
        for initializer in initializers:
            source += '- Source group ' + initializer['source'] + ' initialized with '
            source += 'the value of '
            if type(initializer['value']) == str:
                source += self.render_expression(str_to_sympy(initializer['value']))
            else:
                source += str(initializer['value'])
            source += " to the variable " + self.render_expression(str_to_sympy(str(initializer['variable'])))

            if type(initializer['index']) == str:
                source += ' with condition ' + initializer['index']
            elif type(initializer['index']) == bool:
                if initializer['index']:
                    source += ' to all indices '
                else:
                    source += ' to no indices'
            else:
                source += 'to indices ' + ','.join([str(ind) for ind in initializer['index']])
            source += endl
        return source

    def create_md_string(self, net_dict):
        """
        Create markdown code from the standard dictionary
        """
        # details about network
        overall_string = header('Network details', 1) + endl
        n_runs = "run"
        if len(net_dict) > 1:
            n_runs += "s"
        overall_string += "The Network consists of {} \
                           simulation ".format(len(net_dict)) + (n_runs +
                           endl + horizontal_rule() + endl)
        
        # start going to the dictionary items in particular run instance
        for run_indx in range(len(net_dict)):
            # details about the particular run
            run_dict = net_dict[run_indx]
            run_string = ('Duration of simulation is ' + 
                           str(run_dict['duration']) + endl)
            # map expand functions for particular components
            func_map = {'neurongroup': {'f': expand_NeuronGroup,
                                        'h': 'NeuronGroup(s) '},
                       'poissongroup': expand_PoissonGroup,
                       'spikegeneratorgroup': expand_SpikeGenerator,
                       'statemonitor': expand_StateMonitor,
                       'spikemonitor': expand_SpikeMonitor,
                       'eventmonitor': expand_EventMonitor,
                       'populationratemonitor': expand_PopulationRateMonitor,
                       'synapses': expand_Synapses}
            # loop through the components
            for (obj_key, obj_list) in run_dict['components']:
                if obj_key in func_map.keys():
                    # loop through the members in list
                    run_string += (bold(func_map['obj_key']['h'] +
                                   'defined: ') + endl)
                    for obj_mem in obj_list:
                        run_string += func_map[obj_key](obj_mem)
            overall_string += run_string
            # loop through initializer_connectors
            # TODO: update the name
            for init_conn in run_dict['initializers']:
                
        self.md_text = overall_string

        return self.md_text


class Human_Readable(BaseExporter):
    """
    Device to export Human-readable format (markdown) from
    the Brian model. It derives from BaseExporter to use the
    dictionary representation of the model
    """

    def build(self, direct_call=True, debug=False, author=None,
              add_meta=False, output=None, format='std_dict', verbose=True):
        """
        Build the exporter

        Parameters
        ----------
        direct_call : bool
            To check whether build() was called directly
        debug : bool, optional
            To run in debug mode
        author : str, optional
            Author field to add in the metadata
        add_meta : bool, optional
            To attach meta field in output
        output : str, optional
            File name to write markdown script
        format : str, optional
            Format type to export markdown.
            Available formats: {std_dict, custom_dict, nordlie}
        verbose : bool, optional
            Whether to verbose within the components
        """
    
        # get source file name
        frame = inspect.stack()[1]
        user_file = inspect.getmodule(frame[0]).__file__
        date_time = datetime.datetime.now()
        brian_version = brian2.__version__
        # if author given
        if author:
            if type(author) != str:
                raise Exception('Author field should be string, \
                                 not {} type'.format(type(author)))
        else:
            author = '-'
        # prepare meta-data
        meta_data = italics('Filename: {}\
                             \nAuthor: {}\
                             \nDate and localtime: {}\
                             \nBrian version: {}'.format(user_file, author,
                             date_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                             brian_version)) + endl + horizontal_rule() + endl
        self.meta_data = meta_data
        # check filename
        if output:
            if type(output) != str:
                raise Exception('Output filename should be string, \
                                 not {} type'.format(type(author)))
        else:
            output = 'output'
        self.output = output
        # check the format of exporting
        self.format_options = {'std_dict', 'custom_dict', 'nordlie'}
        if format not in self.format_options:
            raise Exception('Unknown format options to export, valid formats \
                             are: std_dict, custom_dict, nordlie')
        self.format = format
        self.verbose = verbose
        # start creating markdown code
        md_exporter = MdExporter()
        self.md_text = md_exporter.create_md_string(self.runs)

        if debug:
            if add_meta:
                print(meta_data + self.md_text)
            else:
                print(self.md_text)
            

he_device = Human_Readable()
all_devices['heexport'] = he_device
