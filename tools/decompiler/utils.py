"""
Utility functions for the Oregon Trail decompiler.
"""

import logging
import os
import re


def setup_logging(level=logging.INFO):
    """
    Set up logging with appropriate formatting.
    
    Args:
        level: Logging level to use
    """
    logging.basicConfig(
        level=level,
        format="%(levelname).1s %(module)s: %(message)s",
        force=True
    )
    return logging.getLogger(__name__)


def ensure_directory(directory):
    """
    Make sure a directory exists, creating it if necessary.
    
    Args:
        directory: The directory path to ensure exists
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def hex_string_to_int(hex_string):
    """
    Convert a hex string to an integer, handling various formats.
    
    Args:
        hex_string: Hex string (e.g., "0x1234", "1234h", "1234")
        
    Returns:
        Integer value
    """
    hex_string = hex_string.strip()
    
    if hex_string.startswith("0x"):
        return int(hex_string[2:], 16)
    elif hex_string.endswith("h"):
        return int(hex_string[:-1], 16)
    else:
        try:
            return int(hex_string, 16)
        except ValueError:
            try:
                return int(hex_string)
            except ValueError:
                return None


def replace_memory_references(code, address_map):
    """
    Replace memory addresses with symbolic names.
    
    Args:
        code: The code to process
        address_map: Dictionary mapping addresses to symbolic names
        
    Returns:
        Code with memory references replaced
    """
    result = code
    for addr, name in address_map.items():
        addr_str = f"0x{addr:X}"
        result = re.sub(r'\[' + addr_str + r'\]', f'[{name}]', result)
        result = re.sub(r'\b' + addr_str + r'\b', name, result)
    
    return result


def translate_condition(condition, operands=None):
    """
    Translate a condition mnemonic to a more readable form or C-like condition.
    
    Args:
        condition: The condition mnemonic (e.g., "jz", "jne")
        operands: Optional operands for the condition
        
    Returns:
        Human-readable condition or C-like condition depending on context
    """
    # Human readable descriptions
    condition_descriptions = {
        "jz": "if zero",
        "je": "if equal",
        "jnz": "if not zero",
        "jne": "if not equal",
        "jg": "if greater",
        "jge": "if greater or equal",
        "jl": "if less",
        "jle": "if less or equal",
        "ja": "if above",
        "jae": "if above or equal",
        "jb": "if below",
        "jbe": "if below or equal",
        "jc": "if carry",
        "jnc": "if not carry",
        "jo": "if overflow",
        "jno": "if not overflow",
        "js": "if sign",
        "jns": "if not sign",
        "jcxz": "if CX is zero",
        "loop": "loop",
        "loope": "loop if equal",
        "loopz": "loop if zero",
        "loopne": "loop if not equal",
        "loopnz": "loop if not zero"
    }
    
    # C-like condition expressions
    c_conditions = {
        "jz": "== 0",
        "je": "== 0",
        "jnz": "!= 0",
        "jne": "!= 0",
        "jg": "> 0",
        "jge": ">= 0",
        "jl": "< 0",
        "jle": "<= 0",
        "ja": "> 0",
        "jae": ">= 0",
        "jb": "< 0",
        "jbe": "<= 0",
        "jc": "& 1",  # Carry flag check
        "jnc": "& 1 == 0",
        "jo": "overflow",
        "jno": "!overflow",
        "js": "< 0",  # Sign flag (negative)
        "jns": ">= 0"
    }
    
    # If operands are provided, try to generate a C-like condition
    if operands is not None:
        # Get the base condition
        cond = c_conditions.get(condition.lower(), condition)
        
        # Try to extract the comparison operands
        if operands and ',' not in operands:
            # This is likely a target address without comparison operands
            # Default to using the condition with a presumed comparison against zero
            return cond
        
        # Return the C-like condition
        return cond
    
    # Otherwise, return the human-readable description
    return condition_descriptions.get(condition.lower(), condition)
