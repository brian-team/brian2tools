'''
Tools for use with the Brian 2 simulator.
'''
import logging

from .baseexport import *
from .mdexport import *
from .nmlexport import *
from .plotting import *
from .serialization import (
    dump_runs,
    dumps_runs,
    encode_export_data,
    decode_export_data,
    load_runs,
    loads_runs,
    NumpyCompatUnpickler,
)
from .tests import run as test

try:
    from ._version import __version__, __version_tuple__
except ImportError:
    try:
        from setuptools_scm import get_version

        __version__ = get_version(
            root="..",
            relative_to=__file__,
            version_scheme="post-release",
            local_scheme="no-local-version",
        )
        __version_tuple__ = tuple(int(x) for x in __version__.split(".")[:3])
    except ImportError:
        logging.getLogger(__name__).warning(
            "Cannot determine Brian2tools version, running from source and "
            "setuptools_scm is not installed."
        )
        __version__ = "unknown"
        __version_tuple__ = (0, 0, 0)