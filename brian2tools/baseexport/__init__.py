"""
stdformatexport package to export Brian models to
standard representation
"""

from brian2.utils.logger import get_logger
from . import device

logger = get_logger(__name__)

msg = "The package is under development and may give incorrect results"
logger.warn(msg)