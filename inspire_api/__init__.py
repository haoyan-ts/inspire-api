"""
Inspire Hand Control Library

A Python library for controlling the Inspire Hand robotic hand via serial and Modbus TCP communication.
"""

from .constants import HandGeneration, JointIndex
from .exceptions import (
    CommunicationError,
    ConnectionError,
    GenerationError,
    HardwareError,
    InspireHandError,
    ValidationError,
)
from .modbus import InspireHandModbus
from .serial import InspireHandSerial
from .types import FingerSensorData, TactileData, ThumbSensorData

__version__ = "1.0.0"
__author__ = "TechShare Inc."
__email__ = "contact@techshare.com"
__description__ = "Python interface for controlling the Inspire Hand robotic hand"

__all__ = [
    # Main classes
    "InspireHandSerial",
    "InspireHandModbus",
    # Data types
    "TactileData",
    "FingerSensorData",
    "ThumbSensorData",
    # Constants
    "HandGeneration",
    "JointIndex",
    # Exceptions
    "InspireHandError",
    "ConnectionError",
    "ValidationError",
    "CommunicationError",
    "HardwareError",
    "GenerationError",
]
