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


def render_expression(expression, diff=False):
    if isinstance(expression, Quantity):
        expression = str(expression)
    else:
        if not isinstance(expression, str):
            expression = str(expression)
        expression = str_to_sympy(expression)
    if diff:
        # independent variable is always 't'
        t = symbols('t')
        expression = Derivative(expression, 't')
    rend_exp = latex(expression, mode='equation',
                    itex=True, long_frac_ratio = 2/2)
    return rend_exp


def expand_runregularly(run_reg):
    lhs, rhs = _equation_separator(run_reg['code'])
    md_str = ('run_regularly of name ' + run_reg['name'] +
                ' execute the code ' +
                render_expression(lhs) + '&#8592;' +
                render_expression(rhs) +
                ' for every ' + render_expression(run_reg['dt']) + endl)
    return md_str


def expand_NeuronGroup(neurongrp):
    
    md_str = ''
    md_str += 'Neurongroup of name ' + bold(neurongrp['name']) + ', with \
               population size ' + bold(neurongrp['N']) + '.' + endl
    md_str += bold('Dynamics:') + endl
    md_str += expand_equations(neurongrp['equations'])
    if neurongrp['user_method']:
        md_str += (neurongrp['user_method'] + 
                   ' method is used for integration' + endl)
    if 'events' in neurongrp:
        md_str += bold('Events:') + endl
        md_str += expand_events(neurongrp['events'])
    if 'identifiers' in neurongrp:
        md_str += bold('Properties:') + endl
        md_str += expand_identifiers(neurongrp['identifiers'])
    if 'run_regularly' in neurongrp:
        md_str += bold('Run regularly(s): ') + endl
        for run_reg in neurongrp['run_regularly']:
            md_str += expand_runregularly(run_reg)

    return md_str


def expand_identifier(ident_key, ident_value):
    ident_str = ''
    if type(ident_value) != dict:
            ident_str += (render_expression(ident_key) + ": " +
                          render_expression(ident_value))
    else:
        ident_str += (render_expression(ident_key) + ' of type ' +
                        ident_value['type'])
        if ident_value['type'] is 'timedarray':
            ident_str += (' with dimentsion ' +
                          render_expression(ident_value['ndim']) +
                          ' and dt as ' + render_expression(ident_value['dt']))
    return ident_str + ', '


def expand_identifiers(identifiers):

    idents_str = ''
    for key, value in identifiers.items():
        idents_str += expand_identifier(key, value)
    idents_str = idents_str[:-2] + endl
    return idents_str


def expand_event(event_name, event_details):
    event_str = ''
    event_str += 'Event ' + bold(event_name) + ', '
    event_str += ('after ' +
                   render_expression(event_details['threshold']['code']))
    if 'reset' in event_details:
        lhs, rhs = _equation_separator(event_details['reset']['code'])
        event_str += (', ' + render_expression(lhs) + '&#8592;' +
                        render_expression(rhs))
    if 'refractory' in event_details:
        event_str += ', with refractory ' 
        event_str += render_expression(event_details['refractory'])

    return event_str + endl


def expand_events(events):
    events_str = ''
    for name, details in events.items():
        events_str += expand_event(name, details)
    return events_str


def expand_equation(var, equation):
    rend_eqn = ''   
    if equation['type'] == 'differential equation':
        rend_eqn +=  render_expression(var, diff=True)
    elif equation['type'] == 'subexpression':
        rend_eqn +=  render_expression(var)
    else:
        rend_eqn += 'Parameter ' + render_expression(var)
    if 'expr' in equation:
        rend_eqn +=  '&#8592;' + render_expression(equation['expr'])
    rend_eqn += (", where unit of " + render_expression(var) +
                    " is " + str(equation['unit']))
    if 'flags' in equation:
        rend_eqn += (' and ' +
                        ', '.join(str(f) for f in equation['flags']) +
                        " as flag(s) associated")
    return rend_eqn + endl


def expand_equations(equations):
    rend_eqns = ''
    for (var, equation) in equations.items():
        rend_eqns += expand_equation(var, equation)
    return rend_eqns


def expand_initializer(initializer):

    init_str = ''
    init_str += ('Source group ' + initializer['source'] + ' initialized \
                  with the value of ' +
                  render_expression(initializer['value']) +
                  " to the variable " +
                  render_expression(initializer['variable']))
    # TODO: not happy with this checking
    if (isinstance(initializer['index'], str) and 
       (initializer['index'] != 'True' and initializer['index'] != 'False')):
        init_str += ' with condition ' + initializer['index']
    elif (isinstance(initializer['index'], bool) or
         (initializer['index'] == 'True' or initializer['index'] == 'False')):
        if initializer['index'] or initializer['index'] == 'True':
            init_str += ' to all members '
        else:
            init_str += ' to no members'
    else:
        init_str += (' to member(s) ' +
                     ','.join([str(ind) for ind in initializer['index']]))
    if 'identifiers' in initializer:
        init_str += endl
        init_str += ('Identifier(s) associated: ' +
                      expand_identifiers(initializer['identifiers']))
    return init_str + endl


def expand_connector(connector):
    con_str = ''
    con_str += ('Synaptic connection from ' + connector['source'] +
                ' to ' + connector['target'])
    if 'i' in connector:
        con_str += '. Connection from source group indices: '
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
                    render_expression(connector['condition']))
    if connector['probability'] != 1:
        con_str += (', with probabilty ' +
                    render_expression(connector['probability']))
    if connector['n_connections'] != 1:
         con_str += (', with number of connections ' +
                     render_expression(connector['n_connections']))
    if 'identifiers' in connector:
        con_str += endl
        con_str += ('Identifier(s) associated: ' +
                      expand_identifiers(connector['identifiers']))
    return con_str + endl


