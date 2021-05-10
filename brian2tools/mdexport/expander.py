"""
Standard markdown expander class to expand Brian objects to
markdown text using standard dictionary representation of baseexport
"""
from brian2.equations.equations import str_to_sympy
from brian2.units.fundamentalunits import DIMENSIONLESS, Quantity, get_dimensions
from sympy import Derivative, symbols
from sympy.printing import latex
from sympy.abc import *
from markdown_strings import *
import numpy as np
import re
import inspect
import datetime
import brian2

# define variables for often used delimiters
endll = '\n\n'
endl = '\n'
tab = '\t'


class MdExpander():

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
    def __init__(self, brian_verbose=False, include_monitors=False,
                 keep_initializer_order=False, author=None,
                 add_meta=False, github_md=False):
        """
        Constructor for `MdExpander`

        Parameters
        ----------

        brian_verbose : bool, optional
            Whether to use Brian-like words for markdown exporter and
            if set ``True``, the names will be Brian based.
            For example, when set ``False``, 'SpikeGeneratorGroup` will be
            changed to something like, "'Spike generating source"
        include_monitors : bool, optional
            Whether to document the monitors (e.g. `SpikeMonitor` or
            `StateMonitor`). Defaults to ``False``
        keep_initializer_order : bool, optional
            Whether to keep the order of variable initializations and
            `Synapses.connect` statements. If set to ``False`` (the
            default), these will instead be included with the respective
            objects which could in principle lead to inaccuracies if the
            statements include references to other variables.
        author : str, optional
            Author field to add in the metadata

        add_meta : bool, optional
            Whether to attach meta field in output markdown text

        github_md : bool, optional
            Whether should render in GitHub supported markdown. Set `False`
            as default (`MathJax` based) and if set `False`, image has to
            created and embedded
        """

        self.brian_verbose = brian_verbose
        self.include_monitors = include_monitors
        self.keep_initializer_order = keep_initializer_order

        # if author name is given
        if author:
            if type(author) != str:
                raise Exception('Author field should be string, \
                                 not {} type'.format(type(author)))
        else:
            author = '-'
        self.author = author

        # get source file name, datetime and Brian version
        frame = inspect.stack()[1]
        user_file = inspect.getmodule(frame[0]).__file__
        date_time = datetime.datetime.now()
        brian_version = brian2.__version__

        # prepare meta-data
        meta_data = italics('Filename: {}\
                             \nAuthor: {}\
                             \nDate and localtime: {}\
                             \nBrian version: {}'.format(user_file, author,
                             date_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                             brian_version)) + endl + horizontal_rule() + endl

        self.meta_data = meta_data
        self.user_file = user_file
        self.add_meta = add_meta
        self.github_md = github_md

    def check_plural(self, iterable, singular_word=None,
                     allow_constants=True, is_int=False):
        """
        Function to attach plural form of the word
        by examining the following iterable

        Parameters
        ----------
        iterable : object with `__iter__` attribute
            Object that has to be examined

        singular_word : str, optional
            Word whose plural form has to searched in `singular_plural_dict`

        allow_constants : bool, optional
            Whether to assume non iterable as singular, if set as `True`,
            the `iterable` argument must be an iterable
        
        is_int : int, optional
            Check whether number `1` is passed, if > 1 return plural,
            by default set as `False`.
            Note: `allow_constants` should be `True`
        """
        count = 0
        # dict where adding 's' at the end won't work
        singular_plural_dict = {'index': 'indices',
                                'property': 'properties'
                               }
        # check iterable
        if hasattr(iterable, '__iter__'):
            for _ in iterable:
                count += 1
                if count > 1:
                    if singular_word:
                        try:
                            return singular_plural_dict[singular_word]
                        except KeyError:
                            raise Exception("The singular word is not found \
                                             in singular-plural dictionary.")
                    return 's'
        # check allow constants
        elif not allow_constants:
            raise IndexError("Suppose to be iterable object \
                              but instance got {}".format(type(iterable)))
        elif is_int and iterable > 1:
            return 's'
        return ''

    def prepare_math_statements(self, statements, differential=False,
                                separate=False, equals='&#8592;'):
        """
        Prepare statements to render in markdown format

        Parameters
        ----------
        statements : str
            String containing mathematical equations and statements

        differential : bool, optional
            Whether should be treated as variable in differential equation

        separate : bool, optional
            Whether lhs and rhs of the statement should be separated and
            rendered

        equals : str, optional
            Equals operator, by default arrow from right to left
        """

        rend_str = ''
        # split multilines
        list_eqns = re.split(';|\n', statements)
        # loop through each line
        for statement in list_eqns:
            # check lhs-rhs to be separated
            if separate:
                # possible operators
                if ('+=' in statement or '=' in statement or
                    '-=' in statement):
                    # join lhs and rhs
                    lhs, rhs = re.split('-=|\+=|=', statement)

                    if '+=' in statement:
                        rend_str += ('Increase ' +
                                      self.render_expression(lhs) + ' by ' +
                                      self.render_expression(rhs))
                    elif '-=' in statement:
                        rend_str += ('Decrease ' +
                                      self.render_expression(lhs) + ' by ' +
                                      self.render_expression(rhs))
                    else:
                        rend_str += (self.render_expression(lhs) +
                                     equals +  self.render_expression(rhs))
                    rend_str += ', '
            # if need not separate
            else:
                rend_str += self.render_expression(statement, differential)

        # to remove ',' from last item
        return rend_str[:-2]

    def prepare_array(self, arr, threshold=10, precision=2):
        """
        Prepare arrays using `numpy.array2string`

        Parameters
        ----------

        arr : `numpy.ndarray`
            Numpy array to prepare

        threshold : int, optional
            Threshold value to print all members
        
        precision : int, optional
            Floating point precision

        """
        if not isinstance(arr, Quantity):
            arr = np.array(arr)
        old_threshold = np.get_printoptions()['threshold']
        old_precision = np.get_printoptions()['precision']
        np.set_printoptions(threshold=threshold, precision=precision)
        md_str = str(arr)
        # reset to old value
        np.set_printoptions(threshold=old_threshold,precision=old_precision)
        return md_str

    def render_expression(self, expression, differential=False):
        """
        Function to render mathematical expression using
        `sympy.printing.latex`

        Parameters
        ----------

        expression : str, Quantity
            Expression that has to rendered

        differential : bool, optional
            Whether should be treated as variable in differential equation
        
        Returns
        -------

        rend_exp : str
            Markdown text for the expression
        """
        # change to str
        if not isinstance(expression, Quantity):
            if not isinstance(expression, str):
                expression = str(expression)
            # convert to sympy expression
            expression = str_to_sympy(expression)
        # check to be treated as differential variable
        if differential:
            # independent variable is always 't'
            t = symbols('t')
            expression = Derivative(expression, 't')
        # render expression
        rend_exp = latex(expression, mode='equation',
                         itex=True, mul_symbol='dot')
        # Deal with rand() and randn()
        rend_exp = rend_exp.replace(r'\operatorname{rand}{\left(_placeholder_{arg} \right)}',
                                    r'\mathcal{U}{\left(0, 1\right)}')
        rend_exp = rend_exp.replace(r'\operatorname{randn}{\left(_placeholder_{arg} \right)}',
                                    r'\mathcal{N}{\left(0, 1\right)}')
        # remove remaining _placeholder_{arg} inside brackets
        rend_exp = rend_exp.replace('_placeholder_{arg}', '-')
        # check GitHub based markdown rendering
        if self.github_md:
            # to remove `$$`
            rend_exp = rend_exp[2:][:-2]
            # link to render as image
            git_rend_exp = (
            '<img src="https://render.githubusercontent.com/render/math?math='+
            rend_exp + '">'
                        )
            return git_rend_exp
        # to remove `$` (in most md compiler single $ is used)
        return rend_exp[1:][:-1]

    def create_md_string(self, net_dict):
        """
        Create markdown text by checking the standard dictionary and call
        required expand functions and arrange the descriptions
        """
        # expand network header
        overall_string = self.expand_network_header(net_dict)

        # start going to the dictionary items in particular run instance
        for run_indx in range(len(net_dict)):

            # details about the particular run
            run_dict = net_dict[run_indx]
            # expand run header
            run_string = self.expand_run_header(run_dict, run_indx,
                                                single_run=len(net_dict) == 1)

            # map expand functions for particular components
            # h: "general user" naming / 'hb': "Brian" user naming
            func_map = {'neurongroup': {'f': self.expand_NeuronGroup,
                                        'hb': 'NeuronGroup',
                                        'h': 'Neuron population', 'order': 1},
                       'poissongroup': {'f': self.expand_PoissonGroup,
                                        'hb': 'PoissonGroup',
                                        'h': 'Poisson spike source',
                                        'order': 2},
                       'spikegeneratorgroup':
                                    {'f': self.expand_SpikeGeneratorGroup,
                                     'hb': 'SpikeGeneratorGroup',
                                     'h': 'Spike generating source',
                                     'order': 2},
                       'statemonitor': {'f': self.expand_StateMonitor,
                                        'hb': 'StateMonitor',
                                        'h': 'Activity recorder', 'order': 4},
                       'spikemonitor': {'f': self.expand_SpikeMonitor,
                                        'hb': 'SpikeMonitor',
                                        'h': 'Spiking activity recorder',
                                        'order': 4},
                       'eventmonitor': {'f': self.expand_EventMonitor,
                                        'hb': 'EventMonitor',
                                        'h': 'Event activity recorder',
                                        'order': 4},
                       'populationratemonitor':
                                    {'f': self.expand_PopulationRateMonitor,
                                     'hb': 'PopulationRateMonitor',
                                     'h': 'Population rate recorder',
                                     'order': 4},
                       'synapses': {'f': self.expand_Synapses,
                                    'hb': 'Synapses',
                                    'h': 'Synapse', 'order': 3},
                       'poissoninput': {'f': self.expand_PoissonInput,
                                         'hb': 'PoissonInput',
                                         'h': 'Poisson input', 'order': 0}}
            # loop over each order and expand the item
            # (same complexity as sorting the dict)
            order_list = [0, 1, 2, 3, 4]
            for current_order in order_list:
                # TODO: Implement skipping monitors properly
                if current_order == 4 and not self.include_monitors:
                    continue
                # loop through the components
                for (obj_key, obj_list) in run_dict['components'].items():
                    # whether object component is in map and correct order
                    if (obj_key in func_map.keys() and
                        func_map[obj_key]['order'] == current_order):
                        # loop through the members in list
                        # check Brian based verbose is required
                        if self.brian_verbose:
                            obj_h = func_map[obj_key]['hb']
                        else:
                            obj_h = func_map[obj_key]['h']
                        run_string += (bold(obj_h +
                                       self.check_plural(obj_list) +
                                       ' :') + endl)
                        # point out components
                        for obj_mem in obj_list:
                            if not self.keep_initializer_order:
                                # Add initializer/connector information to the respective dict
                                initializers_connectors = run_dict.get('initializers_connectors', [])
                                if obj_key in ['neurongroup', 'synapses']:
                                    obj_mem['initializer'] = [initializer
                                                              for initializer in initializers_connectors
                                                              if initializer['type'] == 'initializer' and
                                                                 initializer['source'] == obj_mem['name']]
                                if obj_key == 'synapses':
                                    obj_mem['connectors'] = [connector
                                                             for connector in initializers_connectors
                                                             if connector['type'] == 'connect' and
                                                                connector['synapses'] == obj_mem['name']]
                            run_string += ('- ' +
                                           func_map[obj_key]['f'](obj_mem))

            if self.keep_initializer_order:
                # differentiate connectors and initializers
                any_init = False
                any_connect = 0
                if 'initializers_connectors' in run_dict:
                    # loop through the members only to check the items
                    for init_cont in run_dict['initializers_connectors']:
                        if init_cont['type'] == 'initializer':
                            any_init = True
                        else:
                            any_connect += 1
                # check at least any one is present
                if any_init or any_connect:
                    if any_init:
                        run_string += bold('Initializing at start')
                    if any_connect:
                        if any_init:
                            run_string += ' and '
                        run_string += bold('Synaptic connection' +
                                    self.check_plural(any_connect, is_int=True) +
                                    ' :')
                    run_string += endl

                    for init_cont in run_dict['initializers_connectors']:
                        # expand accordingly
                        if init_cont['type'] == 'initializer':
                            run_string += ('- ' +
                                           self.expand_initializer(init_cont))
                        else:
                            run_string += '- ' + self.expand_connector(init_cont)

            # check inactive objects
            if 'inactive' in run_dict:
                run_string += endl
                run_string += (bold('Inactive member' +
                               self.check_plural(run_dict['inactive']) + ':')
                               + endl)
                run_string += ', '.join(run_dict['inactive'])

            run_string += ('The simulation was run for ' +
                       bold(str(run_dict['duration'])) + endll)

            overall_string += run_string

        # final markdown text to pass to `build()`
        self.md_text = overall_string

        if self.add_meta:
            self.md_text = self.meta_data + self.md_text

        return self.md_text

    def expand_network_header(self, net_dict):
        """
        Expand function to write network header
        """
        md_str = header('Network details', 1) + endl
        n_runs = ''
        if len(net_dict) > 1:
            n_runs += 's'
            # mention about no. of total run simulations
            md_str += ('The Network consist' + n_runs + ' of {} simulation \
                        run'.format(bold(len(net_dict))) +
                        self.check_plural(net_dict) + endl + horizontal_rule() +
                        endl)
        return md_str

    def expand_run_header(self, run_dict, run_indx, single_run=False):
        """
        Expand run() header

        Parameters
        ----------

        run_dict : dict
            run dictionary

        run_indx : int
            Index of run

        single_run : bool, optional
            Whether only single run() defined for the network
        """
        md_str = ''

        if not single_run:
            md_str += header('Run ' + str(run_indx + 1) + ' details', 3)

        md_str += endl

        return md_str

    def expand_NeuronGroup(self, neurongrp):
        """
        Expand NeuronGroup from standard dictionary

        Parameters
        ----------

        neurongrp : dict
            Standard dictionary of NeuronGroup
        """
        # start expanding
        md_str = ''
        # name and size
        md_str += ('Group ' + bold(neurongrp['name']) + ', consisting of ' +
                   bold(neurongrp['N']) + ' neurons.' + endll)
        # expand model equations
        md_str += tab + bold('Model dynamics:') + endll
        md_str += self.expand_equations(neurongrp['equations'])
        if neurongrp['user_method']:
            md_str += (tab + 'The equations are integrated with the \'' +
                       neurongrp['user_method'] + '\' method.' + endll)
        # expand associated events
        if 'events' in neurongrp:
            md_str += tab + bold('Events:') + endll
            md_str += self.expand_events(neurongrp['events'])
        # expand identifiers associated
        if 'identifiers' in neurongrp:
            md_str += tab + bold('Constants:') + ' '
            md_str += self.expand_identifiers(neurongrp['identifiers']) + endll
        if not self.keep_initializer_order and 'initializer' in neurongrp and len(neurongrp['initializer']):
            md_str += tab + bold('Initial values:') + '\n'
            for initializer in neurongrp['initializer']:
                md_str += tab + '* ' + self.expand_initializer(initializer) + '\n'
            md_str += '\n'
        # expand run_regularly()
        if 'run_regularly' in neurongrp:
            md_str += (tab + bold('Run regularly') +
            self.check_plural(neurongrp['run_regularly']) + ': ' + endll)
            for run_reg in neurongrp['run_regularly']:
                md_str += self.expand_runregularly(run_reg)

        return md_str

    def expand_SpikeSource(self, source):
        """
        Check whether subgroup dict and expand accordingly
        
        Parameters
        ----------

        source : str, dict
            Source group name or subgroup dictionary
        """
        if isinstance(source, str):
            return italics(source)
        # if not one member
        if source['start'] != source['stop']:
            return ('neurons ' + str(source['start']) + ' to ' +
                    str(source['stop']) + ' of ' + italics(source['group']))
        # if only single member
        return ('neuron ' + str(source['start']) + ' of '+
                italics(source['group']))

    def expand_identifier(self, ident_key, ident_value):
        """
        Expand identifer (key-value form)

        Parameters
        ----------

        ident_key : str
            Identifier name
        ident_value : Quantity, str, dict
            Identifier value. Dictionary if identifer is of type either
            `TimedArray` or custom function
        """
        ident_str = ''
        # if not `TimedArray` nor custom function
        if type(ident_value) != dict:
            ident_str += (self.render_expression(ident_key) + "= " +
                          self.render_expression(ident_value))
        # expand dictionary
        else:
            ident_str += (self.render_expression(ident_key) + ' of type ' +
                          ident_value['type'])
            if ident_value['type'] == 'timedarray':
                ident_str += (' with dimension ' +
                              self.render_expression(ident_value['ndim']) +
                              ' and dt as ' +
                              self.render_expression(ident_value['dt']))
        return ident_str

    def expand_identifiers(self, identifiers):
        """
        Expand function to loop through identifiers and call
        `expand_identifier`
        """
        idents = [self.expand_identifier(key, value)
                  for key, value in identifiers.items()]
        if len(idents) == 1:
            idents_str = idents[0]
        elif len(idents) == 2:
            idents_str = idents[0] + ' and ' + idents[1]
        else:
            idents_str = ', '.join(idents[:-1]) + ', and ' + idents[-1]
        return idents_str

    def expand_event(self, event_name, event_details):
        """
        Function to expand event dictionary

        Parameters
        ----------

        event_name : str
            name of the event

        event_details : dict
            details of the event
        """
        event_str = ''
        event_str += tab + ('If ' + self.render_expression(event_details['threshold']['code']) +
                            ', a ' + bold(event_name) + ' event is triggered')
        if 'reset' in event_details:
            event_str += (' and ' + self.prepare_math_statements(
                event_details['reset']['code'],
                separate=True)
                         )
        event_str += '.'
        if 'refractory' in event_details:
            if isinstance(event_details['refractory'], Quantity):
                event_str += ' The neuron remains refractory for '
                event_str += self.render_expression(event_details['refractory']) + '.'
            else:
                event_str += ' The neuron remains refractory as long as '
                event_str += self.render_expression(event_details['refractory']) + '.'

        return event_str + endll

    def expand_events(self, events):
        """
        Expand function to loop through all events and call
        `expand_event`
        """
        events_str = ''
        for name, details in events.items():
            events_str += self.expand_event(name, details)

        return events_str

    def expand_equation(self, var, equation):
        """
        Expand Equation from equation dictionary

        Parameters
        ----------

        var : str
            Variable name
        equation : dict
            Details of the equation
        """
        rend_eqn = ''
        if equation['type'] == 'differential equation':
            rend_eqn += self.render_expression(var, differential=True)
        elif equation['type'] == 'subexpression':
            rend_eqn += self.render_expression(var)
        else:
            rend_eqn += 'Parameter ' + self.render_expression(var)
            if get_dimensions(equation['unit']) is DIMENSIONLESS:
                unit = '(dimensionless)'
            else:
                unit = '(in units of ' + self.render_expression(equation['unit']) + ')'
            rend_eqn += ' ' + unit
        if 'expr' in equation:
            rend_eqn += '=' + self.render_expression(equation['expr'])
        # TODO: How to handle units
        # rend_eqn += (", where unit of " + self.render_expression(var) +
        #                 " is " + str(equation['unit']))
        if 'flags' in equation:
            if 'unless refractory' in equation['flags']:
                rend_eqn += ', except during the refractory period.'
            # TODO: How to handle other flags?
            # rend_eqn += (' and ' + self.prepare_array(equation['flags']) +
            #              ' as flag' + self.check_plural(equation['flags']) +
            #              ' associated')
        return tab + rend_eqn + endll

    def expand_equations(self, equations):
        """
        Function to loop all equations
        """
        rend_eqns = ''
        for (var, equation) in equations.items():
            rend_eqns += self.expand_equation(var, equation)
        return rend_eqns

    def expand_initializer(self, initializer):
        """
        Expand initializer from initializer dictionary

        Parameters
        ----------

        initializer : dict
            Dictionary representation of initializer
        """
        init_str = ''
        init_str += ('Variable ' +
                     self.render_expression(initializer['variable']))
        if self.keep_initializer_order:
            init_str += (' of ' + self.expand_SpikeSource(initializer['source']) +
                     ' initialized with ')
        else:
            init_str += '= '
        init_str += self.render_expression(initializer['value'])

        # not a good checking
        if (isinstance(initializer['index'], str) and
                (initializer['index'] != 'True' and initializer['index'] != 'False')):
            init_str += ' if ' + self.render_expression(initializer['index'])
        elif (isinstance(initializer['index'], bool) or
            (initializer['index'] == 'True' or
             initializer['index'] == 'False')):
            if initializer['index'] is True or initializer['index'] == 'True':
                init_str += ''  # "to all members" implied
            else:
                raise AssertionError('Initialization with \'False\' as index?')
        else:
            init_str += (' to member' +
                         self.check_plural(initializer['index']) + ' ')
            if not hasattr(initializer['index'], '__iter___'):
                init_str += str(initializer['index'])
            else:
                init_str += ','.join(
                    [str(ind) for ind in initializer['index']]
                                    )
        if 'identifiers' in initializer:
            init_str += (', where ' + self.expand_identifiers(initializer['identifiers']) + '.')
        # pad new line if ordered in list
        if self.keep_initializer_order:
            return init_str + endll
        return init_str

    def expand_connector(self, connector):
        """
        Expand synaptic connector from connector dictionary

        Parameters
        ----------

        connector : dict
            Dictionary representation of connector
        """
        con_str = ''
        if self.keep_initializer_order:
            # Otherwise not necessary since this is part of the Synapses description
            con_str += ('Connection from ' +
                        self.expand_SpikeSource(connector['source']) +
                        ' to ' + self.expand_SpikeSource(connector['target']))
        if 'i' in connector:
            con_str += ('. From source group ' +
                        self.check_plural(connector['i'], 'index') + ': ')
            if not isinstance(connector['i'], str):
                if hasattr(connector['i'], '__iter__'):
                    con_str += self.prepare_array(connector['i'])
                else:
                    con_str += str(connector['i'])
            else:
                con_str += (' with generator syntax ' +
                            inline_code(connector['i']))
            if 'j' in connector:
                con_str += (' to target group ' +
                            self.check_plural(connector['j'], 'index') + ': ')
                if not isinstance(connector['j'], str):
                    if hasattr(connector['j'], '__iter__'):
                        con_str += self.prepare_array(connector['j'])
                    else:
                        con_str += str(connector['j'])
                else:
                    con_str += (' with generator syntax ' +
                                 inline_code(connector['j']))
            else:
                con_str += ' to all target group members'

        elif 'j' in connector:
            con_str += '. Connection for all members in source group'
            if not isinstance(connector['j'], str):
                con_str += (' to target group ' +
                        self.check_plural(connector['j'], 'index') + ': ')
                if hasattr(connector['j'], '__iter__'):
                    con_str += self.prepare_array(connector['j'])
                else:
                    con_str += str(connector['j'])
            else:
                con_str += (' to target group with generator syntax ' +
                             inline_code(connector['j']))

        elif 'condition' in connector:
            con_str += (' with condition ' +
                        self.render_expression(connector['condition']))
        else:
            con_str += '. Pairwise connections'
        if connector['probability'] != 1:
            con_str += (' with probability ' +
                        self.render_expression(connector['probability']))
        if connector['n_connections'] != 1:
            con_str += (' with number of connections ' +
                        self.render_expression(connector['n_connections']))
        if 'identifiers' in connector:
            con_str += ('. Constants associated: ' +
                        self.expand_identifiers(connector['identifiers']))
        return con_str + '.' + endll

    def expand_PoissonGroup(self, poisngrp):
        """
        Expand PoissonGroup from standard dictionary

        Parameters
        ----------

        poisngrp : dict
            Standard dictionary of PoissonGroup
        """

        md_str = ''
        md_str += (tab + 'Name ' + bold(poisngrp['name']) + ', with \
                population size ' + bold(poisngrp['N']) +
                ' and rate as ' + self.render_expression(poisngrp['rates']) +
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
        """
        Expand SpikeGeneratorGroup from standard dictionary

        Parameters
        ----------

        spkgen : dict
            Standard dictionary of SpikeGeneratorGroup
        """
        md_str = ''
        md_str += (tab + 'Name ' + bold(spkgen['name']) +
                ', with population size ' + bold(spkgen['N']) +
                ', has neuron' + self.check_plural(spkgen['indices']) + ': ' +
                self.prepare_array(spkgen['indices']) +
                ' that spike at times ' +
                self.prepare_array(spkgen['times']) +
                ', with period ' + str(spkgen['period']) +
                '.' + endll)
        if 'run_regularly' in spkgen:
            md_str += tab + bold('Run regularly: ') + endll
            for run_reg in spkgen['run_regularly']:
                md_str += self.expand_runregularly(run_reg)

        return md_str

    def expand_StateMonitor(self, statemon):
        """
        Expand StateMonitor from standard dictionary

        Parameters
        ----------

        statemon : dict
            Standard dictionary of StateMonitor
        """
        md_str = ''
        md_str += (tab + 'Monitors variable' +
                self.check_plural(statemon['variables']) + ': ' +
                ','.join(
                [self.render_expression(var) for var in statemon['variables']]
                        ) +
                ' of ' + self.expand_SpikeSource(statemon['source']))
        if isinstance(statemon['record'], bool):
            if statemon['record']:
                md_str += ' for all members'
        else:
            # another bad hack (before with initializers)
            if not statemon['record'].size:
                md_str += ' for no member'
            else:
                md_str += (', for member' +
                           self.check_plural(statemon['record']) +
                           ': ' +
                           ','.join([str(ind) for ind in statemon['record']]))
        return md_str + endll

    def expand_SpikeMonitor(self, spikemon):
        """
        Expand SpikeMonitor from standard representation

        Parameters
        ----------

        spikemon : dict
            Standard dictionary of SpikeMonitor
        """
        return self.expand_EventMonitor(spikemon)

    def expand_EventMonitor(self, eventmon):
        """
        Expand EventMonitor from standard representation

        Parameters
        ----------

        eventmon : dict
            Standard dictionary of EventMonitor
        """
        md_str = ''
        md_str += (tab + 'Monitors variable' +
                self.check_plural(eventmon['variables']) + ': ' +
                ','.join(
                [self.render_expression(var) for var in eventmon['variables']]
                    ) +
                ' of ' + self.expand_SpikeSource(eventmon['source']))
        if isinstance(eventmon['record'], bool):
            if eventmon['record']:
                md_str += ' for all members'
        else:
            if not eventmon['record'].size:
                md_str += ' for no member'
            else:
                md_str += (
                    ', for member' + self.check_plural(eventmon['record']) +
                    ': ' +
                    ','.join([str(ind) for ind in eventmon['record']]))
        md_str += (' when event ' + bold(eventmon['event']) +
                    ' is triggered')
        return md_str + endll

    def expand_PopulationRateMonitor(self, popratemon):
        """
        Expand PopulationRateMonitor

        Parameters
        ----------

        popratemon : dict
            PopulationRateMonitor's baseexport dictionary
        """
        md_str = ''
        md_str += (tab + 'Monitors the population of ' +
                   self.expand_SpikeSource(popratemon['source']) +
                   '.' + endll)
        return md_str

    def expand_pathway(self, pathway):
        """
        Expand `SynapticPathway`

        Parameters
        ----------

        pathway : dict
            SynapticPathway's baseexport dictionary
        """
        if pathway['prepost'] == 'pre':
            pathway_str = 'pre-synaptic'
        elif pathway['prepost'] == 'post':
            pathway_str = 'post-synaptic'
        else:
            pathway_str = pathway['prepost']
        if pathway['event'] == 'spike':
            event_str = 'spike'
        else:
            event_str = italics(pathway['event']) + ' event'
        md_str = (tab + 'For each ' + bold(pathway_str) +
                  ' ' + pathway['event'] + ': ' +
                  self.prepare_math_statements(pathway['code'], separate=True)
                  )
        # check delay is associated
        if 'delay' in pathway:
            md_str += (', with a synaptic delay of ' +
                    self.render_expression(pathway['delay']))
        return md_str

    def expand_pathways(self, pathways):
        """
        Loop through pathways and call `expand_pathway`
        """
        path_strs = [self.expand_pathway(pathway)
                     for pathway in pathways]
        return endll.join(path_strs)

    def expand_summed_variable(self, sum_variable):
        """
        Expand Summed variable

        Parameters
        ----------

        sum_variabe : dict
            SummedVariable's baseexport dictionary
        """
        md_str = (tab + 'Updates target group ' +
                  self.expand_SpikeSource(sum_variable['target']) +
                  ' with statement: ' +
                  self.render_expression(sum_variable['code']) + endll)

        return md_str

    def expand_summed_variables(self, sum_variables):
        """
        Loop through summed variables and call `expand_summed_variable`
        """
        sum_var_str = ''
        for sum_var in sum_variables:
            sum_var_str += self.expand_summed_variable(sum_var)
        return sum_var_str

    def expand_Synapses(self, synapse):
        """
        Expand `Synapses` details from Baseexporter dictionary

        Parameters
        ----------

        synapse : dict
            Dictionary representation of `Synapses` object
        """
        md_str = ''
        md_str += (tab + 'Connections ' + bold(synapse['name']) + ', connecting ' +
                   self.expand_SpikeSource(synapse['source']) +
                   ' to ' + self.expand_SpikeSource(synapse['target'])
                  )
        # expand connectors
        if not self.keep_initializer_order and 'connectors' in synapse:
            if len(synapse['connectors']) > 1:
                raise NotImplementedError('Only a single connect statement per Synapses object supported.')
            if len(synapse['connectors']):
                md_str += tab + self.expand_connector(synapse['connectors'][0])
        else:
            md_str += '.' + endll
        # expand model equations
        if 'equations' in synapse:
            md_str += tab + bold('Model dynamics:') + endll
            md_str += self.expand_equations(synapse['equations'])
            if 'user_method' in synapse:
                md_str += (tab + 'The equations are integrated with the \'' +
                           synapse['user_method'] + '\' method.' + endll)
        # expand pathways using `expand_pathways`
        if 'pathways' in synapse:
            md_str += self.expand_pathways(synapse['pathways'])
            if 'equations' not in synapse and 'identifiers' in synapse:
                # Put the external constants right here
                md_str += tab + ', where ' + self.expand_identifiers(synapse['identifiers']) + '.'
            md_str += endll
        # expand summed_variables using `expand_summed_variables`
        if 'summed_variables' in synapse:
            md_str += tab + bold('Summed variables:') + endll
            md_str += self.expand_summed_variables(synapse['summed_variables'])
        # expand identifiers if defined
        if 'identifiers' in synapse and 'equations' in synapse:
            md_str += tab + bold('Constants:') + ' '
            md_str += self.expand_identifiers(synapse['identifiers']) + endll
        if not self.keep_initializer_order and 'initializer' in synapse and len(synapse['initializer']):
            md_str += tab + bold('Initial values:') + '\n'
            for initializer in synapse['initializer']:
                md_str += tab + '* ' + self.expand_initializer(initializer) + '\n'
            md_str += '\n'
        return md_str

    def expand_PoissonInput(self, poinp):
        """
        Expand PoissonInput

        Parameters
        ----------

        poinp : dict
            Standard dictionary representation for PoissonInput
        """
        md_str = ''
        md_str += (tab + 'PoissonInput with size ' + bold(poinp['N']) +
                ' gives input to variable ' +
                self.render_expression(poinp['target_var']) +
                ' with rate ' + self.render_expression(poinp['rate']) +
                ' and weight of ' + self.render_expression(poinp['weight']) +
                endll)
        if 'identifiers' in poinp:
            md_str += tab + bold('Constants:') + endll
            md_str += self.expand_identifiers(poinp['identifiers'])
        return md_str

    def expand_runregularly(self, run_reg):
        """
        Expand run_regularly from standard dictionary

        Parameters
        ----------

        run_reg : dict
            Standard dictionary representation for run_regularly()
        """
        md_str = (tab + 'For every ' + self.render_expression(run_reg['dt']) +
                ' code: ' +
                self.prepare_math_statements(run_reg['code'], separate=True) +
                ' will be executed' + endll)
        return md_str
