"""Serial communication interface for Inspire Hand control."""

import os
import time
from typing import List, Optional

import numpy as np
import numpy.typing as npt
import serial
import serial.tools

if os.name == "posix":
    import serial.tools.list_ports_posix
elif os.name == "nt":
    import serial.tools.list_ports_windows

from .base import InspireHandBase
from .constants import (
    BUFFER_CLEAR_DELAY,
    DEFAULT_BAUDRATE,
    DEFAULT_HAND_ID,
    DEFAULT_PORT,
    SERIAL_CMD_READ,
    SERIAL_CMD_WRITE,
    SERIAL_MIN_FRAME_SIZE,
    SERIAL_READ_DELAY,
    SERIAL_START_BYTE_1,
    SERIAL_START_BYTE_2,
)
from .exceptions import CommunicationError, ConnectionError, ValidationError
from .registers import categorize_register
from .utils import (
    calculate_checksum,
    convert_12bytes_to_6values,
    convert_to_serial_bytes,
    validate_angles,
    validate_forces,
    validate_speeds,
)


class InspireHandSerial(InspireHandBase):
    """
    Serial communication interface for Inspire Hand control.

    This class provides control over the Inspire Hand via RS485/UART serial communication.
    Supports both Generation 3 and Generation 4 hardware.

    Args:
        port: Serial port (e.g., "COM3" on Windows, "/dev/ttyUSB0" on Linux)
        baudrate: Communication baudrate (default: 115200)
        generation: Hardware generation (3 or 4, default: 3)
        debug: Enable debug logging (default: False)

    Example:
        >>> hand = InspireHandSerial(port="COM3", generation=3)
        >>> hand.connect()
        >>> hand.set_angle(np.array([500, 500, 500, 500, 500, 0], dtype=np.int32))
        >>> hand.disconnect()
    """

    _ser: serial.Serial
    _port: str
    _baudrate: int

    def __init__(
        self,
        port: str = DEFAULT_PORT,
        baudrate: int = DEFAULT_BAUDRATE,
        generation: int = 3,
        debug: bool = False,
    ):
        super().__init__(generation=generation, debug=debug)
        self._port = port
        self._baudrate = baudrate
        self._ser = None  # type: ignore

    def _validate_com_port(self) -> bool:
        """Validate that the COM port exists on the system."""
        if os.name == "nt":
            self._logger.debug(f"Checking COM port {self._port} on Windows")
            ports = list(serial.tools.list_ports_windows.comports())
            if self._port not in [p.device for p in ports]:
                self._logger.error(f"Port {self._port} not found")
                return False
            return True
        elif os.name == "posix":
            self._logger.debug(f"Checking port {self._port} on POSIX")
            ports = list(serial.tools.list_ports_posix.comports())
            if self._port not in [p.device for p in ports]:
                self._logger.error(f"Port {self._port} not found")
                return False
            return True
        else:
            self._logger.error(f"Unsupported OS: {os.name}")
            return False

    def connect(self) -> bool:
        """
        Establish serial connection to the hand.

        Returns:
            True if connection successful, False otherwise

        Raises:
            ConnectionError: If connection fails
        """
        try:
            self._ser = serial.Serial(self._port, self._baudrate)
            self._connected = True
            self._logger.info(
                f"Connected to serial port {self._port} at {self._baudrate} baud"
            )
            return True
        except Exception as e:
            self._logger.error(
                f"Failed to connect to {self._port} with baudrate {self._baudrate}: {e}"
            )
            self._connected = False
            raise ConnectionError(f"Failed to connect to {self._port}: {e}") from e

    def disconnect(self) -> bool:
        """
        Close the serial connection.

        Returns:
            True if disconnection successful, False otherwise
        """
        if self._ser:
            try:
                self._ser.close()
                self._connected = False
                self._logger.info(f"Disconnected from {self._port}")
                return True
            except Exception as e:
                self._logger.error(f"Failed to disconnect from {self._ser.port}: {e}")
                return False
        return True

    def is_connected(self) -> bool:
        """Check if connected to the serial port."""
        return self._connected and self._ser is not None and self._ser.is_open

    def reset_error(self) -> bool:
        """Reset error status."""
        return self._write_register(
            DEFAULT_HAND_ID, self._regdict["CLEAR_ERROR"], 1, [0x01]
        )

    def set_angle(
        self, angles: npt.NDArray[np.integer], hand_id: int = DEFAULT_HAND_ID
    ) -> bool:
        """
        Set joint angles.

        Args:
            angles: Array of 6 joint angles (0-1000)
            hand_id: Hand ID for multi-hand setups (default: 1)

        Returns:
            True if successful

        Raises:
            ValidationError: If input is invalid
        """
        angles_validated = validate_angles(angles)
        val_bytes = convert_to_serial_bytes(angles_validated)
        return self._write_register(hand_id, self._regdict["ANGLE_SET"], 12, val_bytes)

    def set_pos(
        self, positions: npt.NDArray[np.integer], hand_id: int = DEFAULT_HAND_ID
    ) -> bool:
        """Set joint positions (uses same register as angles)."""
        positions_validated = validate_angles(positions)
        val_bytes = convert_to_serial_bytes(positions_validated)
        return self._write_register(hand_id, self._regdict["POS_SET"], 12, val_bytes)

    def set_speed(
        self, speeds: npt.NDArray[np.integer], hand_id: int = DEFAULT_HAND_ID
    ) -> bool:
        """
        Set joint speeds.

        Args:
            speeds: Array of 6 joint speeds
            hand_id: Hand ID for multi-hand setups (default: 1)

        Returns:
            True if successful

        Raises:
            ValidationError: If input is invalid
        """
        speeds_validated = validate_speeds(speeds)
        val_bytes = convert_to_serial_bytes(speeds_validated)
        return self._write_register(hand_id, self._regdict["SPEED_SET"], 12, val_bytes)

    def set_force(
        self, forces: npt.NDArray[np.integer], hand_id: int = DEFAULT_HAND_ID
    ) -> bool:
        """
        Set joint forces.

        Args:
            forces: Array of 6 joint forces
            hand_id: Hand ID for multi-hand setups (default: 1)

        Returns:
            True if successful

        Raises:
            ValidationError: If input is invalid
        """
        forces_validated = validate_forces(forces)
        val_bytes = convert_to_serial_bytes(forces_validated)
        return self._write_register(hand_id, self._regdict["FORCE_SET"], 12, val_bytes)

    def _write_register(
        self, hand_id: int, addr: int, num: int, val: List[int]
    ) -> bool:
        """
        Write to a register via serial protocol.

        Args:
            hand_id: Hand ID
            addr: Register address
            num: Number of bytes to write
            val: List of byte values to write

        Returns:
            True if successful

        Raises:
            CommunicationError: If communication fails
            ValidationError: If register is invalid
        """
        if self._ser is None or not self.is_connected():
            raise CommunicationError(
                "Serial connection not established. Call connect() first."
            )

        # Validate register address
        valid_addrs = set()
        for v in self._regdict.values():
            if isinstance(v, tuple):
                valid_addrs.add(v[0])
            else:
                valid_addrs.add(v)

        if addr not in valid_addrs:
            raise ValidationError(
                f"Register address {addr} not valid for generation {self._generation}"
            )

        # Build frame
        frame = [SERIAL_START_BYTE_1, SERIAL_START_BYTE_2]
        frame.append(hand_id)
        frame.append(num + 3)
        frame.append(SERIAL_CMD_WRITE)
        frame.append(addr & 0xFF)
        frame.append((addr >> 8) & 0xFF)
        frame.extend(val)

        # Calculate and append checksum
        checksum = calculate_checksum(bytes(frame))
        frame.append(checksum)

        if self._debug:
            self._logger.debug(f"Writing to register {addr} for hand {hand_id}: {val}")

        self._ser.write(bytearray(frame))

        # Clear response buffer
        time.sleep(BUFFER_CLEAR_DELAY)
        while self._ser.in_waiting > 0:
            self._ser.read_all()
            time.sleep(BUFFER_CLEAR_DELAY)

        return True

    def _read_register(self, hand_id: int, addr: int, num: int) -> List[int]:
        """
        Read from a register via serial protocol.

        Args:
            hand_id: Hand ID
            addr: Register address
            num: Number of bytes to read

        Returns:
            List of byte values read

        Raises:
            CommunicationError: If communication fails
        """
        if self._ser is None or not self.is_connected():
            raise CommunicationError(
                "Serial connection not established. Call connect() first."
            )

        # Build frame
        frame = [SERIAL_START_BYTE_1, SERIAL_START_BYTE_2]
        frame.append(hand_id)
        frame.append(0x04)
        frame.append(SERIAL_CMD_READ)
        frame.append(addr & 0xFF)
        frame.append((addr >> 8) & 0xFF)
        frame.append(num)

        # Calculate and append checksum
        checksum = calculate_checksum(bytes(frame))
        frame.append(checksum)

        if self._debug:
            self._logger.debug(
                f"Reading {num} bytes from register {addr} for hand {hand_id}"
            )

        self._ser.write(bytearray(frame))

        time.sleep(SERIAL_READ_DELAY)
        recv = self._ser.read_all()

        if recv is None or len(recv) == 0:
            if self._debug:
                self._logger.warning(
                    f"Failed to fetch data from register {addr} for hand {hand_id}"
                )
            return []

        # Validate minimum frame size
        if len(recv) < SERIAL_MIN_FRAME_SIZE:
            if self._debug:
                self._logger.warning(f"Response too short: {len(recv)} bytes")
            return []

        num_received = (recv[3] & 0xFF) - 3
        if num_received != num:
            if self._debug:
                self._logger.warning(
                    f"Expected {num} bytes, but received {num_received} bytes"
                )

        # Extract data
        val = []
        actual_data_len = min(num_received, len(recv) - 7)
        for i in range(actual_data_len):
            val.append(recv[7 + i])

        if self._debug:
            self._logger.debug(
                f"Read {actual_data_len} values from register {addr}: {val}"
            )

        return val

    def _read6(self, hand_id: int, reg_name: str) -> List[int]:
        """Read 6 bytes from a named register."""
        if reg_name not in self._regdict:
            raise ValidationError(
                f"Register '{reg_name}' not valid for generation {self._generation}"
            )

        length = 6
        val_act = self._read_register(hand_id, self._regdict[reg_name], length)

        if val_act is None or len(val_act) < length:
            if self._debug:
                self._logger.warning(
                    f"Failed to fetch data from {reg_name} for hand {hand_id}"
                )
            return []

        if self._debug:
            self._logger.info(f"Read {reg_name}: {' '.join(map(str, val_act))}")

        return val_act

    def _read12(self, hand_id: int, reg_name: str) -> List[int]:
        """Read 12 bytes from a named register and convert to 6 16-bit values."""
        if reg_name not in self._regdict:
            raise ValidationError(
                f"Register '{reg_name}' not valid for generation {self._generation}"
            )

        length = 12
        val = self._read_register(hand_id, self._regdict[reg_name], length)

        if len(val) < length:
            if self._debug:
                self._logger.warning(
                    f"Failed to fetch data from {reg_name} for hand {hand_id}"
                )
            return []

        # Convert to 16-bit values
        val_act = convert_12bytes_to_6values(val)

        if self._debug:
            self._logger.info(f"Read {reg_name}: {' '.join(map(str, val_act))}")

        return val_act

    def get_angle_actual(self, hand_id: int = DEFAULT_HAND_ID) -> npt.NDArray[np.int32]:
        """Get actual joint angles."""
        result = self._read12(hand_id, "ANGLE_ACT")
        return np.array(result, dtype=np.int32)

    def get_angle_set(self, hand_id: int = DEFAULT_HAND_ID) -> npt.NDArray[np.int32]:
        """Get target joint angles."""
        result = self._read12(hand_id, "ANGLE_SET")
        return np.array(result, dtype=np.int32)

    def get_pos_actual(self, hand_id: int = DEFAULT_HAND_ID) -> npt.NDArray[np.int32]:
        """Get actual joint positions."""
        result = self._read12(hand_id, "POS_ACT")
        return np.array(result, dtype=np.int32)

    def get_pos_set(self, hand_id: int = DEFAULT_HAND_ID) -> npt.NDArray[np.int32]:
        """Get target joint positions."""
        result = self._read12(hand_id, "POS_SET")
        return np.array(result, dtype=np.int32)

    def get_speed_set(self, hand_id: int = DEFAULT_HAND_ID) -> npt.NDArray[np.int32]:
        """Get target joint speeds."""
        result = self._read12(hand_id, "SPEED_SET")
        return np.array(result, dtype=np.int32)

    def get_force_actual(self, hand_id: int = DEFAULT_HAND_ID) -> npt.NDArray[np.int32]:
        """Get actual joint forces."""
        result = self._read12(hand_id, "FORCE_ACT")
        return np.array(result, dtype=np.int32)

    def get_force_set(self, hand_id: int = DEFAULT_HAND_ID) -> npt.NDArray[np.int32]:
        """Get target joint forces."""
        result = self._read12(hand_id, "FORCE_SET")
        return np.array(result, dtype=np.int32)

    def get_current_actual(
        self, hand_id: int = DEFAULT_HAND_ID
    ) -> npt.NDArray[np.int32]:
        """Get actual current values."""
        result = self._read6(hand_id, "CURRENT")
        return np.array(result, dtype=np.int32)

    def get_error(self, hand_id: int = DEFAULT_HAND_ID) -> npt.NDArray[np.int32]:
        """Get error codes."""
        result = self._read6(hand_id, "ERROR")
        return np.array(result, dtype=np.int32)

    def get_temp(self, hand_id: int = DEFAULT_HAND_ID) -> npt.NDArray[np.int32]:
        """Get temperature values."""
        result = self._read6(hand_id, "TEMP")
        return np.array(result, dtype=np.int32)

    def set_action_sequence(self, hand_id: int, sequence_id: int) -> bool:
        """Set the action sequence ID."""
        return self._write_register(
            hand_id, self._regdict["ACTION_SEQ_INDEX"], 1, [sequence_id]
        )

    def run_action_sequence(self, hand_id: int) -> bool:
        """Run the current action sequence."""
        return self._write_register(hand_id, self._regdict["ACTION_SEQ_RUN"], 1, [1])

    def validate_register_addresses(self, hand_id: int = DEFAULT_HAND_ID) -> dict:
        """
        Validate register addresses by attempting to read from each one.

        Args:
            hand_id: Hand ID to test with

        Returns:
            Dictionary mapping register names to validation status (True if readable)
        """
        if not self.is_connected():
            self._logger.error(
                "Serial connection not established. Call connect() first."
            )
            return {}

        validation_results = {}
        test_registers = [
            "HAND_ID",
            "ANGLE_ACT",
            "POS_ACT",
            "FORCE_ACT",
            "CURRENT",
            "ERROR",
            "STATUS",
            "TEMP",
        ]

        self._logger.info("Validating register addresses for hardware compatibility...")

        for reg_name in test_registers:
            if reg_name not in self._regdict:
                validation_results[reg_name] = False
                self._logger.warning(
                    f"Register '{reg_name}' not found in generation {self._generation} dictionary"
                )
                continue

            try:
                # Try to read from register
                if reg_name in ["CURRENT", "ERROR", "STATUS", "TEMP"]:
                    result = self._read6(hand_id, reg_name)
                else:
                    result = self._read12(hand_id, reg_name)

                validation_results[reg_name] = len(result) > 0

                if validation_results[reg_name]:
                    self._logger.debug(
                        f"✓ Register '{reg_name}' (addr: {self._regdict[reg_name]}) is readable"
                    )
                else:
                    self._logger.warning(
                        f"✗ Register '{reg_name}' (addr: {self._regdict[reg_name]}) failed to read"
                    )

            except Exception as e:
                validation_results[reg_name] = False
                self._logger.error(
                    f"✗ Register '{reg_name}' (addr: {self._regdict[reg_name]}) validation failed: {e}"
                )

        successful_validations = sum(validation_results.values())
        total_validations = len(validation_results)

        self._logger.info(
            f"Register validation complete: {successful_validations}/{total_validations} registers accessible"
        )

        if successful_validations < total_validations:
            self._logger.warning(
                "Some registers failed validation. Consider verifying addresses with manufacturer."
            )

        return validation_results

    def export_register_verification_report(
        self, hand_id: int = DEFAULT_HAND_ID, filepath: Optional[str] = None
    ) -> str:
        """
        Export a comprehensive report for manufacturer verification of register addresses.

        Args:
            hand_id: Hand ID to test with
            filepath: Optional file path to save report

        Returns:
            Report content as string
        """
        validation_results = self.validate_register_addresses(hand_id)

        report_lines = [
            "=" * 80,
            "INSPIRE HAND API - REGISTER VERIFICATION REPORT",
            "=" * 80,
            f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Hardware Generation: {self._generation}",
            f"Test Hand ID: {hand_id}",
            f"Port: {self._port}",
            f"Baudrate: {self._baudrate}",
            "",
            "VALIDATION SUMMARY:",
            f"Total registers tested: {len(validation_results)}",
            f"Successful validations: {sum(validation_results.values())}",
            f"Failed validations: {len(validation_results) - sum(validation_results.values())}",
            "",
            "DETAILED REGISTER INFORMATION:",
            "-" * 80,
        ]

        # Group registers by category
        categories = {}
        for reg_name in self._regdict.keys():
            category = categorize_register(reg_name)
            if category not in categories:
                categories[category] = []
            categories[category].append(reg_name)

        for category, registers in sorted(categories.items()):
            report_lines.append(f"\n{category.upper().replace('_', ' ')}:")
            report_lines.append("-" * 40)

            for reg_name in sorted(registers):
                status = (
                    "✓ PASS" if validation_results.get(reg_name, False) else "✗ FAIL"
                )
                addr = self._regdict[reg_name]
                if isinstance(addr, tuple):
                    addr = addr[0]
                report_lines.append(
                    f"  {reg_name:<25} | Addr: {addr:<6} | 0x{addr:04X} | {status}"
                )

        report_lines.extend(
            [
                "",
                "NOTES FOR MANUFACTURER:",
                "- Registers marked as 'FAIL' may have incorrect addresses",
                "- Please verify against the official hardware manual",
                "- Some failures may be due to hardware state or permissions",
                "",
                "END REPORT",
                "=" * 80,
            ]
        )

        report_content = "\n".join(report_lines)

        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(report_content)
                self._logger.info(f"Register verification report saved to: {filepath}")
            except Exception as e:
                self._logger.error(f"Failed to save report to {filepath}: {e}")

        return report_content
