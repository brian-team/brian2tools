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
        expression = str_to_sympy(expression)
    if diff:
        # independent variable is always 't'
        t = symbols('t')
        expression = Derivative(expression, 't')
    rend_exp = latex(expression, mode='equation',
                    itex=True, long_frac_ratio = 2/2)
    return rend_exp


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
        md_str += bold('Run regularly: ') + endl
        for run_reg in neurongrp['run_regularly']:
            md_str += ('run_regularly() of name ' + run_reg['name'] +
                       'execute the code ' +
                       render_expression(str(run_reg['code'])) +
                       ' for every ' + str(run_reg['dt'])) + endl
    return md_str

def expand_identifier(ident_key, ident_value):
    ident_str = ''
    if type(ident_value) != dict:
            ident_str += (render_expression(str(ident_key)) + ": " +
                          render_expression(ident_value))
    else:
        ident_str += (render_expression(str(ident_key)) + 'of type ' +
                        ident_value['type'])
        if ident_value['type'] is 'timedarray':
            ident_str += ('with dimentsion' + str(ident_value['ndim']) +
                            ' and dt as ' + ident_value['dt'])
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
        if type(event_details['refractory']) != 'str':
            event_str += str(event_details['refractory'])
        else:
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
        rend_eqn =  render_expression(var, diff=True)
    elif equation['type'] == 'subexpression':
        rend_eqn =  render_expression(var)
    if 'expr' in equation:
        rend_eqn +=  '&#8592;' + render_expression(equation['expr'])
    rend_eqn += (", where unit of " + render_expression(var) +
                    " is " + str(equation['unit']))
    if 'flags' in equation:
        rend_eqn += (' and ' +
                        ', '.join(str(f) for f in equation['flags']) +
                        " as flag(s) associated.")
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
    if type(initializer['index']) == str:
        init_str += ' with condition ' + initializer['index']
    elif type(initializer['index']) == bool:
        if initializer['index']:
            init_str += ' to all indices '
        else:
            init_str += ' to no indices'
    else:
        init_str += ('to indices ' +
                     ','.join([str(ind) for ind in initializer['index']]))
    return init_str + endl

def expand_PoissonGroup():
    pass

def expand_SpikeGenerator():
    pass

def expand_StateMonitor():
    pass

def expand_SpikeMonitor():
    pass

def expand_EventMonitor():
    pass

def expand_PopulationRateMonitor():
    pass

def expand_Synapses():
    pass