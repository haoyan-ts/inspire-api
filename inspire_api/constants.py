"""Constants and enumerations for Inspire Hand API."""

import os
from enum import IntEnum


class HandGeneration(IntEnum):
    """Hardware generation of the Inspire Hand."""

    GEN3 = 3
    GEN4 = 4


class JointIndex(IntEnum):
    """Index of each joint in the hand."""

    THUMB = 0
    INDEX = 1
    MIDDLE = 2
    RING = 3
    PINKY = 4
    PALM = 5


class RegisterCategory(str):
    """Categories of hardware registers."""

    SYSTEM_CONTROL = "system_control"
    ACTUATOR_COMMANDS = "actuator_commands"
    SENSOR_READINGS = "sensor_readings"
    ACTION_SEQUENCES = "action_sequences"
    TOUCH_SENSORS = "touch_sensors"
    NETWORK_CONFIG = "network_config"
    OTHER = "other"


# Serial Communication Constants
SERIAL_START_BYTE_1 = 0xEB
SERIAL_START_BYTE_2 = 0x90
SERIAL_CMD_WRITE = 0x12
SERIAL_CMD_READ = 0x11
SERIAL_MIN_FRAME_SIZE = 7

# Default serial port and baudrate
DEFAULT_PORT = "COM3" if os.name == "nt" else "/dev/ttyUSB0"
DEFAULT_BAUDRATE = 115200

# Modbus Constants
MODBUS_MAX_REGISTERS_PER_READ = 125
DEFAULT_MODBUS_IP = "192.168.11.210"
DEFAULT_MODBUS_PORT = 6000

# Joint Control Constants
NUM_JOINTS = 6
DEFAULT_HAND_ID = 1
MIN_ANGLE = 0
MAX_ANGLE = 1000
MIN_SPEED = 0
MAX_SPEED = 1000
MIN_FORCE = 0
MAX_FORCE = 1000

# Special Values
PLACEHOLDER_VALUE = -1  # Used to indicate "don't change this joint"
PLACEHOLDER_VALUE_16BIT = 0xFFFF

# Timing Constants
SERIAL_READ_DELAY = 0.01  # seconds
BUFFER_CLEAR_DELAY = 0.01  # seconds

# Data Conversion Constants
BYTE_MASK = 0xFF
WORD_MASK = 0xFFFF
BITS_PER_BYTE = 8
