"""
Enhanced output processing for the Oregon Trail decompiler.

This module provides functions to enhance decompiled output with
improved annotations, comments, and code formatting.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from .models import X86Instruction, DOSFunction

# Configure logger
logger = logging.getLogger(__name__)

# Mapping of interrupt values to their names
INTERRUPTS = {
    0x10: "BIOS Video Services",
    0x13: "BIOS Disk Services",
    0x14: "BIOS Serial Communications",
    0x15: "BIOS Miscellaneous System Services",
    0x16: "BIOS Keyboard Services",
    0x17: "BIOS Printer Services",
    0x1A: "BIOS Time Services",
    0x21: "DOS Function Calls",
    0x2F: "DOS Multiplex Interrupt",
    0x33: "Mouse Services"
}

# DOS Function calls (INT 21h) by AH value
DOS_FUNCTIONS = {
    0x00: "Program Terminate",
    0x01: "Character Input with Echo",
    0x02: "Character Output",
    0x03: "Auxiliary Input",
    0x04: "Auxiliary Output",
    0x05: "Printer Output",
    0x06: "Direct Console I/O",
    0x07: "Direct Character Input without Echo",
    0x08: "Character Input without Echo",
    0x09: "Display String",
    0x0A: "Buffered Keyboard Input",
    0x0B: "Check Standard Input Status",
    0x0C: "Clear Keyboard Buffer and Invoke Input",
    0x0D: "Disk Reset",
    0x0E: "Select Disk",
    0x0F: "Open File with FCB",
    0x10: "Close File with FCB",
    0x11: "Search for First Entry with FCB",
    0x12: "Search for Next Entry with FCB",
    0x13: "Delete File with FCB",
    0x14: "Sequential Read with FCB",
    0x15: "Sequential Write with FCB",
    0x16: "Create or Truncate File with FCB",
    0x17: "Rename File with FCB",
    0x19: "Get Current Drive",
    0x1A: "Set Disk Transfer Address",
    0x21: "Random Read with FCB",
    0x22: "Random Write with FCB",
    0x23: "Get File Size with FCB",
    0x24: "Set Relative Record with FCB",
    0x25: "Set Interrupt Vector",
    0x26: "Create New Program Segment Prefix",
    0x27: "Random Block Read with FCB",
    0x28: "Random Block Write with FCB",
    0x29: "Parse Filename",
    0x2A: "Get System Date",
    0x2B: "Set System Date",
    0x2C: "Get System Time",
    0x2D: "Set System Time",
    0x2E: "Set Verify Flag",
    0x2F: "Get Disk Transfer Address",
    0x30: "Get DOS Version",
    0x31: "Terminate and Stay Resident",
    0x33: "Get/Set Ctrl-Break Flag",
    0x35: "Get Interrupt Vector",
    0x36: "Get Disk Free Space",
    0x38: "Get/Set Country Information",
    0x39: "Create Directory",
    0x3A: "Remove Directory",
    0x3B: "Change Current Directory",
    0x3C: "Create or Truncate File",
    0x3D: "Open File",
    0x3E: "Close File Handle",
    0x3F: "Read from File or Device",
    0x40: "Write to File or Device",
    0x41: "Delete File",
    0x42: "Move File Pointer",
    0x43: "Get/Set File Attributes",
    0x44: "IOCTL",
    0x45: "Duplicate File Handle",
    0x46: "Force Duplicate File Handle",
    0x47: "Get Current Directory",
    0x48: "Allocate Memory",
    0x49: "Free Allocated Memory",
    0x4A: "Modify Allocated Memory",
    0x4B: "Execute Program (EXEC)",
    0x4C: "Terminate Process with Return Code",
    0x4D: "Get Return Code",
    0x4E: "Find First Matching File",
    0x4F: "Find Next Matching File",
    0x56: "Rename File",
    0x57: "Get/Set File Date and Time",
    0x58: "Get/Set Memory Allocation Strategy",
    0x59: "Get Extended Error Information",
    0x5A: "Create Temporary File",
    0x5B: "Create New File",
    0x62: "Get Program Segment Prefix",
    0x65: "Get Extended Country Information",
    0x66: "Get/Set Global Code Page",
    0x67: "Set Handle Count",
    0x68: "Commit File",
    0x6C: "Extended Open/Create",
}

# BIOS Video Services (INT 10h) by AH value
VIDEO_FUNCTIONS = {
    0x00: "Set Video Mode",
    0x01: "Set Cursor Size",
    0x02: "Set Cursor Position",
    0x03: "Get Cursor Position and Size",
    0x04: "Get Light Pen Position",
    0x05: "Select Active Display Page",
    0x06: "Scroll Window Up",
    0x07: "Scroll Window Down",
    0x08: "Read Character and Attribute at Cursor",
    0x09: "Write Character and Attribute at Cursor",
    0x0A: "Write Character at Cursor",
    0x0B: "Set Color Palette",
    0x0C: "Write Pixel Dot",
    0x0D: "Read Pixel Dot",
    0x0E: "Write Text in Teletype Mode",
    0x0F: "Get Current Video Mode",
    0x10: "Set Palette Registers / Set Color",
    0x11: "Character Generator",
    0x12: "Alternate Select",
    0x13: "Write String",
}

# Mouse Services (INT 33h) by AX value
MOUSE_FUNCTIONS = {
    0x00: "Reset Mouse and Get Status",
    0x01: "Show Mouse Cursor",
    0x02: "Hide Mouse Cursor",
    0x03: "Get Mouse Position and Button Status",
    0x04: "Set Mouse Cursor Position",
    0x05: "Get Button Press Information",
    0x06: "Get Button Release Information",
    0x07: "Set Horizontal Cursor Range",
    0x08: "Set Vertical Cursor Range",
    0x09: "Set Graphics Cursor Block",
    0x0A: "Set Text Cursor",
    0x0B: "Read Mouse Motion Counters",
    0x0C: "Set User-Defined Mouse Event Handler",
    0x0D: "Turn On Light Pen Emulation",
    0x0E: "Turn Off Light Pen Emulation",
    0x0F: "Set Mickey-to-Pixel Ratio",
    0x10: "Set Mouse Exclusion Area",
}

# Common DOS error codes
DOS_ERROR_CODES = {
    0x01: "Invalid function number",
    0x02: "File not found",
    0x03: "Path not found",
    0x04: "Too many open files",
    0x05: "Access denied",
    0x06: "Invalid handle",
    0x07: "Memory control blocks destroyed",
    0x08: "Insufficient memory",
    0x09: "Invalid memory block address",
    0x0A: "Invalid environment",
    0x0B: "Invalid format",
    0x0C: "Invalid access code",
    0x0D: "Invalid data",
    0x0F: "Invalid drive",
    0x10: "Attempt to remove current directory",
    0x11: "Not same device",
    0x12: "No more files",
}


def analyze_interrupt(instr: X86Instruction, next_instr: Optional[X86Instruction] = None) -> Optional[str]:
    """
    Analyze an interrupt instruction and return a descriptive comment.
    
    Args:
        instr: The interrupt instruction
        next_instr: The next instruction (optional, for context)
        
    Returns:
        A string describing the interrupt's purpose, or None if not recognized
    """
    if instr.mnemonic.lower() != "int":
        return None
        
    # Extract the interrupt number
    match = re.search(r'0x([0-9A-F]+)', instr.operands, re.IGNORECASE)
    if not match:
        match = re.search(r'([0-9A-F]+)h', instr.operands, re.IGNORECASE)
        
    if not match:
        return None
        
    int_num = int(match.group(1), 16)
    
    # Look up the interrupt name
    int_name = INTERRUPTS.get(int_num, f"Unknown Interrupt {int_num:02X}h")
    
    # For DOS function calls (INT 21h), check the function number in AH
    if int_num == 0x21:
        # Try to find AH value in previous instructions
        ah_value = _find_register_value("ah", instr)
        if ah_value is not None and ah_value in DOS_FUNCTIONS:
            func_desc = DOS_FUNCTIONS[ah_value]
            return f"{int_name}: {func_desc} (AH={ah_value:02X}h)"
            
    # For video services (INT 10h)
    elif int_num == 0x10:
        ah_value = _find_register_value("ah", instr)
        if ah_value is not None and ah_value in VIDEO_FUNCTIONS:
            func_desc = VIDEO_FUNCTIONS[ah_value]
            return f"{int_name}: {func_desc} (AH={ah_value:02X}h)"
            
    # For mouse services (INT 33h)
    elif int_num == 0x33:
        ax_value = _find_register_value("ax", instr)
        if ax_value is not None and ax_value in MOUSE_FUNCTIONS:
            func_desc = MOUSE_FUNCTIONS[ax_value]
            return f"{int_name}: {func_desc} (AX={ax_value:04X}h)"
            
    # If we couldn't identify the specific function
    return int_name
    

def _find_register_value(reg: str, instr: X86Instruction) -> Optional[int]:
    """
    Look in the instruction stream to find the most recent value assigned to a register.
    
    Args:
        reg: The register name (e.g., "ah", "al", "ax")
        instr: The current instruction
        
    Returns:
        The register value if found, None otherwise
    """
    # This is a simplistic approach based on the operands of the current instruction
    # In a real implementation, we would need to track register values through the control flow
    
    # For AH register
    if reg.lower() == "ah":
        # Check if there's a MOV AH instruction in the operands
        match = re.search(r'mov\s+ah,\s*(?:0x)?([0-9A-F]+)', instr.operands, re.IGNORECASE)
        if match:
            return int(match.group(1), 16)
    
    # For AL register
    elif reg.lower() == "al":
        # Check if there's a MOV AL instruction in the operands
        match = re.search(r'mov\s+al,\s*(?:0x)?([0-9A-F]+)', instr.operands, re.IGNORECASE)
        if match:
            return int(match.group(1), 16)
    
    # For AX register (16-bit)
    elif reg.lower() == "ax":
        # Check if there's a MOV AX instruction in the operands
        match = re.search(r'mov\s+ax,\s*(?:0x)?([0-9A-F]+)', instr.operands, re.IGNORECASE)
        if match:
            return int(match.group(1), 16)
    
    return None


def analyze_dos_api_sequence(instructions: List[X86Instruction]) -> Dict[int, str]:
    """
    Analyze a sequence of instructions to identify DOS API calls and add comments.
    
    Args:
        instructions: List of instructions to analyze
        
    Returns:
        Dictionary mapping instruction addresses to comments
    """
    comments = {}
    
    for i, instr in enumerate(instructions):
        # Handle interrupts
        if instr.mnemonic.lower() == "int":
            next_instr = instructions[i+1] if i+1 < len(instructions) else None
            comment = analyze_interrupt(instr, next_instr)
            if comment:
                comments[instr.address] = comment
                
                # Also check for error code checking after DOS calls
                if i+1 < len(instructions) and "INT 21h" in comment:
                    next_instr = instructions[i+1]
                    if next_instr.mnemonic.lower() in ["jc", "jb"]:
                        comments[next_instr.address] = "Jump if DOS error occurred"
                    elif next_instr.mnemonic.lower() == "mov" and "ax" in next_instr.operands.lower():
                        comments[next_instr.address] = "Save DOS return value"
        
        # Handle specific DOS API patterns
        elif instr.mnemonic.lower() == "mov":
            # File open operations
            if "ah" in instr.operands.lower() and "3d" in instr.operands.lower():
                comments[instr.address] = "Prepare to open file (AH=3Dh)"
            
            # File read operations
            elif "ah" in instr.operands.lower() and "3f" in instr.operands.lower():
                comments[instr.address] = "Prepare to read from file (AH=3Fh)"
            
            # File write operations
            elif "ah" in instr.operands.lower() and "40" in instr.operands.lower():
                comments[instr.address] = "Prepare to write to file (AH=40h)"
                
            # Memory allocation
            elif "ah" in instr.operands.lower() and "48" in instr.operands.lower():
                comments[instr.address] = "Prepare to allocate memory (AH=48h)"
                
            # Load program
            elif "ah" in instr.operands.lower() and "4b" in instr.operands.lower():
                comments[instr.address] = "Prepare to execute program (AH=4Bh)"
                
        # Check for common error handling patterns
        elif instr.mnemonic.lower() == "cmp" and "ax" in instr.operands.lower():
            for code, desc in DOS_ERROR_CODES.items():
                if f"0x{code:02x}" in instr.operands.lower() or f"{code}" in instr.operands:
                    comments[instr.address] = f"Check for DOS error: {desc}"
                    break
    
    return comments


def enhance_dos_api_comments(functions: List[DOSFunction]) -> int:
    """
    Enhance all functions with DOS API-related comments.
    
    Args:
        functions: List of DOSFunction objects to enhance
        
    Returns:
        The number of comments added
    """
    logger.info("Enhancing DOS API comments in decompiled functions")
    total_comments = 0
    
    for func in functions:
        if not hasattr(func, "instructions") or not func.instructions:
            continue
            
        # Analyze the function's instructions
        api_comments = analyze_dos_api_sequence(func.instructions)
        
        # Add the comments to the instructions
        for addr, comment in api_comments.items():
            for instr in func.instructions:
                if instr.address == addr:
                    if hasattr(instr, "comment") and instr.comment:
                        # Only add if it doesn't already contain this information
                        if comment not in instr.comment:
                            instr.comment = f"{instr.comment}; {comment}"
                    else:
                        instr.comment = comment
                    total_comments += 1
    
    logger.info(f"Added {total_comments} DOS API comments")
    return total_comments


def enhance_output_formatting(pseudocode: str) -> str:
    """
    Enhance the formatting of pseudocode output.
    
    Args:
        pseudocode: The pseudocode to format
        
    Returns:
        Formatted pseudocode with improved spacing, indentation, etc.
    """
    # Replace tabs with spaces
    formatted = pseudocode.replace('\t', '    ')
    
    # Ensure consistent spacing around operators
    operators = ['+', '-', '*', '/', '=', '==', '!=', '<', '>', '<=', '>=', '&&', '||']
    for op in operators:
        formatted = re.sub(r'\s*' + re.escape(op) + r'\s*', f' {op} ', formatted)
    
    # Ensure consistent spacing after commas
    formatted = re.sub(r',\s*', ', ', formatted)
    
    # Ensure consistent spacing after semicolons
    formatted = re.sub(r';\s*', '; ', formatted)
    
    # Ensure consistent spacing around parentheses
    formatted = re.sub(r'\(\s+', '(', formatted)
    formatted = re.sub(r'\s+\)', ')', formatted)
    
    # Ensure consistent spacing around braces
    formatted = re.sub(r'{\s*', ' {\n', formatted)
    formatted = re.sub(r'\s*}', '\n}', formatted)
    
    # Fix up spacing in if statements
    formatted = re.sub(r'if\s*\(', 'if (', formatted)
    
    # Fix up spacing in for loops
    formatted = re.sub(r'for\s*\(', 'for (', formatted)
    
    # Fix up spacing in while loops
    formatted = re.sub(r'while\s*\(', 'while (', formatted)
    
    # Replace multiple blank lines with a single blank line
    formatted = re.sub(r'\n\s*\n\s*\n+', '\n\n', formatted)
    
    return formatted


def enhance_code_with_game_knowledge(code: str) -> str:
    """
    Enhance code with game-specific knowledge from Oregon Trail.
    
    This function replaces memory addresses with meaningful names,
    enhances comments, and generally makes the code more readable
    by incorporating knowledge about Oregon Trail's internals.
    
    Args:
        code: The code to enhance
        
    Returns:
        Enhanced code with game-specific knowledge
    """
    from .constants import (
        GAME_STATES, MEMORY_ADDRESSES, GRAPHICS_ADDRESSES,
        SOUND_ADDRESSES, INPUT_ADDRESSES, OREGON_TRAIL_PATTERNS
    )
    
    enhanced = code
    
    # Add a header with more specific information
    header = "// Enhanced Code for Oregon Trail with Game-Specific Knowledge\n"
    header += "// Generated with Oregon Trail Decompiler\n\n"
    
    if enhanced.startswith("//"):
        # Replace the existing header
        enhanced = re.sub(r"//.*?\n\n", header, enhanced, count=1, flags=re.DOTALL)
    else:
        # Add the header at the beginning
        enhanced = header + enhanced
    
    # Replace memory addresses with meaningful names
    for addr, name in MEMORY_ADDRESSES.items():
        addr_str = f"0x{addr:X}"
        # Match both uppercase and lowercase hex, with and without brackets
        enhanced = re.sub(r"\[\s*" + addr_str + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"\[\s*" + addr_str.lower() + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str + r"\b(?!\])", name, enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str.lower() + r"\b(?!\])", name, enhanced, flags=re.IGNORECASE)

    # Replace graphics addresses
    for addr, name in GRAPHICS_ADDRESSES.items():
        addr_str = f"0x{addr:X}"
        enhanced = re.sub(r"\[\s*" + addr_str + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"\[\s*" + addr_str.lower() + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str + r"\b(?!\])", name, enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str.lower() + r"\b(?!\])", name, enhanced, flags=re.IGNORECASE)

    # Replace sound addresses
    for addr, name in SOUND_ADDRESSES.items():
        addr_str = f"0x{addr:X}"
        enhanced = re.sub(r"\[\s*" + addr_str + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"\[\s*" + addr_str.lower() + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str + r"\b(?!\])", name, enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str.lower() + r"\b(?!\])", name, enhanced, flags=re.IGNORECASE)

    # Replace input addresses
    for addr, name in INPUT_ADDRESSES.items():
        addr_str = f"0x{addr:X}"
        enhanced = re.sub(r"\[\s*" + addr_str + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"\[\s*" + addr_str.lower() + r"\s*\]", f"[{name}]", enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str + r"\b(?!\])", name, enhanced, flags=re.IGNORECASE)
        enhanced = re.sub(r"(?<!\[)\b" + addr_str.lower() + r"\b(?!\])", name, enhanced, flags=re.IGNORECASE)

    # Replace game state constants
    for value, name in GAME_STATES.items():
        enhanced = re.sub(
            r"cmp\s+word\s+ptr\s+\[game_state\],\s*" + str(value) + r"\b",
            f"cmp word ptr [game_state], {name} // {value}",
            enhanced,
        )
        enhanced = re.sub(
            r"mov\s+word\s+ptr\s+\[game_state\],\s*" + str(value) + r"\b",
            f"mov word ptr [game_state], {name} // {value}",
            enhanced,
        )

    # Add common code pattern comments
    for pattern, description in OREGON_TRAIL_PATTERNS.items():
        enhanced = re.sub(
            pattern + r"(?![^{/]*//)",  # Don't add comments to lines that already have them
            f"\\g<0> // {description}",
            enhanced,
            flags=re.IGNORECASE
        )

    # Fix formatting
    enhanced = enhance_output_formatting(enhanced)
    
    return enhanced