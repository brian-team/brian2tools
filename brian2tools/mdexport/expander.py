"""
Standard markdown expander class to expand Brian objects to
markdown text using standard dictionary representation of baseexport
"""
from brian2.equations.equations import str_to_sympy
from brian2 import Quantity
from sympy import Derivative, symbols
from sympy.printing import latex
from sympy.abc import *
from markdown_strings import *
import numpy as np
import re


endll = '\n\n'
endl = '\n'
tab = '\t'

def _check_plural(iterable, singular_word=None, allow_constants=True):
    count = 0
    singular_plural_dict = {'index': 'indices',
                            'property': 'properties'
    }
    if hasattr(iterable, '__iter__'):
        for _ in iterable:
            count += 1
            if count > 1:
                if singular_word:
                    try:
                        return singular_plural_dict[singular_word]
                    except:
                        raise Exception("The singular word is not found in \
                                         singular-plural dictionary.")
                return 's'
    elif not allow_constants:
        raise IndexError("Suppose to be iterable object \
                          but instance got {}".format(type(iterable)))
    return ''


def _prepare_math_statements(statements, differential=False,
                           seperate=False, equals='&#8592;'):

    rend_str = ''
    list_eqns = re.split(';|\n', statements)
    for statement in list_eqns:
        # bad way
        if seperate:

           if ('+=' in statement or '=' in statement or
               '-=' in statement):
    
                lhs, rhs = re.split('-=|\+=|=', statement)
                if '+=' in statement:
                    rend_str += (_render_expression(lhs) +
                                '+=' +_render_expression(rhs))
                else:
                    rend_str += (_render_expression(lhs) +
                                equals +  _render_expression(rhs))
        else:
            rend_str += _render_expression(statement, differential)
        rend_str += ', '

    return rend_str[:-2]


def _render_expression(expression, differential=False,
                       github_md=True):
    
    if isinstance(expression, Quantity):
        expression = str(expression)
    else:
        if not isinstance(expression, str):
            expression = str(expression)
        expression = str_to_sympy(expression)
    if differential:
        # independent variable is always 't'
        t = symbols('t')
        expression = Derivative(expression, 't')

    rend_exp = latex(expression, mode='equation',
                    itex=True, mul_symbol='.')
    # horrible thing
    rend_exp = rend_exp.replace('_placeholder_{arg}','-')
    rend_exp = rend_exp.replace('\operatorname','')

    if github_md:
        rend_exp = rend_exp[2:][:-2]
        git_rend_exp = (
        '<img src="https://render.githubusercontent.com/render/math?math=' +
        rend_exp + '">'
        )
        return git_rend_exp
    return rend_exp[1:][:-1]


