"""Abstract base class for Inspire Hand controllers."""

from abc import ABC, abstractmethod
from typing import Dict

import numpy as np
import numpy.typing as npt
from loguru import logger

from .constants import HandGeneration
from .registers import get_registers


class InspireHandBase(ABC):
    """
    Abstract base class for Inspire Hand control interfaces.

    This class provides common functionality for both serial and Modbus implementations.
    Subclasses must implement connection management and low-level communication methods.
    """

    _logger = logger
    _generation: int
    _debug: bool
    _connected: bool

    def __init__(self, generation: int = 3, debug: bool = False):
        """
        Initialize the base controller.

        Args:
            generation: Hardware generation (3 or 4)
            debug: Enable debug logging
        """
        if generation not in [HandGeneration.GEN3, HandGeneration.GEN4]:
            raise ValueError(f"Invalid generation: {generation}. Must be 3 or 4.")

        self._generation = generation
        self._debug = debug
        self._connected = False

    @property
    def _regdict(self) -> Dict:
        """Get the appropriate register dictionary based on generation."""
        return get_registers(self._generation)

    # Abstract methods that must be implemented by subclasses
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the hand.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """
        Close connection to the hand.

        Returns:
            True if disconnection successful, False otherwise
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if connected to the hand.

        Returns:
            True if connected, False otherwise
        """
        pass

    @abstractmethod
    def reset_error(self) -> bool:
        """
        Reset error status.

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def set_angle(self, angles: npt.NDArray[np.integer]) -> bool:
        """
        Set joint angles.

        Args:
            angles: Array of 6 joint angles (0-1000)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def set_speed(self, speeds: npt.NDArray[np.integer]) -> bool:
        """
        Set joint speeds.

        Args:
            speeds: Array of 6 joint speeds

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def set_force(self, forces: npt.NDArray[np.integer]) -> bool:
        """
        Set joint forces.

        Args:
            forces: Array of 6 joint forces

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_angle_actual(self) -> npt.NDArray[np.int32]:
        """
        Get actual joint angles.

        Returns:
            Array of 6 current joint angles
        """
        pass

    @abstractmethod
    def get_angle_set(self) -> npt.NDArray[np.int32]:
        """
        Get target joint angles.

        Returns:
            Array of 6 target joint angles
        """
        pass

    @abstractmethod
    def get_force_actual(self) -> npt.NDArray[np.int32]:
        """
        Get actual joint forces.

        Returns:
            Array of 6 current joint forces
        """
        pass

    # Common methods with default implementations
    def return_to_zero(self) -> bool:
        """Return all joints to zero position."""
        return self.set_angle(np.array([0, 0, 0, 0, 0, 0], dtype=np.int32))

    def perform_open(self) -> bool:
        """Open the hand (set all joints to maximum position)."""
        return self.set_angle(
            np.array([1000, 1000, 1000, 1000, 1000, 1000], dtype=np.int32)
        )

    def perform_close(self) -> bool:
        """Close the hand (set all joints to zero position)."""
        return self.set_angle(np.array([0, 0, 0, 0, 0, 0], dtype=np.int32))

    def set_pos(self, positions: npt.NDArray[np.integer]) -> bool:
        """
        Set joint positions (alias for set_angle).

        Args:
            positions: Array of 6 joint positions

        Returns:
            True if successful, False otherwise
        """
        return self.set_angle(positions)

    def get_pos_actual(self) -> npt.NDArray[np.int32]:
        """Get actual joint positions (alias for get_angle_actual)."""
        return self.get_angle_actual()

    def get_pos_set(self) -> npt.NDArray[np.int32]:
        """Get target joint positions (alias for get_angle_set)."""
        return self.get_angle_set()

    def get_pos(self) -> npt.NDArray[np.int32]:
        """Get current position (alias for get_pos_actual)."""
        return self.get_pos_actual()

    def get_generation(self) -> int:
        """Get the hardware generation (3 or 4)."""
        return self._generation

    def set_debug(self, debug: bool) -> None:
        """Enable or disable debug output."""
        self._debug = debug
        if debug:
            self._logger.info("Debug mode enabled")
        else:
            self._logger.info("Debug mode disabled")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
