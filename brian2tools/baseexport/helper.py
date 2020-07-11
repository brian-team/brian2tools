"""
The file contains helper functions that shall be
used for exporting standard representation format
"""
from brian2 import (DEFAULT_CONSTANTS, DEFAULT_FUNCTIONS,
                    DEFAULT_UNITS, Quantity)
from brian2.core.variables import Constant
from brian2.core.functions import Function
from brian2.utils.stringtools import get_identifiers


def _prune_identifiers(identifiers):
    """
    Helper function to filter out required identifiers
    to use them in standard dictionary format

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

        if isinstance(value, Constant) and (key not in DEFAULT_CONSTANTS and
                                            key not in DEFAULT_UNITS):
            quant_identity = {key: Quantity(value.value, dim=value.dim)}
            clean_identifiers.update(quant_identity)

        if isinstance(value, Function) and key not in DEFAULT_FUNCTIONS:
            clean_identifiers.update({key: value})

        if isinstance(value, Quantity) and key not in DEFAULT_UNITS:
            clean_identifiers.update({key: value})

    return clean_identifiers


def _resolve_identifiers_from_string(string_code, run_namespace):
    """
    Helper function to get identifiers from string, resolve them
    and prune unwanted identifiers

    Parameters
    ----------
    string_code : str
        String code

    run_namespace : dict
        namespace dictionary

    Returns
    -------
    identifiers : dict
        Identifiers retrived, resolved and cleaned
    """

    # from the code get identifiers
    identifiers = get_identifiers(string_code)
    ident_dict = {}
    # loop over identifiers to get their value from namespace
    for identifier in identifiers:
        if identifier in run_namespace:
            ident_dict.update({identifier: run_namespace[identifier]})
    # prune away unwanted identifiers
    ident_dict = _prune_identifiers(ident_dict)
    return ident_dict
