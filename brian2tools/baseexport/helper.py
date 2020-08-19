"""
The file contains helper functions that shall be
used for exporting standard representation format
"""
from brian2 import (DEFAULT_CONSTANTS, DEFAULT_FUNCTIONS,
                    DEFAULT_UNITS, Quantity, TimedArray, second)
from brian2.core.variables import Constant
from brian2.core.functions import Function
from brian2.utils.stringtools import get_identifiers


def _prepare_identifiers(identifiers):
    """
    Helper function to filter out required identifiers and
    prepare them to use in standard dictionary format

    Parameters
    ----------
    identifiers : dict
        Dictionary of identifiers resolved by parent Group

    Returns
    -------
    clean_identifiers : dict
        Filtered identifiers to use with standard format
    """

    clean_identifiers = {}

    for (key, value) in identifiers.items():

        if isinstance(value, Constant):
            if key not in DEFAULT_CONSTANTS and key not in DEFAULT_UNITS:
                quant_identity = {key: Quantity(value.value, dim=value.dim)}
                clean_identifiers.update(quant_identity)
        # check if Function type
        elif isinstance(value, Function):
            # if TimedArray express it
            if isinstance(value, TimedArray):
                timed_arr = {'name': value.name,
                             'values': Quantity(value.values,
                                                dim=value.dim),
                             'dt': Quantity(value.dt, dim=second),
                             'ndim': value.values.ndim,
                             'type': 'timedarray'
                            }
                clean_identifiers.update({key: timed_arr})
            # else if custom function type
            elif key not in DEFAULT_FUNCTIONS:
                clean_identifiers.update({key: {'type': 'custom_func',
                                 'arg_units': value._arg_units,
                                 'arg_types': value._arg_types,
                                 'return_type': value._return_type,
                                 'return_unit': value._return_unit,
                                }})
        elif isinstance(value, Quantity):
            if key not in DEFAULT_UNITS:
                clean_identifiers.update({key: value})

    return clean_identifiers
