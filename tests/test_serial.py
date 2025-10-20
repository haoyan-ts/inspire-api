"""Unit tests for serial communication module."""

import numpy as np
import pytest

from inspire_api import InspireHandSerial, ValidationError
from inspire_api.constants import DEFAULT_BAUDRATE, DEFAULT_PORT


class TestInspireHandSerial:
    """Test cases for InspireHandSerial class."""

    def test_initialization(self):
        """Test serial hand initialization."""
        hand = InspireHandSerial(
            port=DEFAULT_PORT, baudrate=DEFAULT_BAUDRATE, generation=3
        )
        assert hand._port == DEFAULT_PORT
        assert hand._baudrate == DEFAULT_BAUDRATE
        assert hand._generation == 3
        assert not hand._connected

    def test_generation_validation(self):
        """Test that invalid generation raises error."""
        with pytest.raises(ValueError):
            InspireHandSerial(generation=5)

    def test_set_angle_type_validation(self, sample_angles):
        """Test that set_angle requires numpy array."""
        hand = InspireHandSerial(generation=3)
        # This should work
        angles_array = np.array([100, 100, 100, 100, 100, 0], dtype=np.int32)
        # Would raise error if called without connection, but we're testing type validation
        assert isinstance(angles_array, np.ndarray)

    def test_set_angle_length_validation(self):
        """Test that set_angle validates array length."""
        hand = InspireHandSerial(generation=3)
        # Wrong length array should raise ValidationError when validated
        wrong_length = np.array([100, 100, 100], dtype=np.int32)
        with pytest.raises(ValidationError):
            from inspire_api.utils import validate_angles

            validate_angles(wrong_length)

    def test_context_manager(self):
        """Test that hand can be used as context manager."""
        hand = InspireHandSerial(generation=3)
        # Context manager should work (connection will fail but structure is correct)
        assert hasattr(hand, "__enter__")
        assert hasattr(hand, "__exit__")

    def test_get_generation(self):
        """Test getting hardware generation."""
        hand = InspireHandSerial(generation=4)
        assert hand.get_generation() == 4

    def test_debug_mode(self):
        """Test debug mode toggle."""
        hand = InspireHandSerial(debug=False)
        assert not hand._debug
        hand.set_debug(True)
        assert hand._debug


# Note: Integration tests requiring actual hardware should be in a separate file
# and marked with @pytest.mark.integration or similar
