"""
Context-aware variable naming for the decompiler.
"""

import re
from typing import Dict, Optional

from .models import DOSFunction, Variable


# Common variable name prefixes based on usage patterns
VARIABLE_PREFIXES = {
    # Loop counters
    "counter": ["i", "j", "k", "n", "count"],
    # Pointers
    "pointer": ["ptr", "p", "ref"],
    # Flags
    "flag": ["flag", "is", "has", "can", "should"],
    # Indices
    "index": ["idx", "index", "pos", "position"],
    # Sizes
    "size": ["size", "len", "length", "width", "height"],
    # Coordinates
    "coordinate": ["x", "y", "z", "row", "col"],
    # Common data types
    "string": ["str", "string", "text", "name"],
    "number": ["num", "value", "val", "amount"],
    "character": ["ch", "char", "c"],
    "boolean": ["b", "bool", "flag"],
    # Game-specific
    "player": ["player", "user", "character"],
    "score": ["score", "points", "value"],
    "health": ["health", "hp", "life"],
    "inventory": ["inv", "item", "items"],
    "position": ["pos", "location", "loc"],
    "direction": ["dir", "heading", "facing"],
    "time": ["time", "date", "day", "month", "year"],
    "money": ["money", "cash", "dollars", "cents"],
    "food": ["food", "rations", "supplies"],
    "wagon": ["wagon", "cart", "vehicle"],
    "oxen": ["oxen", "ox", "animals"],
    "river": ["river", "water", "depth", "current"],
    "weather": ["weather", "temp", "temperature", "climate"],
    "distance": ["dist", "distance", "miles", "traveled"],
    "pace": ["pace", "speed", "rate"],
    "event": ["event", "occurrence", "happening"],
    "menu": ["menu", "option", "choice"],
    "screen": ["screen", "display", "view"],
    "message": ["msg", "message", "text"],
}

# Common variable name suffixes based on type
VARIABLE_SUFFIXES = {
    "int": [
        "_i",
        "_int",
        "_count",
        "_num",
        "_val",
        "_value",
        "_index",
        "_size",
        "_len",
        "_id",
    ],
    "char": ["_c", "_char", "_byte", "_flag"],
    "int[]": ["_array", "_list", "_table", "_buffer", "_buf", "_data"],
    "char[]": ["_str", "_string", "_text", "_name", "_msg", "_message"],
    "struct": ["_struct", "_record", "_obj", "_object", "_data"],
}

# Common register usage patterns
REGISTER_USAGE = {
    "ax": "result",  # Return value or accumulator
    "bx": "base",  # Base address or pointer
    "cx": "count",  # Counter or loop variable
    "dx": "data",  # Data or second part of result
    "si": "source",  # Source index for string operations
    "di": "dest",  # Destination index for string operations
    "bp": "frame",  # Base pointer for stack frame
    "sp": "stack",  # Stack pointer
}

# Memory address ranges and their likely meanings in Oregon Trail
MEMORY_RANGES = {
    (0x5C00, 0x5CFF): "game_state",
    (0x5D00, 0x5DFF): "player_data",
    (0x5E00, 0x5EFF): "inventory",
    (0x5F00, 0x5FFF): "event_data",
    (0x6000, 0x60FF): "menu_data",
    (0x6100, 0x61FF): "screen_data",
    (0x6200, 0x62FF): "message_data",
}


def get_memory_range_name(address: int) -> Optional[str]:
    """Get the name of the memory range containing the address"""
    for (start, end), name in MEMORY_RANGES.items():
        if start <= address <= end:
            return name
    return None


