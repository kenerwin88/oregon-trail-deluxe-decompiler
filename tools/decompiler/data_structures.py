"""
Data structure detection and reconstruction for the decompiler.
"""

import re
from typing import Dict, List, Tuple

from .models import DOSFunction


class StructField:
    """Represents a field in a struct"""

    def __init__(self, name: str, type: str, offset: int, size: int):
        self.name = name
        self.type = type
        self.offset = offset
        self.size = size

    def __str__(self):
        return f"{self.type} {self.name}; // offset: {self.offset}, size: {self.size}"


class StructDefinition:
    """Represents a struct definition"""

    def __init__(self, name: str, size: int = 0):
        self.name = name
        self.size = size
        self.fields: List[StructField] = []

    def add_field(self, field: StructField):
        self.fields.append(field)
        # Update struct size if needed
        if field.offset + field.size > self.size:
            self.size = field.offset + field.size

    def __str__(self):
        result = f"struct {self.name} {{ // size: {self.size}\n"
        for field in sorted(self.fields, key=lambda f: f.offset):
            result += f"    {field}\n"
        result += "};"
        return result


class ArrayDefinition:
    """Represents an array definition"""

    def __init__(self, name: str, element_type: str, element_size: int, length: int):
        self.name = name
        self.element_type = element_type
        self.element_size = element_size
        self.length = length

    def __str__(self):
        return f"{self.element_type} {self.name}[{self.length}]; // element size: {self.element_size}"


# Common data structures in Oregon Trail
OREGON_TRAIL_STRUCTS = {
    "player_data": {
        "size": 32,
        "fields": [
            {"name": "name", "type": "char", "offset": 0, "size": 16},
            {"name": "health", "type": "int", "offset": 16, "size": 2},
            {"name": "money", "type": "int", "offset": 18, "size": 2},
            {"name": "food", "type": "int", "offset": 20, "size": 2},
            {"name": "oxen", "type": "int", "offset": 22, "size": 2},
            {"name": "clothing", "type": "int", "offset": 24, "size": 2},
            {"name": "ammunition", "type": "int", "offset": 26, "size": 2},
            {"name": "spare_parts", "type": "int", "offset": 28, "size": 2},
            {"name": "status", "type": "int", "offset": 30, "size": 2},
        ],
    },
    "game_state": {
        "size": 64,
        "fields": [
            {"name": "day", "type": "int", "offset": 0, "size": 2},
            {"name": "month", "type": "int", "offset": 2, "size": 2},
            {"name": "year", "type": "int", "offset": 4, "size": 2},
            {"name": "distance", "type": "int", "offset": 6, "size": 2},
            {"name": "weather", "type": "int", "offset": 8, "size": 2},
            {"name": "pace", "type": "int", "offset": 10, "size": 2},
            {"name": "rations", "type": "int", "offset": 12, "size": 2},
            {"name": "location_id", "type": "int", "offset": 14, "size": 2},
            {"name": "next_landmark", "type": "int", "offset": 16, "size": 2},
            {"name": "landmark_distance", "type": "int", "offset": 18, "size": 2},
            {"name": "river_depth", "type": "int", "offset": 20, "size": 2},
            {"name": "river_width", "type": "int", "offset": 22, "size": 2},
            {"name": "current_screen", "type": "int", "offset": 24, "size": 2},
            {"name": "event_flags", "type": "int", "offset": 26, "size": 2},
            {"name": "player_count", "type": "int", "offset": 28, "size": 2},
            {"name": "active_player", "type": "int", "offset": 30, "size": 2},
        ],
    },
    "inventory": {
        "size": 16,
        "fields": [
            {"name": "food", "type": "int", "offset": 0, "size": 2},
            {"name": "oxen", "type": "int", "offset": 2, "size": 2},
            {"name": "clothing", "type": "int", "offset": 4, "size": 2},
            {"name": "ammunition", "type": "int", "offset": 6, "size": 2},
            {"name": "wheels", "type": "int", "offset": 8, "size": 2},
            {"name": "axles", "type": "int", "offset": 10, "size": 2},
            {"name": "tongues", "type": "int", "offset": 12, "size": 2},
            {"name": "money", "type": "int", "offset": 14, "size": 2},
        ],
    },
    "landmark": {
        "size": 32,
        "fields": [
            {"name": "name", "type": "char", "offset": 0, "size": 16},
            {"name": "distance", "type": "int", "offset": 16, "size": 2},
            {"name": "type", "type": "int", "offset": 18, "size": 2},
            {"name": "event_id", "type": "int", "offset": 20, "size": 2},
            {"name": "message_id", "type": "int", "offset": 22, "size": 2},
            {"name": "graphic_id", "type": "int", "offset": 24, "size": 2},
            {"name": "flags", "type": "int", "offset": 26, "size": 2},
        ],
    },
    "event": {
        "size": 16,
        "fields": [
            {"name": "type", "type": "int", "offset": 0, "size": 2},
            {"name": "probability", "type": "int", "offset": 2, "size": 2},
            {"name": "message_id", "type": "int", "offset": 4, "size": 2},
            {"name": "effect_type", "type": "int", "offset": 6, "size": 2},
            {"name": "effect_amount", "type": "int", "offset": 8, "size": 2},
            {"name": "flags", "type": "int", "offset": 10, "size": 2},
        ],
    },
}


