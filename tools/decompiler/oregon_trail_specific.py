"""
Compatibility module for Oregon Trail specific code.
This redirects to the constants module.
"""

from .constants import (
    GAME_STATES, MEMORY_ADDRESSES, GRAPHICS_ADDRESSES,
    SOUND_ADDRESSES, INPUT_ADDRESSES, OREGON_TRAIL_PATTERNS
)
from .enhanced_output import enhance_code_with_game_knowledge as enhance_with_game_knowledge

def identify_game_function(function_name, instructions_text):
    """
    Identify game-specific function based on name and instructions.
    
    Args:
        function_name: Name of the function
        instructions_text: List of instruction text
        
    Returns:
        Function purpose if identified, None otherwise
    """
    # Look for specific function names
    if function_name.startswith("sub_"):
        return None
        
    if "main" in function_name.lower():
        return "Main game loop"
        
    if "init" in function_name.lower():
        return "Initialization routine"
        
    if "update" in function_name.lower():
        return "State update routine"
        
    if "draw" in function_name.lower() or "render" in function_name.lower():
        return "Graphics rendering routine"
        
    if "input" in function_name.lower() or "keyboard" in function_name.lower():
        return "Input handling routine"
        
    if "sound" in function_name.lower() or "audio" in function_name.lower():
        return "Sound/audio routine"
        
    # Check instruction patterns
    instructions_joined = " ".join(instructions_text)
    
    for pattern, desc in OREGON_TRAIL_PATTERNS.items():
        import re
        if re.search(pattern, instructions_joined, re.IGNORECASE):
            return desc
            
    return None