def get_variable_usage_pattern(var: Variable, function: DOSFunction) -> str:
    """
    Determine the usage pattern of a variable based on how it's used in the function.

    Args:
        var: The variable to analyze
        function: The function containing the variable

    Returns:
        A string describing the usage pattern
    """
    # Default pattern
    pattern = "unknown"

    # Check if it's a register variable
    if var.register:
        return REGISTER_USAGE.get(var.register, "register")

    # Check if it's in a known memory range
    if var.address:
        range_name = get_memory_range_name(var.address)
        if range_name:
            return range_name

    # Analyze instructions that reference this variable
    loop_counter = False
    array_index = False
    flag = False
    string_var = False
    pointer = False

    for instr in function.instructions:
        # Check if the variable is used in this instruction
        if var.address and f"0x{var.address:X}" in instr.operands:
            # Check for loop counter pattern
            if instr.mnemonic in ["inc", "dec", "add", "sub"]:
                loop_counter = True

            # Check for array index pattern
            if "+" in instr.operands:
                array_index = True

            # Check for flag pattern
            if instr.mnemonic in ["test", "cmp"]:
                flag = True

            # Check for string pattern
            if instr.mnemonic in ["movsb", "movsw", "stosb", "stosw", "lodsb", "lodsw"]:
                string_var = True

            # Check for pointer pattern
            if "ptr" in instr.operands:
                pointer = True

    # Determine the most likely pattern
    if loop_counter:
        pattern = "counter"
    elif array_index:
        pattern = "index"
    elif flag:
        pattern = "flag"
    elif string_var:
        pattern = "string"
    elif pointer:
        pattern = "pointer"

    return pattern


def generate_variable_name(var: Variable, function: DOSFunction) -> str:
    """
    Generate a meaningful name for a variable based on its usage and type.

    Args:
        var: The variable to name
        function: The function containing the variable

    Returns:
        A meaningful variable name
    """
    # Start with the original name
    name = var.name

    # If it's a register variable, use the register usage pattern
    if var.register:
        reg_usage = REGISTER_USAGE.get(var.register, "reg")
        return f"{reg_usage}_{var.register}"

    # If it's a DOS variable, keep the original name
    if name.startswith("dos_"):
        return name

    # Determine the usage pattern
    usage_pattern = get_variable_usage_pattern(var, function)

    # Get prefixes for this usage pattern
    prefixes = VARIABLE_PREFIXES.get(usage_pattern, ["var"])

    # Get suffixes for this type
    suffixes = VARIABLE_SUFFIXES.get(var.type, [""])

    # If it's in a known memory range, use that as a prefix
    if var.address:
        range_name = get_memory_range_name(var.address)
        if range_name:
            prefixes = [range_name]

    # Generate a name based on prefix, address, and suffix
    if var.address:
        # Use the first prefix and first suffix
        prefix = prefixes[0]
        suffix = suffixes[0] if suffixes else ""

        # Include the address in the name for uniqueness
        addr_part = (
            f"{var.address & 0xFF:02X}"  # Use only the last 2 digits of the address
        )

        return f"{prefix}_{addr_part}{suffix}"
    else:
        # For non-memory variables, just use the first prefix
        return f"{prefixes[0]}"


def rename_variables(function: DOSFunction) -> Dict[str, str]:
    """
    Rename all variables in a function to more meaningful names.

    Args:
        function: The function containing the variables

    Returns:
        A dictionary mapping original names to new names
    """
    name_map = {}

    for var_name, var in function.variables.items():
        new_name = generate_variable_name(var, function)
        name_map[var_name] = new_name
        var.name = new_name

    return name_map


def apply_variable_renaming(code: str, name_map: Dict[str, str]) -> str:
    """
    Apply variable renaming to a code string.

    Args:
        code: The code string to modify
        name_map: A dictionary mapping original names to new names

    Returns:
        The modified code string
    """
    result = code

    # Sort the name map by length of original name (longest first)
    # This ensures that we replace longer names before shorter ones
    # to avoid partial replacements
    sorted_names = sorted(name_map.items(), key=lambda x: len(x[0]), reverse=True)

    for old_name, new_name in sorted_names:
        # Replace the variable name, but only if it's a whole word
        result = re.sub(r"\b" + re.escape(old_name) + r"\b", new_name, result)

    return result
