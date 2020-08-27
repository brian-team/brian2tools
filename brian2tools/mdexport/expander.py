"""
Expander functions of Brian objects used to expand
to markdown text from standard dictionary representation
"""
from markdown_strings import (header, horizontal_rule, 
                              italics, unordered_list, bold)
from sympy.printing import latex
from sympy.abc import *
from sympy import Derivative, symbols
from brian2.equations.equations import str_to_sympy
from brian2 import Quantity
import re
import numpy as np

endl = '\n\n'
tab = '\t'

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


def expand_runregularly(run_reg):
    md_str = (tab + 'For every ' +  _render_expression(run_reg['dt']) +
              ' code: ' +
                _prepare_math_statements(run_reg['code'], seperate=True) +
                ' will be executed' + endl)
    return md_str


def expand_NeuronGroup(neurongrp):
    
    md_str = ''
    md_str += 'Name ' + bold(neurongrp['name']) + ', with \
               population size ' + bold(neurongrp['N']) + '.' + endl
    md_str += tab + bold('Dynamics:') + endl
    md_str += expand_equations(neurongrp['equations'])
    if neurongrp['user_method']:
        md_str += (tab + neurongrp['user_method'] +
                   ' method is used for integration' + endl)
    if 'events' in neurongrp:
        md_str += tab + bold('Events:') + endl
        md_str += expand_events(neurongrp['events'])
    if 'identifiers' in neurongrp:
        md_str += tab + bold('Properties:') + endl
        md_str += expand_identifiers(neurongrp['identifiers'])
    if 'run_regularly' in neurongrp:
        md_str += tab + bold('Run regularly(s): ') + endl
        for run_reg in neurongrp['run_regularly']:
            md_str += expand_runregularly(run_reg)

    return md_str


def expand_identifier(ident_key, ident_value):
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


def expand_identifiers(identifiers):

    idents_str = ''
    for key, value in identifiers.items():
        idents_str += expand_identifier(key, value)
    idents_str = tab + idents_str[:-2] + endl
    return idents_str


def expand_event(event_name, event_details):
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

    return event_str + endl


def expand_events(events):
    events_str = ''
    for name, details in events.items():
        events_str += expand_event(name, details)
    return events_str


def expand_equation(var, equation):
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
        rend_eqn += (' and ' +
                        ', '.join(str(f) for f in equation['flags']) +
                        " as flag(s) associated")
    return tab + rend_eqn + endl


def expand_equations(equations):
    rend_eqns = ''
    for (var, equation) in equations.items():
        rend_eqns += expand_equation(var, equation)
    return rend_eqns


def expand_initializer(initializer):

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
            init_str += ' to all members '
        else:
            init_str += ' to no members'
    else:
        init_str += ' to member(s) '
        if not hasattr(initializer['index'], '__iter___'):
            init_str += str(initializer['index'])
        else:
            init_str += ','.join([str(ind) for ind in initializer['index']])
    if 'identifiers' in initializer:
        init_str += ('. Identifier(s) associated: ' +
                      expand_identifiers(initializer['identifiers']))
    return init_str + endl


def expand_connector(connector):
    con_str = ''
    con_str += ('Connection from ' + connector['source'] +
                ' to ' + connector['target'])
    if 'i' in connector:
        con_str += '. From source group indices: '
        if not isinstance(connector['i'], str):
            if hasattr(connector['i'], '__iter__'):
                con_str += ', '.join(str(ind) for ind in connector['i'])
            else:
                con_str += str(connector['i'])
        else: 
            con_str += ' with generator syntax ' + connector['i']
        if 'j' in connector:
            con_str += ' to target group indices: '
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
                con_str += ' to target group indices: '
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
        con_str += ('. Identifier(s) associated: ' +
                      expand_identifiers(connector['identifiers']))
    return con_str + endl


def expand_PoissonGroup(poisngrp):
    md_str = ''
    md_str += (tab + 'Name ' + bold(poisngrp['name']) + ', with \
               population size ' + bold(poisngrp['N']) +
               ' and rate as ' + _render_expression(poisngrp['rates']) +
               '.' + endl)
    if 'identifiers' in poisngrp:
        md_str += tab + bold('Properties:') + endl
        md_str += expand_identifiers(poisngrp['identifiers'])
    if 'run_regularly' in poisngrp:
        md_str += tab + bold('Run regularly: ') + endl
        for run_reg in poisngrp['run_regularly']:
            md_str += expand_runregularly(run_reg)

    return md_str


