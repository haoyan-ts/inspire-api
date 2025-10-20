# Inspire Hand API

A Python library for controlling the Inspire Hand robotic hand via serial and Modbus TCP communication protocols.

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 🤖 **Serial Communication**: Direct control via RS485/UART
- 🌐 **Modbus TCP**: Network-based control for distributed systems
- 🔄 **Multi-Generation Support**: Compatible with Gen 3 and Gen 4 hardware
- 📊 **Tactile Sensors**: Read tactile data from Gen 4 hardware (palm and finger sensors)
- 🎯 **Type-Safe**: Comprehensive type hints for better IDE support
- 📝 **Well-Documented**: Extensive docstrings and examples
- 🧪 **Tested**: Unit tests for core functionality

## Installation

### Basic Installation (Serial only)

```bash
pip install inspire-hand-api
```

### With Modbus TCP Support

```bash
pip install inspire-hand-api[modbus]
```

### Development Installation

```bash
git clone https://github.com/techshare/inspire-api.git
cd inspire-api
pip install -e ".[all]"
```

## Quick Start

### Serial Communication

```python
from inspire_api import InspireHandSerial
import numpy as np

# Connect to the hand
hand = InspireHandSerial(port="COM3", baudrate=115200, generation=3)
hand.connect()

# Set joint angles (6 joints: thumb, index, middle, ring, pinky, palm)
angles = np.array([500, 500, 500, 500, 500, 0], dtype=np.int32)
hand.set_angle(angles)

# Read current position
current_pos = hand.get_angle_actual()
print(f"Current position: {current_pos}")

# Close the hand
hand.perform_close()

# Disconnect
hand.disconnect()
```

### Modbus TCP Communication

```python
from inspire_api import InspireHandModbus
import numpy as np

# Connect to the hand
hand = InspireHandModbus(ip="192.168.11.210", port=6000, generation=4)
hand.connect()

# Set joint angles
angles = np.array([500, 500, 500, 500, 500, 0], dtype=np.int32)
hand.set_angle(angles)

# Read tactile sensor data (Gen 4 only)
tactile_data = hand.get_all_tactile_data()
print(f"Thumb tip pressure: {tactile_data.thumb.tip}")

# Disconnect
hand.disconnect()
```

## Hardware Support

### Generation 3
- Basic joint control (position, speed, force)
- Error and status monitoring
- Action sequences

### Generation 4
- All Gen 3 features
- Tactile sensors (palm and all finger segments)
- Enhanced sensor resolution
- Network configuration

## API Reference

### Common Methods (Both Serial and Modbus)

#### Connection Management
- `connect()` - Establish connection
- `disconnect()` - Close connection
- `is_connected()` - Check connection status

#### Joint Control
- `set_angle(angles)` - Set joint angles (0-1000)
- `set_speed(speeds)` - Set joint speeds
- `set_force(forces)` - Set joint forces
- `perform_open()` - Open all joints
- `perform_close()` - Close all joints
- `return_to_zero()` - Return to zero position

#### Reading State
- `get_angle_actual()` - Read actual joint angles
- `get_angle_set()` - Read target joint angles
- `get_force_actual()` - Read actual joint forces
- `get_error()` - Read error codes
- `get_temperature()` - Read joint temperatures

#### Tactile Sensors (Gen 4 only)
- `get_all_tactile_data()` - Read all tactile sensors
- `get_tactile_data(finger, position)` - Read specific sensor

### Serial-Specific Methods
- `validate_register_addresses()` - Validate hardware registers
- `export_register_verification_report()` - Generate diagnostic report

### Modbus-Specific Methods
- `get_ip()` - Get configured IP address
- `get_port()` - Get configured port

## Examples

See the [examples/](examples/) directory for more detailed examples:

- `serial_basic.py` - Basic serial communication
- `modbus_basic.py` - Basic Modbus TCP communication
- `tactile_sensors.py` - Reading tactile sensor data (Gen 4)
- `action_sequences.py` - Using pre-programmed action sequences

## Architecture

```
inspire_api/
├── base.py         # Abstract base class
├── serial.py       # Serial communication implementation
├── modbus.py       # Modbus TCP implementation
├── registers.py    # Hardware register mappings
├── constants.py    # Constants and enumerations
├── types.py        # Type definitions and dataclasses
├── exceptions.py   # Custom exception classes
└── utils.py        # Utility functions
```

## Error Handling

The library provides custom exceptions for better error handling:

```python
from inspire_api import InspireHandError, ConnectionError, ValidationError

try:
    hand = InspireHandSerial(port="COM3")
    hand.connect()
except ConnectionError as e:
    print(f"Failed to connect: {e}")
except ValidationError as e:
    print(f"Invalid parameters: {e}")
```

## Configuration

### Debug Mode

Enable debug logging for troubleshooting:

```python
hand = InspireHandSerial(port="COM3", debug=True)
```

### Custom Logger

Use your own logger:

```python
from loguru import logger

# Configure logger as needed
logger.add("hand_control.log", rotation="10 MB")
```

## Testing

Run the test suite:

```bash
pytest
```

With coverage:

```bash
pytest --cov=inspire_api --cov-report=html
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

### Code Style

The project uses:
- `black` for code formatting
- `ruff` for linting
- `mypy` for type checking

```bash
black inspire_api/
ruff check inspire_api/
mypy inspire_api/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### Version 1.0.0 (2025-10-20)
- 🎉 Major refactor to standard Python package structure
- ✨ Added `pyproject.toml` for modern packaging
- 🏗️ Modular architecture with clear separation of concerns
- 🛡️ Custom exception classes for better error handling
- 📚 Comprehensive documentation and examples
- 🧪 Test suite structure
- 🔧 Improved type hints and validation
- 🐛 Fixed import issues in Modbus module

### Version 0.2.0 (Previous)
- Added Gen 4 hardware support
- Tactile sensor integration
- Improved validation methods

## Support

For issues, questions, or contributions:
- **Issues**: [GitHub Issues](https://github.com/techshare/inspire-api/issues)
- **Email**: contact@techshare.com

## Acknowledgments

Developed by TechShare Inc. for the Inspire Hand robotic hand platform.