def expand_PoissonGroup(poisngrp):
    md_str = ''
    md_str += ('PoissonGroup of name ' + bold(poisngrp['name']) + ', with \
               population size ' + bold(poisngrp['N']) +
               ' and rate as ' + render_expression(poisngrp['rates']) +
               '.' + endl)
    if 'identifiers' in poisngrp:
        md_str += bold('Properties:') + endl
        md_str += expand_identifiers(poisngrp['identifiers'])
    if 'run_regularly' in poisngrp:
        md_str += bold('Run regularly: ') + endl
        for run_reg in poisngrp['run_regularly']:
            md_str += expand_runregularly(run_reg)

    return md_str


def expand_SpikeGeneratorGroup(spkgen):
    md_str = ''
    md_str += ('SpikeGeneratorGroup of name ' + bold(spkgen['name']) +
               ', with population size ' + bold(spkgen['N']) +
               ', has neurons ' +
               ', '.join(str(i) for i in spkgen['indices']) +
               ' that spike at times ' +
               ', '.join(str(t) for t in spkgen['times']) +
               ', with period(s)  ' + render_expression(spkgen['period']) +
               #', '.join(render_expression(p) for p in spkgen['period']) +
               '.' + endl)
    if 'run_regularly' in spkgen:
        md_str += bold('Run regularly: ') + endl
        for run_reg in spkgen['run_regularly']:
            md_str += expand_runregularly(run_reg)

    return md_str


def expand_StateMonitor(statemon):
    md_str = ''
    md_str += ('StateMonitor of name ' + bold(statemon['name']) +
               ' monitors variable(s) ' +
               ','.join([render_expression(var) for var in statemon['variables']]) +
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

    md_str += (' in time step ' +
                 render_expression(statemon['dt']) +
                 '.' + endl)
    return md_str


def expand_SpikeMonitor(spikemon):
    return expand_EventMonitor(spikemon)


def expand_EventMonitor(eventmon):
    md_str = ''
    md_str += ('SpikeMonitor of name ' + eventmon['name'] +
               ' monitors variable(s) ' +
               ','.join([render_expression(var) for var in eventmon['variables']]) +
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
    md_str += (' in time step ' +
                 render_expression(eventmon['dt']) +
                 ' when event ' + bold(eventmon['event']) +
                 ' is triggered.' + endl)
    return md_str


def expand_PopulationRateMonitor(popratemon):
    md_str = ''
    md_str += ('PopulationRateMonitor of name ' + bold(popratemon['name']) +
               ' monitors the population of ' + popratemon['source'] + ','+
               ' for time step ' + render_expression(popratemon['dt']) + '.' +
               endl)
    return md_str    

def expand_pathway(pathway):
    md_str = ('Pathway of name ' + pathway['name'] +' with type ' +
               bold(pathway['prepost']) + ' from ' + pathway['source'] +
               ' to ' + pathway['target'] + ', ' + 'runs statement(s) ' +
               pathway['code'] + 'for event ' + pathway['event'])
    if 'delay' in pathway:
        md_str += (' and with synaptic delay of ' + 
        render_expression(pathway['delay']))
    return md_str + endl

def expand_pathways(pathways):
    path_str = ''
    for pathway in pathways:
        path_str += expand_pathway(pathway)
    return path_str

def expand_summed_variable(sum_variable):
    md_str = ('Summed variable of name ' + sum_variable['name'] +
              ' that updates target group ' + sum_variable['target'] +
              ' with statement' + render_expression(sum_variable['code'])
             )
    return md_str

def expand_summed_variables(sum_variables):
    sum_var_str = ''
    for sum_var in sum_variables:
        sum_var_str += expand_summed_variable(sum_var)
    return sum_var_str


def expand_Synapses(synapse):
    md_str = ''
    md_str += ('Synapses of name: ' + synapse['name'] +
               ' with projection from ' + synapse['source'] +
               ' to ' + synapse['target'] + endl
               )
    if 'equations' in synapse:
        md_str += bold('Dynamics:') + endl
        md_str += expand_equations(synapse['equations'])
        if 'user_method' in synapse:
            md_str += (synapse['user_method'] + 
                   ' method is used for integration' + endl)
    if 'pathways' in synapse:
        md_str += bold('Pathways:') + endl
        md_str += expand_pathways(synapse['pathways'])
    if 'summed_variables' in synapse:
        md_str += bold('Summed variables: ') + endl
        md_str += expand_summed_variables(synapse['summed_variables'])
    if 'identifiers' in synapse:
        md_str += bold('Properties:') + endl
        md_str += expand_identifiers(synapse['identifiers'])
    return md_str


def expand_PoissonInput(poinp):
    md_str = ''
    md_str += ('PoissonInput of name ' + poinp['name'] + ', with \
               size ' + bold(poinp['N']) +
               ' gives input to variable ' +
               render_expression(poinp['target_var']) +
               ' with rate ' + render_expression(poinp['rate']) +
               ' and weight of ' + render_expression(poinp['weight']) +
               endl)
    if 'identifiers' in poinp:
        md_str += bold('Properties:') + endl
        md_str += expand_identifiers(poinp['identifiers'])
    return md_str