def detect_struct_access(
    function: DOSFunction,
) -> Dict[int, Dict[int, Tuple[str, int]]]:
    """
    Detect struct accesses in a function.

    Args:
        function: The function to analyze

    Returns:
        A dictionary mapping base addresses to field accesses
    """
    struct_accesses = {}

    # Check if we have instructions
    if not function.instructions:
        return struct_accesses

    # Look for memory accesses with offsets
    for instr in function.instructions:
        # Look for base+offset patterns
        if "+" in instr.operands:
            parts = instr.operands.split("+")
            if len(parts) == 2:
                base_part = parts[0].strip()
                offset_part = parts[1].strip()

                # Extract base address
                base_match = re.search(r"\[([^\]]+)\]", base_part)
                if base_match:
                    base_str = base_match.group(1)
                    try:
                        if base_str.startswith("0x"):
                            base_addr = int(base_str, 16)
                        else:
                            base_addr = int(base_str)

                        # Extract offset
                        offset_match = re.search(r"(\d+)", offset_part)
                        if offset_match:
                            offset = int(offset_match.group(1))

                            # Determine access size
                            size = 1  # Default to byte
                            if "word" in instr.operands:
                                size = 2
                            elif "dword" in instr.operands:
                                size = 4

                            # Add to struct accesses
                            if base_addr not in struct_accesses:
                                struct_accesses[base_addr] = {}
                            struct_accesses[base_addr][offset] = (instr.mnemonic, size)
                    except ValueError:
                        pass

    return struct_accesses


def detect_array_access(function: DOSFunction) -> Dict[int, Tuple[int, int]]:
    """
    Detect array accesses in a function.

    Args:
        function: The function to analyze

    Returns:
        A dictionary mapping base addresses to (element_size, max_index)
    """
    array_accesses = {}

    # Check if we have instructions
    if not function.instructions:
        return array_accesses

    # Look for indexed memory accesses
    for instr in function.instructions:
        # Look for base+index patterns
        if "+" in instr.operands and any(
            reg in instr.operands for reg in ["si", "di", "bx"]
        ):
            parts = instr.operands.split("+")
            if len(parts) == 2:
                base_part = parts[0].strip()
                index_part = parts[1].strip()

                # Extract base address
                base_match = re.search(r"\[([^\]]+)\]", base_part)
                if base_match:
                    base_str = base_match.group(1)
                    try:
                        if base_str.startswith("0x"):
                            base_addr = int(base_str, 16)
                        else:
                            base_addr = int(base_str)

                        # Determine access size
                        size = 1  # Default to byte
                        if "word" in instr.operands:
                            size = 2
                        elif "dword" in instr.operands:
                            size = 4

                        # Add to array accesses
                        if base_addr not in array_accesses:
                            array_accesses[base_addr] = (size, 0)
                        else:
                            curr_size, curr_max = array_accesses[base_addr]
                            array_accesses[base_addr] = (size, curr_max)
                    except ValueError:
                        pass

    return array_accesses


