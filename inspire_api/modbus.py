"""Modbus TCP communication interface for Inspire Hand control."""

import time
from typing import List

import numpy as np
import numpy.typing as npt

try:
    from pymodbus.client import ModbusTcpClient

    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False

from .base import InspireHandBase
from .constants import (
    DEFAULT_MODBUS_IP,
    DEFAULT_MODBUS_PORT,
    MODBUS_MAX_REGISTERS_PER_READ,
)
from .exceptions import (
    CommunicationError,
    ConnectionError,
    GenerationError,
    ValidationError,
)
from .types import FingerSensorData, TactileData, ThumbSensorData
from .utils import (
    convert_to_modbus_values,
    reshape_tactile_data,
    validate_angles,
    validate_forces,
    validate_speeds,
)


class InspireHandModbus(InspireHandBase):
    """
    Modbus TCP communication interface for Inspire Hand control.

    This class provides control over the Inspire Hand via Modbus TCP network protocol.
    Supports both Generation 3 and Generation 4 hardware.

    Args:
        ip: IP address of the Modbus server (default: "192.168.11.210")
        port: TCP port of the Modbus server (default: 6000)
        generation: Hardware generation (3 or 4, default: 3)
        debug: Enable debug logging (default: False)

    Raises:
        ImportError: If pymodbus is not installed

    Example:
        >>> hand = InspireHandModbus(ip="192.168.11.210", generation=4)
        >>> hand.connect()
        >>> hand.set_angle(np.array([500, 500, 500, 500, 500, 0], dtype=np.int32))
        >>> tactile_data = hand.get_all_tactile_data()  # Gen4 only
        >>> hand.disconnect()
    """

    _client: ModbusTcpClient
    _ip: str
    _port: int

    def __init__(
        self,
        ip: str = DEFAULT_MODBUS_IP,
        port: int = DEFAULT_MODBUS_PORT,
        generation: int = 3,
        debug: bool = False,
    ):
        if not MODBUS_AVAILABLE:
            raise ImportError(
                "pymodbus is required for Modbus TCP communication. "
                "Install it with: pip install pymodbus"
            )

        super().__init__(generation=generation, debug=debug)
        self._ip = ip
        self._port = port
        self._client = None  # type: ignore

    def connect(self) -> bool:
        """
        Connect to the Modbus TCP server.

        Returns:
            True if connection successful

        Raises:
            ConnectionError: If connection fails
        """
        try:
            self._client = ModbusTcpClient(self._ip, port=self._port)
            result = self._client.connect()
            self._connected = result
            if result:
                self._logger.info(
                    f"Connected to Modbus TCP server at {self._ip}:{self._port}"
                )
            else:
                raise ConnectionError(
                    f"Failed to connect to Modbus TCP server at {self._ip}:{self._port}"
                )
            return result
        except Exception as e:
            self._logger.error(f"Failed to connect to Modbus TCP server: {e}")
            self._connected = False
            raise ConnectionError(
                f"Failed to connect to {self._ip}:{self._port}: {e}"
            ) from e

    def disconnect(self) -> bool:
        """
        Disconnect from the Modbus TCP server.

        Returns:
            True if disconnection successful
        """
        if self._client and self._connected:
            try:
                self._client.close()
                self._connected = False
                self._logger.info("Disconnected from Modbus TCP server")
                return True
            except Exception as e:
                self._logger.error(f"Failed to disconnect from Modbus TCP server: {e}")
                return False
        return True

    def is_connected(self) -> bool:
        """Check if connected to the Modbus TCP server."""
        return self._connected and self._client is not None

    def reset_error(self) -> bool:
        """Reset error status."""
        return self._write_register(self._regdict["CLEAR_ERROR"], [1])

    def set_angle(self, angles: npt.NDArray[np.integer]) -> bool:
        """
        Set joint angles.

        Args:
            angles: Array of 6 joint angles (0-1000)

        Returns:
            True if successful

        Raises:
            ValidationError: If input is invalid
        """
        angles_validated = validate_angles(angles)
        val_reg = convert_to_modbus_values(angles_validated)
        return self._write_register(self._regdict["ANGLE_SET"], val_reg)

    def set_pos(self, positions: npt.NDArray[np.integer]) -> bool:
        """Set joint positions (uses same register as angles)."""
        return self.set_angle(positions)

    def set_speed(self, speeds: npt.NDArray[np.integer]) -> bool:
        """
        Set joint speeds.

        Args:
            speeds: Array of 6 joint speeds

        Returns:
            True if successful

        Raises:
            ValidationError: If input is invalid
        """
        speeds_validated = validate_speeds(speeds)
        val_reg = convert_to_modbus_values(speeds_validated)
        return self._write_register(self._regdict["SPEED_SET"], val_reg)

    def set_force(self, forces: npt.NDArray[np.integer]) -> bool:
        """
        Set joint forces.

        Args:
            forces: Array of 6 joint forces

        Returns:
            True if successful

        Raises:
            ValidationError: If input is invalid
        """
        forces_validated = validate_forces(forces)
        val_reg = convert_to_modbus_values(forces_validated)
        return self._write_register(self._regdict["FORCE_SET"], val_reg)

    def _write_register(self, address: int, values: List[int]) -> bool:
        """
        Write to Modbus registers.

        Args:
            address: Starting register address
            values: List of 16-bit values to write

        Returns:
            True if successful

        Raises:
            CommunicationError: If communication fails
        """
        if not self.is_connected():
            raise CommunicationError(
                "Modbus connection not established. Call connect() first."
            )

        try:
            if self._debug:
                self._logger.debug(f"Writing to register {address}: {values}")

            self._client.write_registers(address, values)
            return True
        except Exception as e:
            self._logger.error(f"Failed to write to register {address}: {e}")
            raise CommunicationError(
                f"Failed to write to register {address}: {e}"
            ) from e

    def _read_register(self, address: int, count: int) -> List[int]:
        """
        Read from Modbus registers with automatic segmentation for large reads.

        This method reads holding registers from a Modbus device, automatically handling
        large read requests by segmenting them into smaller chunks that comply with
        Modbus protocol limitations (max 125 registers per transaction).

        Args:
            address: Starting register address to read from
            count: Number of consecutive registers to read

        Returns:
            List of register values read from the device

        Raises:
            CommunicationError: If communication fails
        """
        if not self.is_connected():
            raise CommunicationError(
                "Modbus connection not established. Call connect() first."
            )

        try:
            if count <= MODBUS_MAX_REGISTERS_PER_READ:
                # Single read for small requests
                if self._debug:
                    self._logger.debug(
                        f"Reading {count} registers from address {address}"
                    )

                response = self._client.read_holding_registers(address, count=count)
                if response.isError():
                    raise CommunicationError(
                        f"Modbus read error from address {address}"
                    )

                result = response.registers
                if self._debug:
                    self._logger.debug(
                        f"Read {len(result)} values from register {address}: {result}"
                    )

                return result
            else:
                # Segmented read for large requests
                if self._debug:
                    self._logger.debug(
                        f"Reading {count} registers from address {address} in segments "
                        f"(max {MODBUS_MAX_REGISTERS_PER_READ} per segment)"
                    )

                all_results = []
                remaining_count = count
                current_address = address

                while remaining_count > 0:
                    segment_count = min(remaining_count, MODBUS_MAX_REGISTERS_PER_READ)

                    if self._debug:
                        self._logger.debug(
                            f"Reading segment: {segment_count} registers from address {current_address}"
                        )

                    response = self._client.read_holding_registers(
                        current_address, count=segment_count
                    )
                    if response.isError():
                        raise CommunicationError(
                            f"Modbus read error from address {current_address} (segment)"
                        )

                    segment_results = response.registers
                    all_results.extend(segment_results)

                    remaining_count -= segment_count
                    current_address += segment_count

                if self._debug:
                    self._logger.debug(
                        f"Completed segmented read: {len(all_results)} total values from address {address}"
                    )

                return all_results

        except Exception as e:
            self._logger.error(f"Failed to read from register {address}: {e}")
            raise CommunicationError(
                f"Failed to read from register {address}: {e}"
            ) from e

    def _read6_16bit(self, reg_name: str) -> List[int]:
        """Read 6 16-bit values from a named register."""
        if reg_name not in self._regdict:
            raise ValidationError(
                f"Register '{reg_name}' not valid for generation {self._generation}"
            )

        val = self._read_register(self._regdict[reg_name], 6)

        if len(val) < 6:
            if self._debug:
                self._logger.warning(f"Failed to fetch 6 values from {reg_name}")
            return []

        if self._debug:
            self._logger.info(f"Read {reg_name}: {' '.join(map(str, val))}")

        return val

    def _read6_8bit(self, reg_name: str) -> List[int]:
        """Read 6 8-bit values from a named register (3 Modbus registers split into bytes)."""
        if reg_name not in self._regdict:
            raise ValidationError(
                f"Register '{reg_name}' not valid for generation {self._generation}"
            )

        val_act = self._read_register(self._regdict[reg_name], 3)

        if len(val_act) < 3:
            if self._debug:
                self._logger.warning(f"Failed to fetch data from {reg_name}")
            return []

        # Split each 16-bit register into high and low bytes
        results = []
        for val in val_act:
            low_byte = val & 0xFF
            high_byte = (val >> 8) & 0xFF
            results.append(low_byte)
            results.append(high_byte)

        if self._debug:
            self._logger.info(f"Read {reg_name}: {' '.join(map(str, results))}")

        return results

    def get_angle_actual(self) -> npt.NDArray[np.int32]:
        """Get actual joint angles."""
        result = self._read6_16bit("ANGLE_ACT")
        return np.array(result, dtype=np.int32)

    def get_angle_set(self) -> npt.NDArray[np.int32]:
        """Get target joint angles."""
        result = self._read6_16bit("ANGLE_SET")
        return np.array(result, dtype=np.int32)

    def get_pos_actual(self) -> npt.NDArray[np.int32]:
        """Get actual joint positions."""
        result = self._read6_16bit("ANGLE_ACT")
        return np.array(result, dtype=np.int32)

    def get_pos_set(self) -> npt.NDArray[np.int32]:
        """Get target joint positions."""
        result = self._read6_16bit("ANGLE_SET")
        return np.array(result, dtype=np.int32)

    def get_speed_set(self) -> npt.NDArray[np.int32]:
        """Get target joint speeds."""
        result = self._read6_16bit("SPEED_SET")
        return np.array(result, dtype=np.int32)

    def get_force_actual(self) -> npt.NDArray[np.int32]:
        """Get actual joint forces."""
        result = self._read6_16bit("FORCE_ACT")
        return np.array(result, dtype=np.int32)

    def get_force_set(self) -> npt.NDArray[np.int32]:
        """Get target joint forces."""
        result = self._read6_16bit("FORCE_SET")
        return np.array(result, dtype=np.int32)

    def get_error(self) -> npt.NDArray[np.int32]:
        """Get error codes."""
        result = self._read6_8bit("ERROR")
        return np.array(result, dtype=np.int32)

    def get_temperature(self) -> npt.NDArray[np.int32]:
        """Get temperature values."""
        result = self._read6_8bit("TEMP")
        return np.array(result, dtype=np.int32)

    def get_temp(self) -> npt.NDArray[np.int32]:
        """Get temperature values (alias)."""
        return self.get_temperature()

    def get_status(self) -> npt.NDArray[np.int32]:
        """Get status codes."""
        result = self._read6_8bit("STATUS")
        return np.array(result, dtype=np.int32)

    def set_action_sequence(self, sequence_id: int) -> bool:
        """Set the action sequence ID."""
        return self._write_register(self._regdict["ACTION_SEQ_INDEX"], [sequence_id])

    def run_action_sequence(self) -> bool:
        """Run the current action sequence."""
        return self._write_register(self._regdict["ACTION_SEQ_RUN"], [1])

    def get_all_tactile_data(self) -> TactileData:
        """
        Get all tactile sensor data as a structured TactileData object.

        Returns:
            TactileData: Structured object containing all tactile sensor data with timestamp

        Raises:
            GenerationError: If not using Gen 4 hardware
        """
        if self._generation != 4:
            raise GenerationError(
                "Tactile sensors are only available in Gen 4 hardware"
            )

        timestamp = time.time()

        tactile_sensors = {
            "PINKY_TOP_TAC": ("pinky", "top"),
            "PINKY_TIP_TAC": ("pinky", "tip"),
            "PINKY_BASE_TAC": ("pinky", "base"),
            "RING_TOP_TAC": ("ring", "top"),
            "RING_TIP_TAC": ("ring", "tip"),
            "RING_BASE_TAC": ("ring", "base"),
            "MIDDLE_TOP_TAC": ("middle", "top"),
            "MIDDLE_TIP_TAC": ("middle", "tip"),
            "MIDDLE_BASE_TAC": ("middle", "base"),
            "INDEX_TOP_TAC": ("index", "top"),
            "INDEX_TIP_TAC": ("index", "tip"),
            "INDEX_BASE_TAC": ("index", "base"),
            "THUMB_TOP_TAC": ("thumb", "top"),
            "THUMB_TIP_TAC": ("thumb", "tip"),
            "THUMB_MID_TAC": ("thumb", "mid"),
            "THUMB_BASE_TAC": ("thumb", "base"),
            "PALM_TAC": ("palm", None),
        }

        sensor_data = {}
        palm_data = None

        for reg_name, (finger, position) in tactile_sensors.items():
            if reg_name not in self._regdict:
                self._logger.warning(f"Tactile sensor register '{reg_name}' not found")
                continue

            address, shape = self._regdict[reg_name]
            rows, cols = shape
            total_elements = rows * cols

            raw_data = self._read_register(address, total_elements)

            if len(raw_data) != total_elements:
                self._logger.error(
                    f"Failed to read complete tactile data for {finger}_{position}: "
                    f"expected {total_elements}, got {len(raw_data)}"
                )
                continue

            is_palm = finger == "palm"
            matrix = reshape_tactile_data(raw_data, rows, cols, is_palm)

            if is_palm:
                palm_data = matrix
            else:
                if finger not in sensor_data:
                    sensor_data[finger] = {}
                sensor_data[finger][position] = matrix

            if self._debug:
                sensor_name = f"{finger}_{position}" if position else finger
                self._logger.debug(
                    f"Read {sensor_name} tactile data: {shape} matrix from address {address}"
                )

        # Create structured finger data objects
        finger_objects = {}
        for finger_name in ["pinky", "ring", "middle", "index"]:
            if finger_name in sensor_data:
                finger_objects[finger_name] = FingerSensorData(
                    top=sensor_data[finger_name].get(
                        "top", np.array([], dtype=np.int32)
                    ),
                    tip=sensor_data[finger_name].get(
                        "tip", np.array([], dtype=np.int32)
                    ),
                    base=sensor_data[finger_name].get(
                        "base", np.array([], dtype=np.int32)
                    ),
                )

        # Create thumb data object
        thumb_data = ThumbSensorData(
            top=sensor_data.get("thumb", {}).get("top", np.array([], dtype=np.int32)),
            tip=sensor_data.get("thumb", {}).get("tip", np.array([], dtype=np.int32)),
            mid=sensor_data.get("thumb", {}).get("mid", np.array([], dtype=np.int32)),
            base=sensor_data.get("thumb", {}).get("base", np.array([], dtype=np.int32)),
        )

        # Create and return the structured TactileData object
        empty_finger = FingerSensorData(
            np.array([], dtype=np.int32),
            np.array([], dtype=np.int32),
            np.array([], dtype=np.int32),
        )

        return TactileData(
            timestamp=timestamp,
            pinky=finger_objects.get("pinky", empty_finger),
            ring=finger_objects.get("ring", empty_finger),
            middle=finger_objects.get("middle", empty_finger),
            index=finger_objects.get("index", empty_finger),
            thumb=thumb_data,
            palm=palm_data if palm_data is not None else np.array([], dtype=np.int32),
        )

    def get_tactile_data(
        self, finger: str, position: str = ""
    ) -> npt.NDArray[np.int32]:
        """
        Get tactile data for a single sensor.

        Args:
            finger: Name of the finger ('pinky', 'ring', 'middle', 'index', 'thumb', 'palm')
            position: Position on finger ('top', 'tip', 'base', 'mid' for thumb only)
                     Not used for palm sensor

        Returns:
            2D numpy array with tactile sensor data

        Raises:
            GenerationError: If not using Gen 4 hardware
            ValidationError: If finger or position is invalid
        """
        if self._generation != 4:
            raise GenerationError(
                "Tactile sensors are only available in Gen 4 hardware"
            )

        # Handle palm sensor
        if finger == "palm":
            reg_name = "PALM_TAC"
            if reg_name not in self._regdict:
                raise ValidationError("Palm sensor register not found")

            address, shape = self._regdict[reg_name]
            rows, cols = shape
            total_elements = rows * cols

            raw_data = self._read_register(address, total_elements)
            if len(raw_data) != total_elements:
                self._logger.error(
                    f"Failed to read complete palm tactile data: "
                    f"expected {total_elements}, got {len(raw_data)}"
                )
                return np.array([], dtype=np.int32)

            return reshape_tactile_data(raw_data, rows, cols, is_palm=True)

        # Validate finger
        if finger not in ["pinky", "ring", "middle", "index", "thumb"]:
            raise ValidationError(
                f"Finger '{finger}' not found. "
                f"Available: pinky, ring, middle, index, thumb, palm"
            )

        # Validate position
        if finger == "thumb":
            valid_positions = ["top", "tip", "mid", "base"]
            if position not in valid_positions:
                raise ValidationError(
                    f"Position '{position}' not valid for thumb. Available: {valid_positions}"
                )
        else:
            valid_positions = ["top", "tip", "base"]
            if position not in valid_positions:
                raise ValidationError(
                    f"Position '{position}' not valid for {finger}. Available: {valid_positions}"
                )

        # Build register name
        reg_name = f"{finger.upper()}_{position.upper()}_TAC"

        if reg_name not in self._regdict:
            raise ValidationError(f"Sensor register '{reg_name}' not found")

        address, shape = self._regdict[reg_name]
        rows, cols = shape
        total_elements = rows * cols

        raw_data = self._read_register(address, total_elements)
        if len(raw_data) != total_elements:
            self._logger.error(
                f"Failed to read complete tactile data for {finger}_{position}: "
                f"expected {total_elements}, got {len(raw_data)}"
            )
            return np.array([], dtype=np.int32)

        matrix = reshape_tactile_data(raw_data, rows, cols, is_palm=False)

        if self._debug:
            self._logger.debug(
                f"Read {finger}_{position} tactile data: {shape} matrix from address {address}"
            )

        return matrix

    def get_ip(self) -> str:
        """Get the configured IP address."""
        return self._ip

    def get_port(self) -> int:
        """Get the configured port."""
        return self._port

    def validate_register_addresses(self) -> dict:
        """
        Validate register addresses by attempting to read from each one.

        Returns:
            Dictionary mapping register names to validation status (True if readable)
        """
        if not self.is_connected():
            self._logger.error(
                "Modbus connection not established. Call connect() first."
            )
            return {}

        validation_results = {}
        test_registers = [
            "HAND_ID",
            "ANGLE_ACT",
            "FORCE_ACT",
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
                if reg_name in ["ERROR", "STATUS", "TEMP"]:
                    result = self._read6_8bit(reg_name)
                else:
                    result = self._read6_16bit(reg_name)

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
                    f"✗ Register '{reg_name}' (addr: {self._regdict[reg_name]}) "
                    f"validation failed: {e}"
                )

        successful_validations = sum(validation_results.values())
        total_validations = len(validation_results)

        self._logger.info(
            f"Register validation complete: {successful_validations}/{total_validations} "
            f"registers accessible"
        )

        if successful_validations < total_validations:
            self._logger.warning(
                "Some registers failed validation. Consider verifying addresses with manufacturer."
            )

        return validation_results
