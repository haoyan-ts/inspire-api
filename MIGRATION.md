# Migration Guide: v0.2.0 to v1.0.0

This document helps you migrate from the old package structure to the new refactored version.

## Overview of Changes

### Package Structure

**Before (v0.2.0):**
```
inspire_api/
├── __init__.py
├── inspire_serial.py
└── inspire_modbus.py
```

**After (v1.0.0):**
```
inspire_api/
├── __init__.py
├── base.py          # NEW: Abstract base class
├── serial.py        # RENAMED from inspire_serial.py
├── modbus.py        # RENAMED from inspire_modbus.py
├── registers.py     # NEW: Register definitions
├── constants.py     # NEW: Constants and enums
├── types.py         # NEW: Data structures
├── exceptions.py    # NEW: Custom exceptions
└── utils.py         # NEW: Utility functions
```

## Import Changes

### Basic Imports

**Before:**
```python
from inspire_api import InspireHandSerial, InspireHandModbus
```

**After (same!):**
```python
from inspire_api import InspireHandSerial, InspireHandModbus
```

### New Imports Available

```python
# Data structures
from inspire_api import TactileData, FingerSensorData, ThumbSensorData

# Constants
from inspire_api import HandGeneration, JointIndex

# Exceptions
from inspire_api import (
    InspireHandError,
    ConnectionError,
    ValidationError,
    CommunicationError,
    GenerationError,
)
```

## API Changes

### 1. Class Initialization

**No changes required** - all constructors remain backwards compatible:

```python
# Serial - still works the same
hand = InspireHandSerial(port="COM3", baudrate=115200, generation=3)

# Modbus - still works the same
hand = InspireHandModbus(ip="192.168.11.210", port=6000, generation=4)
```

### 2. Connection Management

**No changes** - all methods remain the same:

```python
hand.connect()
hand.disconnect()
hand.is_connected()
```

### 3. Joint Control

**No changes** - all methods remain the same:

```python
import numpy as np

angles = np.array([500, 500, 500, 500, 500, 0], dtype=np.int32)
hand.set_angle(angles)
hand.set_speed(speeds)
hand.set_force(forces)
hand.perform_open()
hand.perform_close()
hand.return_to_zero()
```

### 4. Reading State

**No changes** - all getter methods remain the same:

```python
current = hand.get_angle_actual()
target = hand.get_angle_set()
forces = hand.get_force_actual()
errors = hand.get_error()
temps = hand.get_temp()  # Or get_temperature() for Modbus
```

### 5. Improved Error Handling

**New feature** - you can now catch specific exceptions:

**Before:**
```python
try:
    hand.connect()
except Exception as e:
    print(f"Error: {e}")
```

**After:**
```python
from inspire_api import ConnectionError, ValidationError

try:
    hand.connect()
except ConnectionError as e:
    print(f"Failed to connect: {e}")
except ValidationError as e:
    print(f"Invalid input: {e}")
```

### 6. Context Manager Support

**New feature** - you can now use the hand as a context manager:

```python
with InspireHandSerial(port="COM3") as hand:
    hand.set_angle(angles)
    # Automatically disconnects when exiting the block
```

## Breaking Changes

### Module Names (Internal Only)

If you were importing from internal modules (not recommended), update your imports:

**Before:**
```python
from inspire_api.inspire_serial import InspireHandSerial
from inspire_api.inspire_modbus import InspireHandModbus
```

**After:**
```python
from inspire_api.serial import InspireHandSerial
from inspire_api.modbus import InspireHandModbus
```

**Recommended:**
```python
# Always import from the package root
from inspire_api import InspireHandSerial, InspireHandModbus
```

### Register Dictionaries

If you were accessing `regdict` directly:

**Before:**
```python
from inspire_api.inspire_serial import regdict, regdict_gen4
```

**After:**
```python
from inspire_api.registers import get_registers

regdict_gen3 = get_registers(3)
regdict_gen4 = get_registers(4)
```

### Constants

If you were using magic numbers, use the new constants:

**Before:**
```python
port = "COM3"  # Windows default
max_angle = 1000
num_joints = 6
```

**After:**
```python
from inspire_api.constants import DEFAULT_PORT, MAX_ANGLE, NUM_JOINTS

port = DEFAULT_PORT
max_angle = MAX_ANGLE
num_joints = NUM_JOINTS
```

