"""Unit tests for Modbus TCP communication module."""

import numpy as np
import pytest

from inspire_api.constants import DEFAULT_MODBUS_IP, DEFAULT_MODBUS_PORT

# Check if pymodbus is available
try:
    from inspire_api import InspireHandModbus

    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False


@pytest.mark.skipif(not MODBUS_AVAILABLE, reason="pymodbus not installed")
class TestInspireHandModbus:
    """Test cases for InspireHandModbus class."""

    def test_initialization(self):
        """Test Modbus hand initialization."""
        hand = InspireHandModbus(
            ip=DEFAULT_MODBUS_IP, port=DEFAULT_MODBUS_PORT, generation=4
        )
        assert hand._ip == DEFAULT_MODBUS_IP
        assert hand._port == DEFAULT_MODBUS_PORT
        assert hand._generation == 4
        assert not hand._connected

    def test_generation_validation(self):
        """Test that invalid generation raises error."""
        with pytest.raises(ValueError):
            InspireHandModbus(generation=5)

    def test_get_ip_port(self):
        """Test getting IP and port."""
        hand = InspireHandModbus(ip="192.168.1.100", port=5000, generation=3)
        assert hand.get_ip() == "192.168.1.100"
        assert hand.get_port() == 5000

    def test_tactile_data_gen3_error(self):
        """Test that tactile sensors raise error on Gen3."""
        from inspire_api import GenerationError

        hand = InspireHandModbus(generation=3)
        # Should raise GenerationError if we try to get tactile data
        # (would need to be connected first, but we can test the check)
        with pytest.raises(GenerationError):
            hand.get_all_tactile_data()

    def test_context_manager(self):
        """Test that hand can be used as context manager."""
        hand = InspireHandModbus(generation=4)
        assert hasattr(hand, "__enter__")
        assert hasattr(hand, "__exit__")

    def test_get_generation(self):
        """Test getting hardware generation."""
        hand = InspireHandModbus(generation=4)
        assert hand.get_generation() == 4

    def test_debug_mode(self):
        """Test debug mode toggle."""
        hand = InspireHandModbus(debug=False)
        assert not hand._debug
        hand.set_debug(True)
        assert hand._debug


# Note: Integration tests requiring actual hardware should be in a separate file
