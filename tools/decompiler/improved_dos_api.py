"""
Enhanced DOS API functions and interrupts analysis for the decompiler.
"""

from typing import Dict, Optional, Tuple, List
import re
from .models import X86Instruction

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
    0x1B: "Get Default Drive Data",
    0x1C: "Get Drive Data",
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
    0x71: "LFN: Find First File",
    0x72: "LFN: Find Next File",
    0x73: "LFN: Get File Name",
    0x74: "LFN: Get Volume Information",
    0x76: "LFN: Get File Information",
    0x7A: "LFN: Get Current Directory"
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
    0x1A: "Get/Set Display Combination",
    0x1B: "Get Functionality/State Information",
    0x1C: "Save/Restore Video State"
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
    0x13: "Set Double-Speed Threshold",
    0x14: "Swap User-Defined Mouse Event Handlers",
    0x15: "Get Mouse Save State Size",
    0x16: "Save Mouse State",
    0x17: "Restore Mouse State",
    0x18: "Set Alternate Mouse Event Handler",
    0x19: "Get Alternate Mouse Event Handler",
    0x1A: "Set Mouse Sensitivity",
    0x1B: "Get Mouse Sensitivity",
    0x1C: "Set Mouse Interrupt Rate",
    0x1D: "Set Display Page for Mouse",
    0x1E: "Get Display Page for Mouse",
    0x1F: "Disable Mouse Driver",
    0x20: "Enable Mouse Driver",
    0x21: "Reset Mouse Driver",
    0x22: "Set Language for Mouse Driver",
    0x23: "Get Language Number for Mouse Driver",
    0x24: "Get Mouse Information"
}

# BIOS Disk Services (INT 13h) by AH value
DISK_FUNCTIONS = {
    0x00: "Reset Disk Drive",
    0x01: "Get Disk Drive Status",
    0x02: "Read Disk Sectors",
    0x03: "Write Disk Sectors",
    0x04: "Verify Disk Sectors",
    0x05: "Format Disk Track",
    0x08: "Get Drive Parameters",
    0x09: "Initialize Fixed Disk Parameter Tables",
    0x0A: "Read Long Sectors",
    0x0B: "Write Long Sectors",
    0x0C: "Seek to Cylinder",
    0x0D: "Alternate Disk Reset",
    0x10: "Test Drive Ready",
    0x11: "Recalibrate Drive",
    0x14: "Controller Internal Diagnostic",
    0x15: "Get Disk Type",
    0x16: "Get Disk Change Status",
    0x17: "Set Disk Type",
    0x18: "Set Media Type for Format",
    0x41: "Extended Disk Drive (EDD) Check Extensions Present",
    0x42: "Extended Disk Drive (EDD) Read Sectors",
    0x43: "Extended Disk Drive (EDD) Write Sectors",
    0x44: "Extended Disk Drive (EDD) Verify Sectors",
    0x45: "Extended Disk Drive (EDD) Lock/Unlock Drive",
    0x46: "Extended Disk Drive (EDD) Eject Media",
    0x47: "Extended Disk Drive (EDD) Move to Specified Cylinder",
    0x48: "Extended Disk Drive (EDD) Get Drive Parameters",
    0x49: "Extended Disk Drive (EDD) Get Extended Drive Parameters"
}

# Common DOS file access modes
FILE_ACCESS_MODES = {
    0x00: "Read Only",
    0x01: "Write Only",
    0x02: "Read/Write"
}

# Sound card functions
SOUND_FUNCTIONS = {
    # Sound Blaster
    0x20: "DSP Reset",
    0x40: "Set Time Constant",
    0x41: "Set Output Sample Rate",
    0x42: "Set Input Sample Rate",
    0x45: "Continue DMA Operation",
    0x48: "Set DSP Block Transfer Size",
    0x74: "DMA 8-bit Sound Output",
    0x75: "DMA 8-bit Sound Output (Reference)",
    0x76: "DMA 2-bit Sound Output",
    0x80: "Stop Sound Output",
    0xD0: "Pause 8-bit DMA Mode",
    0xD1: "Speaker On",
    0xD3: "Speaker Off",
    0xDA: "Exit 8-bit DMA Mode",
    0xE0: "DSP Identification",
    0xE1: "DSP Version",
    0xE2: "DSP Copyright",
    0xE3: "DSP Write Test",
    0xE8: "Read DSP Version",
    0xF0: "Generate IRQ",
    0xF2: "Force 8-bit IRQ",
    0xF8: "Sine Generator"
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
    0x0E: "Reserved",
    0x0F: "Invalid drive",
    0x10: "Attempt to remove current directory",
    0x11: "Not same device",
    0x12: "No more files",
    0x13: "Disk write-protected",
    0x14: "Unknown unit",
    0x15: "Drive not ready",
    0x16: "Unknown command",
    0x17: "Data error (CRC)",
    0x18: "Bad request structure length",
    0x19: "Seek error",
    0x1A: "Unknown media type",
    0x1B: "Sector not found",
    0x1C: "Printer out of paper",
    0x1D: "Write fault",
    0x1E: "Read fault",
    0x1F: "General failure",
    0x20: "Sharing violation",
    0x21: "Lock violation",
    0x22: "Invalid disk change",
    0x23: "FCB unavailable",
    0x24: "Sharing buffer overflow",
    0x25: "Code page mismatch",
    0x26: "Cannot complete file operation",
    0x27: "Insufficient disk space"
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
            
    # For disk services (INT 13h)
    elif int_num == 0x13:
        ah_value = _find_register_value("ah", instr)
        if ah_value is not None and ah_value in DISK_FUNCTIONS:
            func_desc = DISK_FUNCTIONS[ah_value]
            return f"{int_name}: {func_desc} (AH={ah_value:02X}h)"
            
    # If we couldn't identify the specific function
    return int_name
    

def _find_register_value(reg: str, instr: X86Instruction, max_lookback: int = 5) -> Optional[int]:
    """
    Look backwards in the instruction stream to find the most recent value assigned to a register.
    
    Args:
        reg: The register name (e.g., "ah", "al", "ax")
        instr: The current instruction
        max_lookback: Maximum number of instructions to look back
        
    Returns:
        The register value if found, None otherwise
    """
    # This function would need to be implemented with access to the previous instructions
    # For now, we'll use a simplistic approach based on the operands of the current instruction
    
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


def enhance_dos_api_comments(functions: List):
    """
    Enhance all functions with DOS API-related comments.
    
    Args:
        functions: List of DOSFunction objects to enhance
        
    Returns:
        The number of comments added
    """
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
    
    return total_comments