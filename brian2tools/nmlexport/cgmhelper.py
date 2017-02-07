import numpy as np

from brian2.core.namespace import get_local_namespace, DEFAULT_UNITS
from brian2.core.variables import Constant
from brian2.equations.equations import DIFFERENTIAL_EQUATION, SUBEXPRESSION, \
                                       PARAMETER
from brian2.groups.neurongroup import NeuronGroup
from brian2.monitors.spikemonitor import SpikeMonitor
from brian2.devices.device import Device, all_devices
from brian2.units import second, Unit, Quantity

from brian2.utils.stringtools import get_identifiers
from brian2.utils.logger import get_logger

# Make a "basestring class" for Python 3 that can be used with isinstance
try:
    basestring
except NameError:
    basestring = (str, bytes)

# Helper functions to convert the objects into string descriptions

def eq_string(equations):
    lines = []
    for eq in equations.ordered:
        unit = '1' if eq.unit == Unit(1) else repr(eq.unit)
        flags = ''
        if len(eq.flags):
            flags = '({})'.format(', '.join(eq.flags))
        if eq.type == DIFFERENTIAL_EQUATION:
            lines.append('d{eq.varname}/dt = {eq.expr} : {unit} {flags}'.format(eq=eq,
                                                                                unit=unit,
                                                                                flags=flags))
        elif eq.type == SUBEXPRESSION:
            lines.append('{eq.varname} = {eq.expression} : {unit} {flags}'.format(eq=eq,
                                                                                  unit=unit,
                                                                                  flags=flags))
        elif eq.type == PARAMETER:
            lines.append('{eq.varname} : {unit} {flags}'.format(eq=eq, unit=unit,
                                                                flags=flags))
    return '\n'.join(lines)


def get_namespace_dict(identifiers, neurongroup, run_namespace):
    variables = neurongroup.resolve_all(identifiers, run_namespace)
    namespace = {key: Quantity(value.get_value(),
                               dim=value.unit.dimensions)
                 for key, value in variables.items()
                 if (isinstance(value, Constant) and
                     not key in DEFAULT_UNITS)}
    return namespace


def description(brian_obj, run_namespace):
    if isinstance(brian_obj, NeuronGroup):
        return neurongroup_description(brian_obj, run_namespace)
    elif isinstance(brian_obj, SpikeMonitor):
        desc = '%s, name=%r' % (brian_obj.source.name, brian_obj.name)
        return '%s = SpikeMonitor(%s)' % (brian_obj.name, desc), {}
    else:
        return '', {}


def neurongroup_description(neurongroup, run_namespace):
    eqs = eq_string(neurongroup.user_equations)
    identifiers = neurongroup.user_equations.identifiers
    desc = "%d,\n'''%s'''" % (len(neurongroup), eqs)
    if 'spike' in neurongroup.events:
        threshold = neurongroup.events['spike']
        desc += ',\nthreshold=%r' % threshold
        identifiers |= get_identifiers(threshold)
    if 'spike' in neurongroup.event_codes:
        reset = neurongroup.event_codes['spike']
        desc += ',\nreset=%r' % reset
        identifiers |= get_identifiers(reset)
    if neurongroup._refractory is not None:
        refractory = neurongroup._refractory
        desc += ',\nrefractory=%r' % refractory
        if isinstance(refractory, basestring):
            identifiers |= get_identifiers(refractory)
    namespace = get_namespace_dict(identifiers, neurongroup,
                                   run_namespace)
    desc += ',\nname=%r' % neurongroup.name
    desc = '%s = NeuronGroup(%s)' % (neurongroup.name, desc)
    return desc, namespace
