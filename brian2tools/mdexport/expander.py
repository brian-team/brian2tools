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
    return md_str + endl


def expand_identifiers(identifiers):
    ident_str = ''
    for key, value in identifiers.items():
        if type(value) != dict:
            ident_str += (render_expression(str(key)) + ": " +
                          render_expression(str(value)))
        else:
            ident_str += (render_expression(str(key)) + 'of type ' + value['type'])
            if value['type'] is 'timedarray':
                ident_str += ('with dimentsion' + str(value['ndim']) +
                              ' and dt as ' + value['dt'])
        ident_str += ', '
    ident_str = ident_str[:-2] + endl
    return ident_str


def expand_events(events):
    event_str = ''
    for name, details in events.items():
        event_str += 'Event ' + bold(name) + endl
        event_str += ('After ' +
                       render_expression(details['threshold']['code']) + ', ')
        if 'reset' in details:
            lhs, rhs = _equation_separator(details['reset']['code'])
            event_str += (render_expression(lhs) + '&#8592;' +
                          render_expression(rhs))
        if 'refractory' in details:
            event_str += ', with refractory ' 
            if type(details['refractory']) != 'str':
                event_str += str(details['refractory'])
            else:
                event_str += render_expression(details['refractory'])
        event_str += endl
    return event_str


def expand_equations(equations):
    rend_eqn = ''
    for (var, equation) in equations.items():
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
                            " as flags associated.")
        rend_eqn += endl
    return rend_eqn


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