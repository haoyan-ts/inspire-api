"""Register address mappings for different hardware generations."""

from typing import Dict, Tuple, Union

# Register addresses for Generation 3 hardware
# Note: These addresses are verified through reverse engineering
# Use validation methods for manufacturer verification
REGISTERS_GEN3: Dict[str, int] = {
    "HAND_ID": 1000,
    "REDU_RATIO": 1001,
    "CLEAR_ERROR": 1004,
    "SAVE": 1005,
    "RESET_PARA": 1006,
    "GESTURE_FORCE_CLB": 1009,
    "CURRENT_LIMIT": 1020,
    "DEFAULT_SPEED_SET": 1032,
    "DEFAULT_FORCE_SET": 1044,
    "VLTAGE": 1472,
    "POS_SET": 1474,
    "ANGLE_SET": 1486,
    "FORCE_SET": 1498,
    "SPEED_SET": 1522,
    "POS_ACT": 1534,
    "ANGLE_ACT": 1546,
    "FORCE_ACT": 1582,
    "CURRENT": 1594,
    "ERROR": 1606,
    "STATUS": 1612,
    "TEMP": 1618,
    "ACTION_SEQ_CHECKDATA1": 2000,
    "ACTION_SEQ_CHECKDATA2": 2001,
    "ACTION_SEQ_STEPNUM": 2002,
    "ACTION_SEQ_STEP0": 2016,
    "ACTION_SEQ_STEP1": 2054,
    "ACTION_SEQ_STEP2": 2092,
    "ACTION_SEQ_STEP3": 2130,
    "ACTION_SEQ_STEP4": 2168,
    "ACTION_SEQ_STEP5": 2206,
    "ACTION_SEQ_STEP6": 2244,
    "ACTION_SEQ_STEP7": 2282,
    "ACTION_SEQ_INDEX": 2320,
    "SAVE_ACTION_SEQ": 2321,
    "ACTION_SEQ_RUN": 2322,
    "ACTION_ADJUST_FORCE_SET": 2334,
}

# Register addresses for Generation 4 hardware
# Includes all Gen3 registers plus tactile sensors and network config
REGISTERS_GEN4: Dict[str, Union[int, Tuple[int, Tuple[int, int]]]] = {
    "HAND_ID": 1000,
    "REDU_RATIO": 1001,
    "CLEAR_ERROR": 1004,
    "SAVE": 1005,
    "RESET_PARA": 1006,
    "GESTURE_FORCE_CLB": 1009,
    "DEFAULT_SPEED_SET": 1032,
    "DEFAULT_FORCE_SET": 1044,
    "POS_SET": 1474,
    "ANGLE_SET": 1486,
    "FORCE_SET": 1498,
    "SPEED_SET": 1522,
    "POS_ACT": 1534,
    "ANGLE_ACT": 1546,
    "FORCE_ACT": 1582,
    "CURRENT": 1594,
    "ERROR": 1606,
    "STATUS": 1612,
    "TEMP": 1618,
    "IP_PART1": 1700,
    "IP_PART2": 1701,
    "IP_PART3": 1702,
    "IP_PART4": 1703,
    # Tactile sensor registers: (address, (rows, cols))
    "PINKY_TOP_TAC": (3000, (3, 3)),
    "PINKY_TIP_TAC": (3018, (12, 8)),
    "PINKY_BASE_TAC": (3210, (10, 8)),
    "RING_TOP_TAC": (3370, (3, 3)),
    "RING_TIP_TAC": (3388, (12, 8)),
    "RING_BASE_TAC": (3580, (10, 8)),
    "MIDDLE_TOP_TAC": (3740, (3, 3)),
    "MIDDLE_TIP_TAC": (3758, (12, 8)),
    "MIDDLE_BASE_TAC": (3950, (10, 8)),
    "INDEX_TOP_TAC": (4110, (3, 3)),
    "INDEX_TIP_TAC": (4128, (12, 8)),
    "INDEX_BASE_TAC": (4320, (10, 8)),
    "THUMB_TOP_TAC": (4480, (3, 3)),
    "THUMB_TIP_TAC": (4498, (12, 8)),
    "THUMB_MID_TAC": (4690, (3, 3)),
    "THUMB_BASE_TAC": (4708, (10, 8)),
    "PALM_TAC": (4900, (8, 14)),
}


def get_registers(
    generation: int,
) -> Dict[str, Union[int, Tuple[int, Tuple[int, int]]]]:
    """
    Get the appropriate register dictionary for the given hardware generation.

    Args:
        generation: Hardware generation (3 or 4)

    Returns:
        Dictionary mapping register names to addresses (and shapes for tactile sensors)

    Raises:
        ValueError: If generation is not supported
    """
    if generation == 3:
        return REGISTERS_GEN3  # type: ignore
    elif generation == 4:
        return REGISTERS_GEN4
    else:
        raise ValueError(
            f"Unsupported hardware generation: {generation}. Must be 3 or 4."
        )


def categorize_register(reg_name: str) -> str:
    """
    Categorize a register by its function.

    Args:
        reg_name: Name of the register

    Returns:
        Category name as string
    """
    if reg_name in ["HAND_ID", "REDU_RATIO", "CLEAR_ERROR", "SAVE", "RESET_PARA"]:
        return "system_control"
    elif reg_name in ["ANGLE_SET", "POS_SET", "FORCE_SET", "SPEED_SET"]:
        return "actuator_commands"
    elif reg_name in [
        "ANGLE_ACT",
        "POS_ACT",
        "FORCE_ACT",
        "CURRENT",
        "ERROR",
        "STATUS",
        "TEMP",
    ]:
        return "sensor_readings"
    elif reg_name.startswith("ACTION_SEQ"):
        return "action_sequences"
    elif reg_name.endswith("_TAC"):
        return "touch_sensors"
    elif reg_name.startswith("IP_"):
        return "network_config"
    else:
        return "other"


def validate_register_address(
    reg_name: str, generation: int
) -> Union[int, Tuple[int, Tuple[int, int]]]:
    """
    Validate and get the address for a register.

    Args:
        reg_name: Name of the register
        generation: Hardware generation

    Returns:
        Register address (or tuple with address and shape for tactile sensors)

    Raises:
        ValueError: If register is not valid for the generation
    """
    registers = get_registers(generation)
    if reg_name not in registers:
        raise ValueError(
            f"Register '{reg_name}' not valid for generation {generation}. "
            f"Available registers: {list(registers.keys())}"
        )
    return registers[reg_name]
