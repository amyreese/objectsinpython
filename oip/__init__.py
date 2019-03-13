# Copyright 2019 John Reese
# Licensed under the MIT license

"""
Interface to Objects In Space for CircuitPython hardware.
"""

__author__ = "John Reese"
__version__ = "0.1"

from .main import OIP
from .serial import Boolean, Command, Numeric, ALL_COMMANDS, DESCRIPTIONS, VERSION
