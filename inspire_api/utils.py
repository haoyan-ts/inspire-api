"""Utility functions for Inspire Hand API."""

from typing import List, Tuple

import numpy as np
import numpy.typing as npt

from .constants import (
    BITS_PER_BYTE,
    BYTE_MASK,
    MAX_ANGLE,
    MAX_FORCE,
    MAX_SPEED,
    MIN_ANGLE,
    MIN_FORCE,
    MIN_SPEED,
    NUM_JOINTS,
    PLACEHOLDER_VALUE,
    WORD_MASK,
)
from .exceptions import ValidationError


def validate_joint_values(
    values: npt.NDArray[np.integer],
    value_type: str = "angle",
    min_val: int = MIN_ANGLE,
    max_val: int = MAX_ANGLE,
) -> npt.NDArray[np.int32]:
    """
    Validate and normalize joint values.

    Args:
        values: Array of joint values (numpy array)
        value_type: Type of value for error messages ("angle", "speed", "force")
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Validated and normalized numpy array of int32 values

    Raises:
        ValidationError: If input is invalid
    """
    if not isinstance(values, np.ndarray):
        raise ValidationError(f"{value_type} must be a numpy.ndarray")

    # Flatten and convert to int32
    values_flat = values.flatten().astype(np.int32)

    if len(values_flat) != NUM_JOINTS:
        raise ValidationError(
            f"Expected {NUM_JOINTS} {value_type} values, got {len(values_flat)}"
        )

    # Validate each value (allow -1 as placeholder)
    for i, val in enumerate(values_flat):
        if val != PLACEHOLDER_VALUE and (val < min_val or val > max_val):
            raise ValidationError(
                f"Joint {i} {value_type} value {val} out of range [{min_val}, {max_val}]"
            )

    return values_flat


def validate_angles(angles: npt.NDArray[np.integer]) -> npt.NDArray[np.int32]:
    """Validate joint angles."""
    return validate_joint_values(angles, "angle", MIN_ANGLE, MAX_ANGLE)


def validate_speeds(speeds: npt.NDArray[np.integer]) -> npt.NDArray[np.int32]:
    """Validate joint speeds."""
    return validate_joint_values(speeds, "speed", MIN_SPEED, MAX_SPEED)


def validate_forces(forces: npt.NDArray[np.integer]) -> npt.NDArray[np.int32]:
    """Validate joint forces."""
    return validate_joint_values(forces, "force", MIN_FORCE, MAX_FORCE)


def int16_to_bytes(value: int) -> Tuple[int, int]:
    """
    Convert a 16-bit integer to low and high bytes.

    Args:
        value: Integer value to convert

    Returns:
        Tuple of (low_byte, high_byte)
    """
    low_byte = value & BYTE_MASK
    high_byte = (value >> BITS_PER_BYTE) & BYTE_MASK
    return low_byte, high_byte


def bytes_to_int16(low: int, high: int) -> int:
    """
    Convert low and high bytes to a 16-bit integer.

    Args:
        low: Low byte (0-255)
        high: High byte (0-255)

    Returns:
        16-bit integer value
    """
    return (low & BYTE_MASK) + ((high & BYTE_MASK) << BITS_PER_BYTE)


def calculate_checksum(data: bytes) -> int:
    """
    Calculate checksum for serial communication.

    Args:
        data: Byte array starting from index 2 (after start bytes)

    Returns:
        Checksum value (8-bit)
    """
    checksum = 0x00
    for byte in data[2:]:
        checksum += byte
    return checksum & BYTE_MASK


def convert_to_modbus_values(values: npt.NDArray[np.int32]) -> List[int]:
    """
    Convert joint values to Modbus register format.

    Args:
        values: Array of 6 joint values

    Returns:
        List of 6 16-bit register values
    """
    val_reg = []
    for value in values:
        if value == PLACEHOLDER_VALUE:
            val_reg.append(0xFFFF)  # Special placeholder
        else:
            val_reg.append(value & WORD_MASK)  # Take low 16 bits
    return val_reg


def convert_to_serial_bytes(values: npt.NDArray[np.int32]) -> List[int]:
    """
    Convert joint values to serial byte format (12 bytes for 6 joints).

    Args:
        values: Array of 6 joint values

    Returns:
        List of 12 bytes (low, high for each value)
    """
    val_bytes = []
    for value in values:
        low, high = int16_to_bytes(value)
        val_bytes.append(low)
        val_bytes.append(high)
    return val_bytes


def parse_serial_response(data: bytes, expected_length: int) -> List[int]:
    """
    Parse serial response data.

    Args:
        data: Raw response bytes
        expected_length: Expected number of data bytes

    Returns:
        List of parsed data values

    Raises:
        ValidationError: If response format is invalid
    """
    if len(data) < 7:  # Minimum frame size
        raise ValidationError(f"Response too short: {len(data)} bytes")

    num_received = (data[3] & BYTE_MASK) - 3
    if num_received != expected_length:
        raise ValidationError(
            f"Expected {expected_length} bytes, received {num_received} bytes"
        )

    # Extract data bytes (skip header and checksum)
    actual_data_len = min(num_received, len(data) - 7)
    values = [data[7 + i] for i in range(actual_data_len)]

    return values


def convert_12bytes_to_6values(bytes_data: List[int]) -> List[int]:
    """
    Convert 12 bytes to 6 16-bit values.

    Args:
        bytes_data: List of 12 bytes (low, high pairs)

    Returns:
        List of 6 16-bit integer values

    Raises:
        ValidationError: If input has wrong length
    """
    if len(bytes_data) < 12:
        raise ValidationError(f"Expected 12 bytes, got {len(bytes_data)}")

    values = []
    for i in range(6):
        low = bytes_data[2 * i]
        high = bytes_data[2 * i + 1]
        values.append(bytes_to_int16(low, high))

    return values


def reshape_tactile_data(
    raw_data: List[int], rows: int, cols: int, is_palm: bool = False
) -> npt.NDArray[np.int32]:
    """
    Reshape raw tactile sensor data into proper matrix format.

    Args:
        raw_data: Flat list of sensor values
        rows: Number of rows in the matrix
        cols: Number of columns in the matrix
        is_palm: Whether this is palm data (uses different mapping)

    Returns:
        2D numpy array with properly shaped tactile data

    Raises:
        ValidationError: If data length doesn't match dimensions
    """
    expected_len = rows * cols
    if len(raw_data) != expected_len:
        raise ValidationError(
            f"Data length {len(raw_data)} doesn't match dimensions {rows}x{cols}={expected_len}"
        )

    data_array = np.array(raw_data, dtype=np.int32)

    if is_palm:
        # Palm: column-first ordering (bottom to top)
        matrix = data_array.reshape(cols, rows, order="C")
        return matrix.T
    else:
        # Fingers: row-first ordering (left to right)
        return data_array.reshape(rows, cols, order="C")