def expand_SpikeGeneratorGroup(spkgen):
    md_str = ''
    md_str += (tab + 'Name ' + bold(spkgen['name']) +
               ', with population size ' + bold(spkgen['N']) +
               ', has neuron(s) ' +
               ', '.join(str(i) for i in spkgen['indices']) +
               ' that spike at times ' +
               ', '.join(str(t) for t in spkgen['times']) +
               ', with period ' + str(spkgen['period']) +
               '.' + endl)
    if 'run_regularly' in spkgen:
        md_str += tab + bold('Run regularly: ') + endl
        for run_reg in spkgen['run_regularly']:
            md_str += expand_runregularly(run_reg)

    return md_str


def expand_StateMonitor(statemon):
    md_str = ''
    md_str += (tab + 'Monitors variable(s): ' +
               ','.join([_render_expression(var) for var in statemon['variables']]) +
               ' of ' + statemon['source'])
    if isinstance(statemon['record'], bool):
        if statemon['record']:
            md_str += ' for all members'
    else:
        # another horrible hack (before with initializers)
        if not statemon['record'].size:
            md_str += ' for no member'
        else:
            md_str += (', for member(s): ' +
                       ','.join([str(ind) for ind in statemon['record']]))

    md_str += (' with time step ' +
                 _render_expression(statemon['dt']) +
                 '.' + endl)
    return md_str


def expand_SpikeMonitor(spikemon):
    return expand_EventMonitor(spikemon)


def expand_EventMonitor(eventmon):
    md_str = ''
    md_str += (tab + 'Monitors variable(s): ' +
               ','.join([_render_expression(var) for var in eventmon['variables']]) +
               ' of ' + eventmon['source'] + '.')
    if isinstance(eventmon['record'], bool):
        if eventmon['record']:
            md_str += ' for all members'
    else:
        # another horrible hack (before with initializers)
        if not eventmon['record'].size:
            md_str += ' for no member'
        else:
            md_str += (', for member(s): ' +
                       ','.join([str(ind) for ind in eventmon['record']]))
    md_str += (' with time step ' +
                 _render_expression(eventmon['dt']) +
                 ' when event ' + bold(eventmon['event']) +
                 ' is triggered.' + endl)
    return md_str


def expand_PopulationRateMonitor(popratemon):
    md_str = ''
    md_str += (tab + 'Monitors the population of ' + popratemon['source'] + 
               ', with time step ' + _render_expression(popratemon['dt']) +
               endl)
    return md_str


def expand_pathway(pathway):
    md_str = (tab + 'On ' + bold(pathway['prepost']) +
             ' of event ' + pathway['event'] + ' statement(s): ' +
              _prepare_math_statements(pathway['code'], seperate=True) +
              ' is executed'
             )
    if 'delay' in pathway:
        md_str += (', with synaptic delay of ' +
                   _render_expression(pathway['delay']))

    return md_str + endl


def expand_pathways(pathways):
    path_str = ''
    for pathway in pathways:
        path_str += expand_pathway(pathway)
    return path_str


def expand_summed_variable(sum_variable):
    md_str = (tab + 'Updates target group ' + sum_variable['target'] +
              ' with statement: ' + _render_expression(sum_variable['code']) +
              endl)
    return md_str


def expand_summed_variables(sum_variables):
    sum_var_str = ''
    for sum_var in sum_variables:
        sum_var_str += expand_summed_variable(sum_var)
    return sum_var_str


def expand_Synapses(synapse):
    md_str = ''
    md_str += (tab + 'From ' + synapse['source'] +
               ' to ' + synapse['target'] + endl
               )
    if 'equations' in synapse:
        md_str += tab + bold('Dynamics:') + endl
        md_str += tab + expand_equations(synapse['equations'])
        if 'user_method' in synapse:
            md_str += (tab + synapse['user_method'] + 
                   ' method is used for integration' + endl)
    if 'pathways' in synapse:
        md_str += tab + bold('Pathways:') + endl
        md_str += expand_pathways(synapse['pathways'])
    if 'summed_variables' in synapse:
        md_str += tab + bold('Summed variables: ') + endl
        md_str += expand_summed_variables(synapse['summed_variables'])
    if 'identifiers' in synapse:
        md_str += tab + bold('Properties:') + endl
        md_str += expand_identifiers(synapse['identifiers'])
    return md_str


def expand_PoissonInput(poinp):
    md_str = ''
    md_str += (tab + 'PoissonInput with size ' + bold(poinp['N']) +
               ' gives input to variable ' +
               _render_expression(poinp['target_var']) +
               ' with rate ' + _render_expression(poinp['rate']) +
               ' and weight of ' + _render_expression(poinp['weight']) +
               endl)
    if 'identifiers' in poinp:
        md_str += tab + bold('Properties:') + endl
        md_str += expand_identifiers(poinp['identifiers'])
    return md_str
