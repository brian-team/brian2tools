"""
The file contains helper functions that shall be 
used for exporting standard representation format
"""
from brian2.core.variables import Constant
from brian2.core.functions import Function
from brian2 import DEFAULT_CONSTANTS, DEFAULT_FUNCTIONS, Quantity

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

        if isinstance(value, Constant) and key not in DEFAULT_CONSTANTS:
            quant_identity = {key : Quantity(value.value, dim = value.dim)}
            clean_identifiers.update(quant_identity)
        
        if isinstance(value, Function) and key not in DEFAULT_FUNCTIONS:
            clean_identifiers.update({key : value})
            
    return clean_identifiers
