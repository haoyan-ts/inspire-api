"""Type definitions and dataclasses for Inspire Hand API."""

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


@dataclass
class FingerSensorData:
    """Data class for individual finger sensor data (3 segments)."""

    top: npt.NDArray[np.int32]
    tip: npt.NDArray[np.int32]
    base: npt.NDArray[np.int32]


@dataclass
class ThumbSensorData:
    """Data class for thumb sensor data (includes mid sensor - 4 segments)."""

    top: npt.NDArray[np.int32]
    tip: npt.NDArray[np.int32]
    mid: npt.NDArray[np.int32]
    base: npt.NDArray[np.int32]


@dataclass
class TactileData:
    """
    Data class for all tactile sensor data with timestamp.

    This structure contains tactile sensor readings from all parts of the hand:
    - 5 fingers (pinky, ring, middle, index, thumb)
    - Each finger has multiple segments with pressure sensors
    - Palm sensor

    Attributes:
        timestamp: Unix timestamp when data was captured
        pinky: Tactile data for pinky finger (3 segments)
        ring: Tactile data for ring finger (3 segments)
        middle: Tactile data for middle finger (3 segments)
        index: Tactile data for index finger (3 segments)
        thumb: Tactile data for thumb (4 segments including mid)
        palm: Tactile data for palm (8x14 matrix)
    """

    timestamp: float
    pinky: FingerSensorData
    ring: FingerSensorData
    middle: FingerSensorData
    index: FingerSensorData
    thumb: ThumbSensorData
    palm: npt.NDArray[np.int32]