class Std_mdexpander():

    """
    Build Markdown texts from run dictionary.
    The class contain various expand functions for corresponding Brian
    objects and get standard dictionary as argument to expand them with
    sentences in markdown format.

    Note
    ----
    If suppose the user would like to change the format or wordings in
    the exported model descriptions, one can derive from this standard
    markdown expander class to override the required changes in expand
    functions.
    """

    def create_md_string(self, net_dict):
        """
        Create markdown text by checking the standard dictionary and call
        required expand functions and arrange the descriptions
        """
        # get details about network runs
        overall_string = header('Network details', 1) + endl
        n_runs = 's'
        if len(net_dict) > 1:
            n_runs = ''
        # start header to mention about no. of total run simulations
        overall_string += ('The Network consist' + n_runs + ' of {} \
                           simulation run'.format(
                                                bold(len(net_dict))
                                                ) +
                           _check_plural(net_dict) +
                           endl + horizontal_rule() + endl)
        # start going to the dictionary items in particular run instance
        for run_indx in range(len(net_dict)):
            # details about the particular run
            run_dict = net_dict[run_indx]
            # start run header to say about duration
            if len(net_dict) > 1:
                run_string = (header('Run ' + str(run_indx + 1) + ' details', 3) +
                            endl)
            else:
                run_string = endl
            run_string += ('Duration of simulation is ' +
                            bold(str(run_dict['duration'])) + endll)
            # map expand functions for particular components
            func_map = {'neurongroup': {'f': self.expand_NeuronGroup,
                                        'h': 'NeuronGroup'},
                       'poissongroup': {'f': self.expand_PoissonGroup,
                                        'h': 'PoissonGroup'},
                       'spikegeneratorgroup':
                                    {'f': self.expand_SpikeGeneratorGroup,
                                     'h': 'SpikeGeneratorGroup'},
                       'statemonitor': {'f': self.expand_StateMonitor,
                                        'h': 'StateMonitor'},
                       'spikemonitor': {'f': self.expand_SpikeMonitor,
                                        'h': 'SpikeMonitor'},
                       'eventmonitor': {'f': self.expand_EventMonitor,
                                        'h': 'EventMonitor'},
                       'populationratemonitor':
                                        {'f': self.expand_PopulationRateMonitor,
                                         'h': 'PopulationRateMonitor'},
                       'synapses': {'f': self.expand_Synapses,
                                    'h': 'Synapse'},
                       'poissoninput': {'f': self.expand_PoissonInput,
                                         'h': 'PoissonInput'}}
            # loop through the components
            for (obj_key, obj_list) in run_dict['components'].items():
                # check the object component is in map
                if obj_key in func_map.keys():
                    # loop through the members in list
                    run_string += (bold(func_map[obj_key]['h'] +
                                   _check_plural(obj_list) + ' defined:') +
                                   endl)
                    # point out components
                    for obj_mem in obj_list:
                        run_string += '- ' + func_map[obj_key]['f'](obj_mem)
                run_string += endl
            # differentiate connectors and initializers from
            # `initializers_connectors`
            initializer = []
            connector = []
            # check if they are available, if so expand them
            if 'initializers_connectors' in run_dict:
                # loop through the members in list
                for init_cont in run_dict['initializers_connectors']:
                    if init_cont['type'] is 'initializer':
                        initializer.append(init_cont)
                    else:
                        connector.append(init_cont)
            if initializer:
                run_string += bold('Initializer' +
                                   _check_plural(initializer) +
                                   ' defined:') + endl
                # loop through the initits
                for initit in initializer:
                    run_string += '- ' + self.expand_initializer(initit)
            if connector:
                run_string += endl
                run_string += bold('Synaptic Connection' +
                                   _check_plural(connector) +
                                   ' defined:') + endl
                # loop through the connectors
                for connect in connector:
                    run_string += '- ' + self.expand_connector(connect)
            if 'inactive' in run_dict:
                run_string += endl
                run_string += (bold('Inactive member' + 
                               _check_plural(run_dict['inactive']) + ': ')
                               + endl)
                run_string += ', '.join(run_dict['inactive'])
            overall_string += run_string

        self.md_text = overall_string

        return self.md_text

    def expand_NeuronGroup(self, neurongrp):
        
        md_str = ''
        md_str += 'Name ' + bold(neurongrp['name']) + ', with \
                population size ' + bold(neurongrp['N']) + '.' + endll
        md_str += tab + bold('Dynamics:') + endll
        md_str += self.expand_equations(neurongrp['equations'])
        if neurongrp['user_method']:
            md_str += (tab + neurongrp['user_method'] +
                    ' method is used for integration' + endll)
        if 'events' in neurongrp:
            md_str += tab + bold('Events:') + endll
            md_str += self.expand_events(neurongrp['events'])
        if 'identifiers' in neurongrp:
            md_str += tab + bold('Constants:') + endll
            md_str += self.expand_identifiers(neurongrp['identifiers'])
        if 'run_regularly' in neurongrp:
            md_str += (tab + bold('Run regularly') + 
            _check_plural(neurongrp['run_regularly']) + ': ' + endll)
            for run_reg in neurongrp['run_regularly']:
                md_str += self.expand_runregularly(run_reg)

        return md_str

    def expand_identifier(self, ident_key, ident_value):
        ident_str = ''
        if type(ident_value) != dict:
                ident_str += (_render_expression(ident_key) + ": " +
                            _render_expression(ident_value))
        else:
            ident_str += (_render_expression(ident_key) + ' of type ' +
                            ident_value['type'])
            if ident_value['type'] is 'timedarray':
                ident_str += (' with dimentsion ' +
                            _render_expression(ident_value['ndim']) +
                            ' and dt as ' + _render_expression(ident_value['dt']))
        return ident_str + ', '

    def expand_identifiers(self, identifiers):

        idents_str = ''
        for key, value in identifiers.items():
            idents_str += self.expand_identifier(key, value)
        idents_str = tab + idents_str[:-2] + endll
        return idents_str

    def expand_event(self, event_name, event_details):
        event_str = ''
        event_str += tab + 'Event ' + bold(event_name) + ', '
        event_str += ('after ' +
                    _render_expression(event_details['threshold']['code']))
        if 'reset' in event_details:
            event_str += (', ' + 
                        _prepare_math_statements(
                                        event_details['reset']['code'],
                                        seperate=True)
                        )
        if 'refractory' in event_details:
            event_str += ', with refractory ' 
            event_str += _render_expression(event_details['refractory'])

        return event_str + endll

    def expand_events(self, events):
        events_str = ''
        for name, details in events.items():
            events_str += self.expand_event(name, details)
        return events_str

    def expand_equation(self, var, equation):
        rend_eqn = ''   
        if equation['type'] == 'differential equation':
            rend_eqn +=  _render_expression(var, differential=True)
        elif equation['type'] == 'subexpression':
            rend_eqn +=  _render_expression(var)
        else:
            rend_eqn += 'Parameter ' + _render_expression(var)
        if 'expr' in equation:
            rend_eqn +=  '&#8592;' + _render_expression(equation['expr'])
        rend_eqn += (", where unit of " + _render_expression(var) +
                        " is " + str(equation['unit']))
        if 'flags' in equation:
            rend_eqn += (' and ' + ', '.join(str(f) for f in equation['flags']) +
                        ' as flag' + _check_plural(equation['flags']) +
                        ' associated')
        return tab + rend_eqn + endll

    def expand_equations(self, equations):
        rend_eqns = ''
        for (var, equation) in equations.items():
            rend_eqns += self.expand_equation(var, equation)
        return rend_eqns

    def expand_initializer(self, initializer):

        init_str = ''
        init_str += ('Variable ' + _render_expression(initializer['variable']) +
                    ' of ' +  initializer['source'] + ' initialized with ' +
                    _render_expression(initializer['value']) 
                    )
        # TODO: not happy with this checking
        if (isinstance(initializer['index'], str) and 
        (initializer['index'] != 'True' and initializer['index'] != 'False')):
            init_str += ' on condition ' + initializer['index']
        elif (isinstance(initializer['index'], bool) or
            (initializer['index'] == 'True' or initializer['index'] == 'False')):
            if initializer['index'] or initializer['index'] == 'True':
                init_str += ' to all members'
            else:
                init_str += ' to no member'
        else:
            init_str += ' to member' + _check_plural(initializer['index']) + ' '
            if not hasattr(initializer['index'], '__iter___'):
                init_str += str(initializer['index'])
            else:
                init_str += ','.join([str(ind) for ind in initializer['index']])
        if 'identifiers' in initializer:
            init_str += ('. Identifier' +
                        _check_plural(initializer['identifiers']) +
                        ' associated: ' +
                        self.expand_identifiers(initializer['identifiers']))
        return init_str + endll

    def expand_connector(self, connector):
        con_str = ''
        con_str += ('Connection from ' + connector['source'] +
                    ' to ' + connector['target'])
        if 'i' in connector:
            con_str += ('. From source group ' +
                        _check_plural(connector['i'], 'index') + ': ')
            if not isinstance(connector['i'], str):
                if hasattr(connector['i'], '__iter__'):
                    con_str += ', '.join(str(ind) for ind in connector['i'])
                else:
                    con_str += str(connector['i'])
            else: 
                con_str += ' with generator syntax ' + connector['i']
            if 'j' in connector:
                con_str += (' to target group ' +
                            _check_plural(connector['j'], 'index') + ': ')
                if not isinstance(connector['j'], str):
                    if hasattr(connector['j'], '__iter__'):
                        con_str += ', '.join(str(ind) for ind in connector['j'])
                    else:
                        con_str += str(connector['j'])
                else: 
                    con_str += ' with generator syntax ' + connector['j']
            else:
                con_str += ' to all traget group members'

        elif 'j' in connector:
            con_str += '. Connection for all members in source group'
            if not isinstance(connector['j'], str):
                    con_str += (' to target group ' +
                            _check_plural(connector['j'], 'index') + ': ')
                    if hasattr(connector['j'], '__iter__'):
                        con_str += ', '.join(str(ind) for ind in connector['j'])
                    else:
                        con_str += str(connector['j'])
            else: 
                con_str += (' to target group with generator syntax ' +
                            connector['j'])

        elif 'condition' in connector:
            con_str += (' with condition ' +
                        _render_expression(connector['condition']))
        if connector['probability'] != 1:
            con_str += (', with probabilty ' +
                        _render_expression(connector['probability']))
        if connector['n_connections'] != 1:
            con_str += (', with number of connections ' +
                        _render_expression(connector['n_connections']))
        if 'identifiers' in connector:
            con_str += ('. Constants associated: ' +
                        self.expand_identifiers(connector['identifiers']))
        return con_str + endll

    def expand_PoissonGroup(self, poisngrp):
        md_str = ''
        md_str += (tab + 'Name ' + bold(poisngrp['name']) + ', with \
                population size ' + bold(poisngrp['N']) +
                ' and rate as ' + _render_expression(poisngrp['rates']) +
                '.' + endll)
        if 'identifiers' in poisngrp:
            md_str += tab + bold('Constants:') + endll
            md_str += self.expand_identifiers(poisngrp['identifiers'])
        if 'run_regularly' in poisngrp:
            md_str += tab + bold('Run regularly: ') + endll
            for run_reg in poisngrp['run_regularly']:
                md_str += self.expand_runregularly(run_reg)

        return md_str

    def expand_SpikeGeneratorGroup(self, spkgen):
        md_str = ''
        md_str += (tab + 'Name ' + bold(spkgen['name']) +
                ', with population size ' + bold(spkgen['N']) +
                ', has neuron' + _check_plural(spkgen['indices']) + ': ' +
                ', '.join(str(i) for i in spkgen['indices']) +
                ' that spike at times ' +
                ', '.join(str(t) for t in spkgen['times']) +
                ', with period ' + str(spkgen['period']) +
                '.' + endll)
        if 'run_regularly' in spkgen:
            md_str += tab + bold('Run regularly: ') + endll
            for run_reg in spkgen['run_regularly']:
                md_str += self.expand_runregularly(run_reg)

        return md_str

    def expand_StateMonitor(self, statemon):
        md_str = ''
        md_str += (tab + 'Monitors variable' + 
                _check_plural(statemon['variables']) + ': ' +
                ','.join(
                    [_render_expression(var) for var in statemon['variables']]
                        ) +
                ' of ' + statemon['source'])
        if isinstance(statemon['record'], bool):
            if statemon['record']:
                md_str += ' for all members'
        else:
            # another horrible hack (before with initializers)
            if not statemon['record'].size:
                md_str += ' for no member'
            else:
                md_str += (', for member' + _check_plural(statemon['record']) +
                        ': ' +
                        ','.join([str(ind) for ind in statemon['record']]) +
                        '.' + endll)
        return md_str

    def expand_SpikeMonitor(self, spikemon):
        return self.expand_EventMonitor(spikemon)

    def expand_EventMonitor(self, eventmon):
        md_str = ''
        md_str += (tab + 'Monitors variable' +
                _check_plural(eventmon['variables']) + ': ' +
                ','.join(
                    [_render_expression(var) for var in eventmon['variables']]
                    ) +
                ' of ' + eventmon['source'] + '.')
        if isinstance(eventmon['record'], bool):
            if eventmon['record']:
                md_str += ' for all members'
        else:
            # another horrible hack (before with initializers)
            if not eventmon['record'].size:
                md_str += ' for no member'
            else:
                md_str += (', for member' + _check_plural(eventmon['record']) +
                        ': ' +
                        ','.join([str(ind) for ind in eventmon['record']]))
        md_str += (' when event ' + bold(eventmon['event']) +
                    ' is triggered.' + endll)
        return md_str

    def expand_PopulationRateMonitor(self, popratemon):
        md_str = ''
        md_str += (tab + 'Monitors the population of ' + popratemon['source'] +
                '.' + endll)
        return md_str

    def expand_pathway(self, pathway):
        md_str = (tab + 'On ' + bold(pathway['prepost']) +
                ' of event ' + pathway['event'] + ' statements: ' +
                _prepare_math_statements(pathway['code'], seperate=True) +
                ' executed'
                )
        if 'delay' in pathway:
            md_str += (', with synaptic delay of ' +
                    _render_expression(pathway['delay']))

        return md_str + endll

    def expand_pathways(self, pathways):
        path_str = ''
        for pathway in pathways:
            path_str += self.expand_pathway(pathway)
        return path_str

    def expand_summed_variable(self, sum_variable):
        md_str = (tab + 'Updates target group ' + sum_variable['target'] +
                ' with statement: ' + _render_expression(sum_variable['code']) +
                endll)
        return md_str

    def expand_summed_variables(self, sum_variables):
        sum_var_str = ''
        for sum_var in sum_variables:
            sum_var_str += self.expand_summed_variable(sum_var)
        return sum_var_str

    def expand_Synapses(self, synapse):
        md_str = ''
        md_str += (tab + 'From ' + synapse['source'] +
                ' to ' + synapse['target'] + endll
                )
        if 'equations' in synapse:
            md_str += tab + bold('Dynamics:') + endll
            md_str += tab + self.expand_equations(synapse['equations'])
            if 'user_method' in synapse:
                md_str += (tab + synapse['user_method'] + 
                    ' method is used for integration' + endll)
        if 'pathways' in synapse:
            md_str += tab + bold('Pathways:') + endll
            md_str += self.expand_pathways(synapse['pathways'])
        if 'summed_variables' in synapse:
            md_str += tab + bold('Summed variables: ') + endll
            md_str += self.expand_summed_variables(synapse['summed_variables'])
        if 'identifiers' in synapse:
            md_str += tab + bold('Constants:') + endll
            md_str += self.expand_identifiers(synapse['identifiers'])
        return md_str

    def expand_PoissonInput(self, poinp):
        md_str = ''
        md_str += (tab + 'PoissonInput with size ' + bold(poinp['N']) +
                ' gives input to variable ' +
                _render_expression(poinp['target_var']) +
                ' with rate ' + _render_expression(poinp['rate']) +
                ' and weight of ' + _render_expression(poinp['weight']) +
                endll)
        if 'identifiers' in poinp:
            md_str += tab + bold('Constants:') + endll
            md_str += self.expand_identifiers(poinp['identifiers'])
        return md_str

    def expand_runregularly(self, run_reg):
        md_str = (tab + 'For every ' +  _render_expression(run_reg['dt']) +
                ' code: ' +
                    _prepare_math_statements(run_reg['code'], seperate=True) +
                    ' will be executed' + endll)
        return md_str
