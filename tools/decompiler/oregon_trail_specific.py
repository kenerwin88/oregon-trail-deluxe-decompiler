"""
Oregon Trail specific code analysis and transformation module.

This module provides game-specific knowledge integration for the Oregon Trail
decompilation process, enhancing the output with meaningful names, structures,
and patterns relevant to the game.
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple

from .constants import (
    GAME_STATES, MEMORY_ADDRESSES, GRAPHICS_ADDRESSES, SOUND_ADDRESSES, 
    INPUT_ADDRESSES, OREGON_TRAIL_PATTERNS, PROFESSIONS, WEATHER_CONDITIONS,
    PACE_SETTINGS, RATION_SETTINGS, RIVER_CROSSING_METHODS, LANDMARKS,
    EVENTS, ILLNESSES, MONTHS, ITEM_TYPES
)
from .enhanced_output import enhance_code_with_game_knowledge as enhance_with_game_knowledge
from .models import DOSFunction, X86Instruction

# Configure logger
logger = logging.getLogger(__name__)

# Game-specific data structures
OREGON_TRAIL_STRUCTS = {
    "Player": {
        "name": "char[20]",
        "health": "int",
        "illness": "int",
        "status": "int",
        "profession": "int"
    },
    "Wagon": {
        "oxen": "int",
        "food": "int",
        "clothing": "int",
        "ammunition": "int",
        "spare_parts": "int",
        "money": "int",
        "distance_traveled": "int"
    },
    "GameState": {
        "state": "int",
        "month": "int",
        "day": "int",
        "year": "int",
        "miles_traveled": "int",
        "weather": "int",
        "health": "int",
        "pace": "int",
        "rations": "int",
        "players": "Player[5]"
    },
    "Landmark": {
        "name": "char[20]",
        "distance": "int",
        "type": "int"
    },
    "Event": {
        "type": "int",
        "message": "char[100]",
        "options": "char[4][20]",
        "consequences": "int[4]"
    }
}

# Common game function patterns
OREGON_TRAIL_FUNCTION_PATTERNS = {
    # Format: (pattern, (function_name, return_type, parameters, description))
    r"mov\s+ax,\s*word\s+ptr\s+\[0x5c08\].*add\s+ax": (
        "update_distance_traveled", "void", [], 
        "Updates the total distance traveled on the trail"
    ),
    r"mov\s+ax,\s*word\s+ptr\s+\[0x5c0c\].*add\s+ax": (
        "update_weather", "int", ["int weather_factor"], 
        "Updates the current weather conditions"
    ),
    r"mov\s+ax,\s*word\s+ptr\s+\[0x5c0e\].*sub\s+ax": (
        "update_health", "int", ["int player_index", "int health_change"],
        "Updates the health of a player based on conditions"
    ),
    r"mov\s+ax,\s*word\s+ptr\s+\[0x5c14\].*sub\s+ax": (
        "consume_food", "int", ["int amount"],
        "Consumes a specified amount of food"
    ),
    r"mov\s+ax,\s*word\s+ptr\s+\[0x5c16\].*sub\s+ax": (
        "spend_money", "int", ["int amount"], 
        "Spends money and updates the player's balance"
    ),
    r"mov\s+word\s+ptr\s+\[0x5c28\],": (
        "set_landmark", "void", ["int landmark_index"],
        "Sets the current landmark location"
    ),
    r"int\s+0x33.*mov\s+ax,\s*0x3": (
        "get_mouse_position", "void", ["int* x", "int* y", "int* buttons"],
        "Gets the current mouse position and button state"
    ),
    r"int\s+0x21.*mov\s+ah,\s*0x3d": (
        "open_file", "int", ["char* filename", "int mode"],
        "Opens a file and returns a file handle"
    ),
    r"int\s+0x21.*mov\s+ah,\s*0x3f": (
        "read_file", "int", ["int handle", "void* buffer", "int count"],
        "Reads data from a file into a buffer"
    ),
    r"int\s+0x21.*mov\s+ah,\s*0x40": (
        "write_file", "int", ["int handle", "void* buffer", "int count"],
        "Writes data from a buffer to a file"
    ),
    r"int\s+0x10.*mov\s+ah,\s*0x13": (
        "write_string", "void", ["char* string", "int row", "int col", "int color"],
        "Writes a string to the screen at a specified position"
    ),
    r"int\s+0x10.*mov\s+ah,\s*0x0e": (
        "write_char", "void", ["char c", "int color"],
        "Writes a character to the screen in teletype mode"
    )
}

def identify_game_function(function_name, instructions_text):
    """
    Identify game-specific function based on name and instructions.
    
    Args:
        function_name: Name of the function
        instructions_text: List of instruction text or a single string
        
    Returns:
        Function purpose if identified, None otherwise
    """
    # Look for specific function names
    if function_name.startswith("sub_"):
        # For sub_XXXX functions, need to rely on instruction patterns
        pass
    elif "main" in function_name.lower():
        return "Main game loop"
    elif "init" in function_name.lower():
        return "Initialization routine"
    elif "update" in function_name.lower():
        return "State update routine"
    elif "draw" in function_name.lower() or "render" in function_name.lower():
        return "Graphics rendering routine"
    elif "input" in function_name.lower() or "keyboard" in function_name.lower():
        return "Input handling routine"
    elif "sound" in function_name.lower() or "audio" in function_name.lower():
        return "Sound/audio routine"
    elif "save" in function_name.lower():
        return "Game save routine"
    elif "load" in function_name.lower():
        return "Game load routine"
    elif "menu" in function_name.lower():
        return "Menu handling routine"
    elif "event" in function_name.lower():
        return "Event processing routine"
    elif "hunt" in function_name.lower():
        return "Hunting mini-game routine"
    elif "river" in function_name.lower():
        return "River crossing routine"
    elif "trading" in function_name.lower() or "trade" in function_name.lower():
        return "Trading post routine"
    elif "landmark" in function_name.lower():
        return "Landmark interaction routine"
    
    # Convert instructions to a single string if it's a list
    if isinstance(instructions_text, list):
        instructions_joined = " ".join(instructions_text)
    else:
        instructions_joined = instructions_text
    
    # Check for specialized function patterns
    for pattern, func_info in OREGON_TRAIL_FUNCTION_PATTERNS.items():
        if re.search(pattern, instructions_joined, re.IGNORECASE):
            func_name, return_type, params, desc = func_info
            return desc
    
    # Check for more general patterns
    for pattern, desc in OREGON_TRAIL_PATTERNS.items():
        if re.search(pattern, instructions_joined, re.IGNORECASE):
            return desc
            
    return None

def enhance_function_signature(function):
    """
    Enhance a function's signature with game-specific knowledge.
    
    Args:
        function: The function to enhance
        
    Returns:
        True if enhancements were made, False otherwise
    """
    if not hasattr(function, "instructions") or not function.instructions:
        return False
    
    # Get the instruction text
    instructions_text = [f"{instr.mnemonic} {instr.operands}" for instr in function.instructions]
    instructions_joined = " ".join(instructions_text)
    
    # Check for specialized function patterns
    for pattern, func_info in OREGON_TRAIL_FUNCTION_PATTERNS.items():
        if re.search(pattern, instructions_joined, re.IGNORECASE):
            func_name, return_type, params, desc = func_info
            
            # Build parameter string
            param_str = ", ".join(params) if params else "void"
            
            # Update function
            function.name = func_name
            function.signature = f"{return_type} {func_name}({param_str})"
            function.purpose = desc
            function.parameters = params
            function.return_type = return_type
            return True
            
    return False

def identify_game_data_structures(function):
    """
    Identify game-specific data structures used in a function.
    
    Args:
        function: The function to analyze
        
    Returns:
        Dictionary mapping memory addresses to structure information
    """
    if not hasattr(function, "instructions") or not function.instructions:
        return {}
    
    structs = {}
    
    # Look for memory accesses to known game structures
    for instr in function.instructions:
        if instr.mnemonic in ["mov", "add", "sub", "cmp"]:
            # Check for memory address patterns
            for addr, name in MEMORY_ADDRESSES.items():
                addr_str = f"0x{addr:X}"
                
                # Check if the address is in the operands
                if addr_str in instr.operands or addr_str.lower() in instr.operands:
                    # Determine what structure this is part of
                    struct_type = None
                    if "game_state" in name:
                        struct_type = "GameState"
                    elif "player" in name:
                        struct_type = "Player"
                    elif "wagon" in name or "oxen" in name or "food" in name:
                        struct_type = "Wagon"
                    elif "landmark" in name:
                        struct_type = "Landmark"
                    elif "event" in name:
                        struct_type = "Event"
                    
                    if struct_type:
                        structs[addr] = {
                            "name": name,
                            "type": struct_type,
                            "info": OREGON_TRAIL_STRUCTS.get(struct_type, {})
                        }
    
    return structs

def enhance_instruction_with_game_knowledge(instr):
    """
    Enhance an instruction with game-specific knowledge.
    
    Args:
        instr: The instruction to enhance
        
    Returns:
        Enhanced instruction text
    """
    # Start with the original instruction text
    text = f"{instr.mnemonic} {instr.operands}"
    
    # Replace memory addresses with meaningful names
    for addr, name in MEMORY_ADDRESSES.items():
        addr_str = f"0x{addr:X}"
        
        # Replace with brackets
        pattern_brackets = r"\[\s*" + re.escape(addr_str) + r"\s*\]"
        if re.search(pattern_brackets, text, re.IGNORECASE):
            text = re.sub(pattern_brackets, f"[{name}]", text, flags=re.IGNORECASE)
        
        # Replace without brackets
        pattern_no_brackets = r"(?<!\[)\b" + re.escape(addr_str) + r"\b(?!\])"
        if re.search(pattern_no_brackets, text, re.IGNORECASE):
            text = re.sub(pattern_no_brackets, name, text, flags=re.IGNORECASE)
    
    # Check for specific game values
    # Game state comparisons
    if "game_state" in text:
        for state_val, state_name in GAME_STATES.items():
            pattern = r"cmp\s+.*\[game_state\],\s*" + str(state_val) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                if not hasattr(instr, "comment") or not instr.comment:
                    instr.comment = f"Compare game state to {state_name}"
    
    # Profession checks
    if "profession" in text:
        for prof_val, prof_name in PROFESSIONS.items():
            pattern = r"cmp\s+.*\[.*profession.*\],\s*" + str(prof_val) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                if not hasattr(instr, "comment") or not instr.comment:
                    instr.comment = f"Check if profession is {prof_name}"
    
    # Weather conditions
    if "weather" in text:
        for weather_val, weather_name in WEATHER_CONDITIONS.items():
            pattern = r"cmp\s+.*\[.*weather.*\],\s*" + str(weather_val) + r"\b"
            if re.search(pattern, text, re.IGNORECASE):
                if not hasattr(instr, "comment") or not instr.comment:
                    instr.comment = f"Check if weather is {weather_name}"
    
    return text

def generate_game_structures():
    """
    Generate C structure definitions for game-specific data structures.
    
    Returns:
        String containing C struct definitions
    """
    structs = []
    
    for struct_name, fields in OREGON_TRAIL_STRUCTS.items():
        struct_def = f"typedef struct {struct_name} {{\n"
        
        for field_name, field_type in fields.items():
            struct_def += f"    {field_type} {field_name};\n"
        
        struct_def += f"}} {struct_name};\n\n"
        structs.append(struct_def)
    
    return "".join(structs)

def enhance_c_code_with_game_knowledge(c_code, functions):
    """
    Enhance C code with game-specific knowledge.
    
    Args:
        c_code: The C code to enhance
        functions: List of functions
        
    Returns:
        Enhanced C code
    """
    enhanced = c_code
    
    # First, apply the standard enhancements
    enhanced = enhance_with_game_knowledge(enhanced)
    
    # Add game-specific structure definitions
    game_structures = generate_game_structures()
    
    # Insert the structures after the include section
    include_pattern = r"(#include.*\n)+"
    match = re.search(include_pattern, enhanced)
    if match:
        enhanced = enhanced[:match.end()] + "\n// Oregon Trail Game Structures\n" + game_structures + enhanced[match.end():]
    else:
        enhanced = "// Oregon Trail Game Structures\n" + game_structures + enhanced
    
    # Replace hex constants with named constants
    # Game states
    for state_val, state_name in GAME_STATES.items():
        enhanced = re.sub(
            r"\b" + str(state_val) + r"\b(?=[^;]*game_state)",
            state_name,
            enhanced
        )
    
    # Weather conditions
    for weather_val, weather_name in WEATHER_CONDITIONS.items():
        enhanced = re.sub(
            r"\b" + str(weather_val) + r"\b(?=[^;]*weather)",
            weather_name,
            enhanced
        )
    
    # Add code to initialize the game state at the top of main function
    if "void main() {" in enhanced:
        game_init = "\n    // Initialize game state\n"
        game_init += "    GameState gameState = {};\n"
        game_init += "    gameState.state = GAME_STATE_MENU;\n"
        game_init += "    gameState.month = MONTH_MARCH;\n"
        game_init += "    gameState.day = 1;\n"
        game_init += "    gameState.year = 1848;\n\n"
        
        enhanced = enhanced.replace("void main() {", "void main() {" + game_init)
    
    return enhanced
