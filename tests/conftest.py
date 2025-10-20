"""Test configuration and fixtures for pytest."""

import numpy as np
import pytest


@pytest.fixture
def sample_angles():
    """Sample joint angles for testing."""
    return np.array([500, 500, 500, 500, 500, 0], dtype=np.int32)


@pytest.fixture
def sample_speeds():
    """Sample joint speeds for testing."""
    return np.array([100, 100, 100, 100, 100, 50], dtype=np.int32)


@pytest.fixture
def sample_forces():
    """Sample joint forces for testing."""
    return np.array([300, 300, 300, 300, 300, 200], dtype=np.int32)


@pytest.fixture
def zero_position():
    """Zero position for all joints."""
    return np.array([0, 0, 0, 0, 0, 0], dtype=np.int32)


@pytest.fixture
def open_position():
    """Fully open position for all joints."""
    return np.array([1000, 1000, 1000, 1000, 1000, 1000], dtype=np.int32)
