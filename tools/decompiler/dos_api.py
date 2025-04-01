"""
DOS API call recognition for the decompiler.
"""

from typing import Dict, Optional


class DOSInterrupt:
    """Represents a DOS interrupt call"""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, str] = None,
        returns: str = None,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters or {}
        self.returns = returns


# Common DOS interrupts
DOS_INT21 = {
    # File operations
    0x3D: DOSInterrupt(
        "DOS_OpenFile",
        "Open file",
        parameters={"DS:DX": "pointer to ASCIIZ filename", "AL": "access mode"},
        returns="AX = file handle or error code if CF set",
    ),
    0x3E: DOSInterrupt(
        "DOS_CloseFile",
        "Close file",
        parameters={"BX": "file handle"},
        returns="AX = error code if CF set",
    ),
    0x3F: DOSInterrupt(
        "DOS_ReadFile",
        "Read from file or device",
        parameters={
            "BX": "file handle",
            "CX": "number of bytes to read",
            "DS:DX": "pointer to buffer",
        },
        returns="AX = bytes read or error code if CF set",
    ),
    0x40: DOSInterrupt(
        "DOS_WriteFile",
        "Write to file or device",
        parameters={
            "BX": "file handle",
            "CX": "number of bytes to write",
            "DS:DX": "pointer to buffer",
        },
        returns="AX = bytes written or error code if CF set",
    ),
    0x41: DOSInterrupt(
        "DOS_DeleteFile",
        "Delete file",
        parameters={"DS:DX": "pointer to ASCIIZ filename"},
        returns="AX = error code if CF set",
    ),
    0x42: DOSInterrupt(
        "DOS_MoveFilePointer",
        "Move file pointer",
        parameters={
            "BX": "file handle",
            "CX:DX": "offset",
            "AL": "method (0=start, 1=current, 2=end)",
        },
        returns="DX:AX = new file position or error code if CF set",
    ),
    # Directory operations
    0x39: DOSInterrupt(
        "DOS_CreateDirectory",
        "Create directory",
        parameters={"DS:DX": "pointer to ASCIIZ directory name"},
        returns="AX = error code if CF set",
    ),
    0x3A: DOSInterrupt(
        "DOS_RemoveDirectory",
        "Remove directory",
        parameters={"DS:DX": "pointer to ASCIIZ directory name"},
        returns="AX = error code if CF set",
    ),
    0x3B: DOSInterrupt(
        "DOS_ChangeDirectory",
        "Change current directory",
        parameters={"DS:DX": "pointer to ASCIIZ directory name"},
        returns="AX = error code if CF set",
    ),
    0x47: DOSInterrupt(
        "DOS_GetCurrentDirectory",
        "Get current directory",
        parameters={
            "DL": "drive number (0=default, 1=A:, etc.)",
            "DS:SI": "pointer to buffer",
        },
        returns="AX = error code if CF set",
    ),
    # Memory management
    0x48: DOSInterrupt(
        "DOS_AllocateMemory",
        "Allocate memory",
        parameters={"BX": "number of paragraphs"},
        returns="AX = segment address or error code if CF set, BX = maximum paragraphs available if CF set",
    ),
    0x49: DOSInterrupt(
        "DOS_FreeMemory",
        "Free allocated memory",
        parameters={"ES": "segment address"},
        returns="AX = error code if CF set",
    ),
    0x4A: DOSInterrupt(
        "DOS_ModifyMemoryAllocation",
        "Modify memory allocation",
        parameters={"BX": "new size in paragraphs", "ES": "segment address"},
        returns="AX = error code if CF set, BX = maximum paragraphs available if CF set",
    ),
    # Process management
    0x4B: DOSInterrupt(
        "DOS_LoadOrExecuteProgram",
        "Load or execute program",
        parameters={
            "AL": "function (0=load and execute, 3=load only)",
            "DS:DX": "pointer to ASCIIZ filename",
            "ES:BX": "pointer to parameter block",
        },
        returns="AX = error code if CF set",
    ),
    0x4C: DOSInterrupt(
        "DOS_TerminateWithReturnCode",
        "Terminate process with return code",
        parameters={"AL": "return code"},
    ),
    0x4D: DOSInterrupt(
        "DOS_GetReturnCode",
        "Get return code of subprocess",
        returns="AX = return code, AH = exit type (0=normal, 1=Ctrl-C, 2=critical error, 3=TSR)",
    ),
    # Console I/O
    0x01: DOSInterrupt(
        "DOS_ReadCharacter",
        "Read character from standard input with echo",
        returns="AL = character read",
    ),
    0x02: DOSInterrupt(
        "DOS_WriteCharacter",
        "Write character to standard output",
        parameters={"DL": "character to write"},
    ),
    0x09: DOSInterrupt(
        "DOS_WriteString",
        "Write string to standard output",
        parameters={"DS:DX": "pointer to string ending with '$'"},
    ),
    0x0A: DOSInterrupt(
        "DOS_BufferedInput",
        "Buffered input",
        parameters={"DS:DX": "pointer to input buffer"},
    ),
}