## New Features

### 1. Type Hints Everywhere

All functions now have comprehensive type hints for better IDE support:

```python
def set_angle(self, angles: npt.NDArray[np.integer]) -> bool:
    ...
```

### 2. Better Validation

Input validation is now more robust with clearer error messages:

```python
# Raises ValidationError with descriptive message
hand.set_angle(np.array([5000, 100, 100, 100, 100, 0], dtype=np.int32))
# ValidationError: Joint 0 angle value 5000 out of range [0, 1000]
```

### 3. Constants and Enums

Use semantic constants instead of magic numbers:

```python
from inspire_api import HandGeneration, JointIndex

# Instead of: generation = 4
generation = HandGeneration.GEN4

# Instead of: angles[0] = 500
angles[JointIndex.THUMB] = 500
```

### 4. Structured Tactile Data

Gen4 tactile sensor data is now properly structured:

```python
tactile_data = hand.get_all_tactile_data()
thumb_pressure = tactile_data.thumb.tip  # 2D numpy array
timestamp = tactile_data.timestamp
```

### 5. Utility Functions

Common operations are now available as utility functions:

```python
from inspire_api.utils import (
    validate_angles,
    validate_speeds,
    int16_to_bytes,
    bytes_to_int16,
)
```

## Testing Your Migration

### 1. Run Your Existing Code

Most code should work without changes. Test thoroughly:

```python
# Your existing code should still work
hand = InspireHandSerial(port="COM3", generation=3)
hand.connect()
hand.set_angle(np.array([500, 500, 500, 500, 500, 0], dtype=np.int32))
hand.disconnect()
```

### 2. Update Exception Handling

Add specific exception handling for better error management:

```python
from inspire_api import ConnectionError, ValidationError, CommunicationError

try:
    hand.connect()
    hand.set_angle(angles)
except ConnectionError:
    # Handle connection failures
    pass
except ValidationError:
    # Handle invalid inputs
    pass
except CommunicationError:
    # Handle communication errors
    pass
```

### 3. Adopt New Features Gradually

Start using new features incrementally:

```python
# 1. Start with context managers
with InspireHandSerial(port="COM3") as hand:
    hand.set_angle(angles)

# 2. Use constants
from inspire_api.constants import MAX_ANGLE, MIN_ANGLE

# 3. Use structured data
if hand.get_generation() == 4:
    tactile_data = hand.get_all_tactile_data()
```

## Installation

### Update Your Package

**Using pip:**
```bash
pip install --upgrade inspire-hand-api
```

**From source:**
```bash
cd inspire-api
pip install -e .
```

**With optional dependencies:**
```bash
# Modbus support
pip install inspire-hand-api[modbus]

# Development tools
pip install inspire-hand-api[dev]

# Everything
pip install inspire-hand-api[all]
```

## Common Issues

### Issue 1: Import Errors

**Problem:**
```python
ImportError: cannot import name 'InspireHandSerial' from 'inspire_api.inspire_serial'
```

**Solution:**
```python
# Import from package root, not submodules
from inspire_api import InspireHandSerial
```

### Issue 2: Type Errors

**Problem:**
```python
TypeError: angles must be a numpy.ndarray
```

**Solution:**
```python
# Ensure you're using numpy arrays
import numpy as np
angles = np.array([500, 500, 500, 500, 500, 0], dtype=np.int32)
```

### Issue 3: Validation Errors

**Problem:**
```python
ValidationError: Expected 6 angle values, got 5
```

**Solution:**
```python
# Ensure you provide all 6 joint values
angles = np.array([500, 500, 500, 500, 500, 0], dtype=np.int32)  # All 6 joints
```

## Support

If you encounter issues during migration:

1. Check the [examples/](../examples/) directory for updated code samples
2. Review the [README.md](../README.md) for API documentation
3. Open an issue on GitHub with your migration question

## Summary

- ✅ Most code works without changes
- ✅ Import from `inspire_api` (not submodules)
- ✅ All core methods remain unchanged
- ✅ New features are optional
- ✅ Better error handling available
- ✅ Improved type hints and validation

The migration should be smooth for most users. The refactoring focused on improving internal structure while maintaining API compatibility.