def identify_known_structs(
    struct_accesses: Dict[int, Dict[int, Tuple[str, int]]],
) -> Dict[int, str]:
    """
    Identify known structs based on access patterns.

    Args:
        struct_accesses: Dictionary of struct accesses

    Returns:
        Dictionary mapping base addresses to struct names
    """
    known_structs = {}

    for base_addr, fields in struct_accesses.items():
        # Check each known struct
        for struct_name, struct_info in OREGON_TRAIL_STRUCTS.items():
            # Count matching fields
            matches = 0
            for field_info in struct_info["fields"]:
                offset = field_info["offset"]
                if offset in fields:
                    matches += 1

            # If more than half the fields match, consider it a match
            if matches >= len(struct_info["fields"]) / 2:
                known_structs[base_addr] = struct_name
                break

    return known_structs


def create_struct_definitions(
    struct_accesses: Dict[int, Dict[int, Tuple[str, int]]],
    known_structs: Dict[int, str],
) -> Dict[int, StructDefinition]:
    """
    Create struct definitions based on access patterns.

    Args:
        struct_accesses: Dictionary of struct accesses
        known_structs: Dictionary of known struct names

    Returns:
        Dictionary of struct definitions
    """
    struct_defs = {}

    for base_addr, fields in struct_accesses.items():
        # Check if it's a known struct
        if base_addr in known_structs:
            struct_name = known_structs[base_addr]
            struct_info = OREGON_TRAIL_STRUCTS[struct_name]

            # Create struct definition
            struct_def = StructDefinition(struct_name, struct_info["size"])

            # Add fields
            for field_info in struct_info["fields"]:
                field = StructField(
                    name=field_info["name"],
                    type=field_info["type"],
                    offset=field_info["offset"],
                    size=field_info["size"],
                )
                struct_def.add_field(field)

            struct_defs[base_addr] = struct_def
        else:
            # Create a new struct definition
            struct_name = f"struct_{base_addr:04X}"
            struct_def = StructDefinition(struct_name)

            # Add fields
            for offset, (access_type, size) in fields.items():
                field_type = "int" if size == 2 else "char" if size == 1 else "long"
                field = StructField(
                    name=f"field_{offset:02X}",
                    type=field_type,
                    offset=offset,
                    size=size,
                )
                struct_def.add_field(field)

            struct_defs[base_addr] = struct_def

    return struct_defs


def create_array_definitions(
    array_accesses: Dict[int, Tuple[int, int]],
) -> Dict[int, ArrayDefinition]:
    """
    Create array definitions based on access patterns.

    Args:
        array_accesses: Dictionary of array accesses

    Returns:
        Dictionary of array definitions
    """
    array_defs = {}

    for base_addr, (element_size, max_index) in array_accesses.items():
        # Determine element type
        element_type = (
            "int" if element_size == 2 else "char" if element_size == 1 else "long"
        )

        # Estimate array length (max_index is often not reliable, so use a default)
        length = max(max_index + 1, 16)  # Default to at least 16 elements

        # Create array definition
        array_name = f"array_{base_addr:04X}"
        array_def = ArrayDefinition(
            name=array_name,
            element_type=element_type,
            element_size=element_size,
            length=length,
        )

        array_defs[base_addr] = array_def

    return array_defs


def analyze_data_structures(
    function: DOSFunction,
) -> Tuple[Dict[int, StructDefinition], Dict[int, ArrayDefinition]]:
    """
    Analyze a function to detect data structures.

    Args:
        function: The function to analyze

    Returns:
        A tuple of (struct_definitions, array_definitions)
    """
    # Detect struct accesses
    struct_accesses = detect_struct_access(function)

    # Identify known structs
    known_structs = identify_known_structs(struct_accesses)

    # Create struct definitions
    struct_defs = create_struct_definitions(struct_accesses, known_structs)

    # Detect array accesses
    array_accesses = detect_array_access(function)

    # Create array definitions
    array_defs = create_array_definitions(array_accesses)

    return struct_defs, array_defs


def update_function_with_data_structures(function: DOSFunction):
    """
    Update a function with detected data structures.

    Args:
        function: The function to update
    """
    # Analyze data structures
    struct_defs, array_defs = analyze_data_structures(function)

    # Add struct definitions to function
    function.struct_defs = struct_defs

    # Add array definitions to function
    function.array_defs = array_defs

    # Update variables that are struct or array accesses
    for var_name, var in function.variables.items():
        if var.address in struct_defs:
            var.type = struct_defs[var.address].name
            var.is_struct = True
        elif var.address in array_defs:
            var.type = array_defs[var.address].element_type + "[]"
            var.is_array = True