# Video services (INT 10h)
VIDEO_INT10 = {
    0x00: DOSInterrupt(
        "VIDEO_SetVideoMode", "Set video mode", parameters={"AL": "video mode"}
    ),
    0x02: DOSInterrupt(
        "VIDEO_SetCursorPosition",
        "Set cursor position",
        parameters={"DH": "row", "DL": "column", "BH": "page number"},
    ),
    0x09: DOSInterrupt(
        "VIDEO_WriteCharacterAttribute",
        "Write character and attribute at cursor",
        parameters={
            "AL": "character",
            "BH": "page number",
            "BL": "attribute",
            "CX": "count",
        },
    ),
    0x0E: DOSInterrupt(
        "VIDEO_WriteTeletype",
        "Write text in teletype mode",
        parameters={
            "AL": "character",
            "BH": "page number",
            "BL": "foreground color (graphics modes only)",
        },
    ),
    0x13: DOSInterrupt(
        "VIDEO_WriteString",
        "Write string",
        parameters={
            "AL": "write mode",
            "BH": "page number",
            "BL": "attribute",
            "CX": "string length",
            "DH": "row",
            "DL": "column",
            "ES:BP": "pointer to string",
        },
    ),
}

# Keyboard services (INT 16h)
KEYBOARD_INT16 = {
    0x00: DOSInterrupt(
        "KEYBOARD_ReadCharacter",
        "Read character from keyboard",
        returns="AH = scan code, AL = ASCII character",
    ),
    0x01: DOSInterrupt(
        "KEYBOARD_CheckForKeypress",
        "Check for keypress",
        returns="ZF = status (0=key available), AH = scan code, AL = ASCII character if ZF=0",
    ),
}

# All interrupts combined
DOS_INTERRUPTS = {
    0x21: DOS_INT21,
    0x10: VIDEO_INT10,
    0x16: KEYBOARD_INT16,
}


def recognize_interrupt(interrupt: int, function: int = None) -> Optional[DOSInterrupt]:
    """
    Recognize a DOS interrupt call.

    Args:
        interrupt: The interrupt number
        function: The function number (in AH or AL)

    Returns:
        A DOSInterrupt object if recognized, None otherwise
    """
    if interrupt not in DOS_INTERRUPTS:
        return None

    if function is None:
        # Return a generic interrupt name if function is not specified
        return DOSInterrupt(f"INT_{interrupt:02X}", f"Interrupt {interrupt:02X}h")

    if function in DOS_INTERRUPTS[interrupt]:
        return DOS_INTERRUPTS[interrupt][function]

    return DOSInterrupt(
        f"INT_{interrupt:02X}_AH{function:02X}",
        f"Interrupt {interrupt:02X}h Function {function:02X}h",
    )


def format_interrupt_call(
    interrupt: DOSInterrupt, parameters: Dict[str, str] = None
) -> str:
    """
    Format an interrupt call as a C-like function call.

    Args:
        interrupt: The interrupt to format
        parameters: Optional parameter values to include

    Returns:
        A formatted function call string
    """
    if parameters is None:
        parameters = {}

    param_str = ", ".join([f"{k}={v}" for k, v in parameters.items()])
    return f"{interrupt.name}({param_str})"
