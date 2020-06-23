"""
The file contains helper functions that shall be 
used for exporting standard representation format
"""
from brian2.core.variables import Constant
from brian2 import DEFAULT_CONSTANTS

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
    filter_identifiers : dict
        Filtered identifiers to use with standard format
    """

    filter_identifiers = {}
    
    for (key, value) in identifiers.items():

        if isinstance(value, Constant) and key not in DEFAULT_CONSTANTS.keys():
            filter_identifiers.update({key : value})
            
    return filter_identifiers