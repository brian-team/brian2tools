import os, inspect, datetime
import brian2
from markdown_strings import header, horizontal_rule, italics, unordered_list, bold
from brian2.devices.device import all_devices
from brian2tools.baseexport.device import BaseExporter
from brian2.equations.equations import str_to_sympy
from sympy.printing import latex
from sympy.abc import *
from sympy import Derivative, symbols
import re

endl = '\n'

def _equation_separator(equation):
    """
    Separates *equation* (str) to LHS and RHS.
    """
    try:
        lhs, rhs = re.split('<=|>=|==|=|>|<', equation)
    except ValueError:
        return None
    return lhs.strip(), rhs.strip()

class MdExporter():
    """
    Build Markdown texts from run dictionary
    """
    def render_expression(self, expression, diff=False):
        if diff:
            # independent variable is always 't'
            t = symbols('t')
            expression = Derivative(expression, 't')
        rend_exp = latex(expression, mode='equation',
                        itex=True, long_frac_ratio = 2/2)
        return rend_exp

    def generate_network_summary(self, run_dict):
        #TODO: add network name
        heading = header("Network details", 1) + endl
        runs = " runs"
        if len(run_dict) == 1:
            runs = " run"
        network_summary = heading + "The Network consists of {} simulation".format(len(run_dict)) + runs + endl + horizontal_rule() + endl
        return network_summary

    def generate_run_summary(self, single_run, run_indx):
        #TODO: add step size
        heading = header("Simulation run {} details".format(run_indx + 1), 3) + endl
        run_summary = heading + "Simulated for the duration of {}".format(str(single_run['duration'])) + endl
        return run_summary
        
    def generate_model_equations(self, equations):

        rendered_eqns = []

        for (var, equation) in equations.items():

            var = str_to_sympy(var)

            if equation['type'] == 'differential equation':
                rend_eqn =  self.render_expression(var, diff=True)
            elif equation['type'] == 'subexpression':
                rend_eqn =  self.render_expression(var)
            if 'expr' in equation:
                rend_eqn +=  '=' + self.render_expression(str_to_sympy(equation['expr']))
            rend_eqn += ", where unit of " + self.render_expression(var) + " is " + str(equation['unit'])
            if 'flags' in equation:
                rend_eqn += ", flags associated " + equation['flags']
            rend_eqn += endl
            rendered_eqns.append(rend_eqn)

        return ''.join(rendered_eqns)

    def generate_model_identifiers(self, identifiers):

        rend_identifiers = []
        for var, value in identifiers.items():
            rend_identifiers.append(self.render_expression(str_to_sympy(var)) + ' = ' + self.render_expression(str(value)) + endl)
        return ''.join(rend_identifiers)

    def generate_event_details(self, events):
        event_details = ''
        for event_name, details in events.items():
            event_details += '- Event named ' + event_name + ' trigerred when ' + self.render_expression(str_to_sympy(details['threshold']['code']))
            if 'reset' in details:
                lhs, rhs = _equation_separator(details['reset']['code'])
                event_details += ' and after event ' + self.render_expression(str_to_sympy(lhs)) + ' = ' + self.render_expression(str_to_sympy(rhs))
            if 'refractory' in details:
                if type(details['refractory']) != 'str':
                    event_details += ' with refractory for ' + str(details['refractory']) + endl
                else:
                    event_details += ' with refractory for ' + self.render_expression(str_to_sympy((details['refractory']))) + endl

        return event_details

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

    def get_initializers_details(self, initializers):
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

    def get_neurongroup_details(self, neurongroup):
        
        name = "- Name: " + ' ' + neurongroup['name'] + endl
        size = "- Population size: " + ' ' + str(neurongroup['N']) + endl
        model_eqn = "- Model Equations:" + endl + self.generate_model_equations(neurongroup['equations']) + endl
        properties = ''
        if 'identifiers' in neurongroup:
            properties += "- Properties:" + endl + self.generate_model_identifiers(neurongroup['identifiers'])
        events = ''
        if 'events' in neurongroup:
            events += "- Events associated:"  + endl + self.generate_event_details(neurongroup['events'])

        neuron_details = name + size + model_eqn + properties + events + endl
        return neuron_details

    def generate_run_components(self, single_run):
        
        if 'neurongroup' in single_run['components']:
            neurongroup = single_run['components']['neurongroup']
            neuron_details = [header("Neuronal models defined", 5) + endl]
            for neuron_count in range(len(single_run['components']['neurongroup'])):
                neuron_heading = header("NeuronGroup {} details".format(neuron_count), 6) + endl
                neuron_detail = self.get_neurongroup_details(neurongroup[neuron_count])
                neuron_details.append(neuron_heading + neuron_detail)
        
        if 'statemonitor' in single_run['components']:
            statemonitor = single_run['components']['statemonitor']
            statemon_details = [header("StateMonitors defined", 5) + endl]
            for statemon_count in range(len(single_run['components']['statemonitor'])):
                statemon_heading = header("StateMonitor {} details".format(statemon_count), 6) + endl
                statemon_detail = self.get_monitor_details(statemonitor[statemon_count])
                statemon_details.append(statemon_heading + statemon_detail)

        initializers_details = ''
        if 'initializers' in single_run:
            initializers_details = header("On starting", 5) + endl
            initializers_details += self.get_initializers_details(single_run['initializers'])

        return ''.join(neuron_details) + ''.join(statemon_details) + initializers_details

    def create_md_string(self, run_dict):

        network_summary = self.generate_network_summary(run_dict)

        run_summary = []
        run_components = []
        run_onstart = []
        run_inactive = []

        for run_indx in range(len(run_dict)):
            single_run_summary = self.generate_run_summary(run_dict[run_indx], run_indx)
            single_run_components = self.generate_run_components(run_dict[run_indx])

        self.md_text = ''.join(network_summary + single_run_summary + single_run_components)

        return self.md_text


class Human_ReadableDevice(BaseExporter):
    """
    Device to export Human-readable format (markdown) from
    the Brian model
    It derives from BaseExporter to use the dictionary representation
    of the model
    """

    def build(self, direct_call=True, debug=False, author=None, add_meta=False):
        """
        Build the exporter 

        Parameters
        ----------
        direct_call : bool
            To check whether build() was called directly
        debug : bool
            To run in debug mode
        author : str
            Author field to add in the metadata
        """
        frame = inspect.stack()[1]
        user_file = inspect.getmodule(frame[0]).__file__
        date_time = datetime.datetime.now()
        brian_version = brian2.__version__

        if author:
            if type(author) != str:
                raise Exception('Invalid data type for author')
        else:
            author = '-'

        meta_data = italics('Filename: {} \nAuthor: {} \nDate and localtime: {} \nBrian version: {}'.format(user_file, author,
                                                        date_time.strftime('%Y-%m-%d %H:%M:%S %Z'), brian_version)) + endl + horizontal_rule() + endl
        md_exporter = MdExporter()
        self.md_text = md_exporter.create_md_string(self.runs)

        if debug:
            if add_meta:
                print(meta_data + self.md_text)
            else:
                print(self.md_text)
            

he_device = Human_ReadableDevice()
all_devices['heexport'] = he_device
