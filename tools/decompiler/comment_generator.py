"""
Comment generator for the decompiler.
"""

import re
from typing import List, Optional

from .models import DOSFunction, X86Instruction


# Common instruction patterns and their explanations
INSTRUCTION_PATTERNS = {
    # Memory operations
    r"mov\s+\[.+\],\s*.+": "Store value to memory",
    r"mov\s+.+,\s*\[.+\]": "Load value from memory",
    # String operations
    r"rep\s+movs": "Copy string/memory block",
    r"rep\s+stos": "Fill memory block",
    r"rep\s+cmps": "Compare strings",
    r"rep\s+scas": "Scan string",
    r"lods": "Load string byte/word",
    r"stos": "Store string byte/word",
    r"movs": "Move string byte/word",
    # Arithmetic operations
    r"add\s+.+,\s*.+": "Add values",
    r"sub\s+.+,\s*.+": "Subtract values",
    r"mul\s+.+": "Multiply (unsigned)",
    r"imul\s+.+": "Multiply (signed)",
    r"div\s+.+": "Divide (unsigned)",
    r"idiv\s+.+": "Divide (signed)",
    r"inc\s+.+": "Increment value",
    r"dec\s+.+": "Decrement value",
    r"neg\s+.+": "Negate value",
    # Logical operations
    r"and\s+.+,\s*.+": "Bitwise AND",
    r"or\s+.+,\s*.+": "Bitwise OR",
    r"xor\s+.+,\s*.+": "Bitwise XOR",
    r"not\s+.+": "Bitwise NOT",
    r"shl\s+.+,\s*.+": "Shift left",
    r"shr\s+.+,\s*.+": "Shift right (unsigned)",
    r"sar\s+.+,\s*.+": "Shift right (signed)",
    r"rol\s+.+,\s*.+": "Rotate left",
    r"ror\s+.+,\s*.+": "Rotate right",
    # Comparison operations
    r"cmp\s+.+,\s*.+": "Compare values",
    r"test\s+.+,\s*.+": "Test bits (AND without storing)",
    # Control flow
    r"jmp\s+.+": "Jump to address",
    r"je\s+.+": "Jump if equal (ZF=1)",
    r"jne\s+.+": "Jump if not equal (ZF=0)",
    r"jz\s+.+": "Jump if zero (ZF=1)",
    r"jnz\s+.+": "Jump if not zero (ZF=0)",
    r"jg\s+.+": "Jump if greater (signed)",
    r"jge\s+.+": "Jump if greater or equal (signed)",
    r"jl\s+.+": "Jump if less (signed)",
    r"jle\s+.+": "Jump if less or equal (signed)",
    r"ja\s+.+": "Jump if above (unsigned)",
    r"jae\s+.+": "Jump if above or equal (unsigned)",
    r"jb\s+.+": "Jump if below (unsigned)",
    r"jbe\s+.+": "Jump if below or equal (unsigned)",
    r"call\s+.+": "Call function",
    r"ret": "Return from function",
    r"loop\s+.+": "Loop (decrement CX and jump if CX!=0)",
    # Stack operations
    r"push\s+.+": "Push value onto stack",
    r"pop\s+.+": "Pop value from stack",
    r"pushf": "Push flags onto stack",
    r"popf": "Pop flags from stack",
    # Flag operations
    r"stc": "Set carry flag",
    r"clc": "Clear carry flag",
    r"std": "Set direction flag",
    r"cld": "Clear direction flag",
    r"sti": "Set interrupt flag",
    r"cli": "Clear interrupt flag",
    # Miscellaneous
    r"nop": "No operation",
    r"int\s+.+": "Call interrupt",
    r"in\s+.+": "Input from port",
    r"out\s+.+": "Output to port",
    r"lea\s+.+,\s*.+": "Load effective address",
    r"xchg\s+.+,\s*.+": "Exchange values",
}

# Common code patterns and their explanations
CODE_PATTERNS = {
    # Loop patterns
    r"mov\s+cx,\s*.+\s*\n\s*loop": "Initialize loop counter and loop",
    r"mov\s+cx,\s*.+\s*\n\s*rep": "Initialize counter for string operation",
    r"inc\s+.+\s*\n\s*cmp\s+.+\s*\n\s*j[bl]": "Increment counter and check loop condition",
    r"dec\s+.+\s*\n\s*cmp\s+.+\s*\n\s*j[ag]": "Decrement counter and check loop condition",
    # Conditional patterns
    r"cmp\s+.+\s*\n\s*je": "Check if values are equal",
    r"cmp\s+.+\s*\n\s*jne": "Check if values are not equal",
    r"test\s+.+\s*\n\s*jz": "Check if bits are all zero",
    r"test\s+.+\s*\n\s*jnz": "Check if any bits are set",
    # Function call patterns
    r"push\s+.+\s*\n\s*push\s+.+\s*\n\s*call": "Prepare arguments and call function",
    r"call\s+.+\s*\n\s*add\s+sp,": "Call function and clean up stack",
    # Memory allocation patterns
    r"mov\s+ah,\s*0x48\s*\n\s*int\s+0x21": "Allocate memory (DOS)",
    r"mov\s+ah,\s*0x49\s*\n\s*int\s+0x21": "Free memory (DOS)",
    # File operation patterns
    r"mov\s+ah,\s*0x3[cd]\s*\n\s*int\s+0x21": "Open file (DOS)",
    r"mov\s+ah,\s*0x3e\s*\n\s*int\s+0x21": "Close file (DOS)",
    r"mov\s+ah,\s*0x3f\s*\n\s*int\s+0x21": "Read from file (DOS)",
    r"mov\s+ah,\s*0x40\s*\n\s*int\s+0x21": "Write to file (DOS)",
    # String operation patterns
    r"cld\s*\n\s*mov\s+si,\s*.+\s*\n\s*mov\s+di,\s*.+\s*\n\s*rep\s+movs": "Copy string from source to destination",
    r"cld\s*\n\s*mov\s+di,\s*.+\s*\n\s*mov\s+al,\s*.+\s*\n\s*rep\s+stos": "Fill memory with a value",
    # Array access patterns
    r"mov\s+bx,\s*.+\s*\n\s*shl\s+bx,\s*1\s*\n\s*add\s+bx,": "Access element in an array of words",
    r"mov\s+si,\s*.+\s*\n\s*add\s+si,\s*.+\s*\n\s*mov\s+al,\s*\[si\]": "Access element in an array of bytes",
}

# Oregon Trail specific patterns
OREGON_TRAIL_PATTERNS = {
    # Game state patterns
    r"mov\s+word\s+ptr\s+\[0x5c\d{2}\],": "Update game state variable",
    r"cmp\s+word\s+ptr\s+\[0x5c\d{2}\],": "Check game state variable",
    # Player data patterns
    r"mov\s+word\s+ptr\s+\[0x5d\d{2}\],": "Update player data",
    r"cmp\s+word\s+ptr\s+\[0x5d\d{2}\],": "Check player data",
    # Inventory patterns
    r"mov\s+word\s+ptr\s+\[0x5e\d{2}\],": "Update inventory item",
    r"cmp\s+word\s+ptr\s+\[0x5e\d{2}\],": "Check inventory item",
    # Event patterns
    r"mov\s+word\s+ptr\s+\[0x5f\d{2}\],": "Update event data",
    r"cmp\s+word\s+ptr\s+\[0x5f\d{2}\],": "Check event data",
    # Menu patterns
    r"mov\s+word\s+ptr\s+\[0x60\d{2}\],": "Update menu data",
    r"cmp\s+word\s+ptr\s+\[0x60\d{2}\],": "Check menu data",
    # Screen patterns
    r"mov\s+word\s+ptr\s+\[0x61\d{2}\],": "Update screen data",
    r"cmp\s+word\s+ptr\s+\[0x61\d{2}\],": "Check screen data",
    # Message patterns
    r"mov\s+word\s+ptr\s+\[0x62\d{2}\],": "Update message data",
    r"cmp\s+word\s+ptr\s+\[0x62\d{2}\],": "Check message data",
    # Game mechanics patterns
    r"int\s+0x10": "Video BIOS interrupt (graphics/text)",
    r"int\s+0x16": "Keyboard BIOS interrupt",
    r"int\s+0x21": "DOS function call",
    r"int\s+0x33": "Mouse interrupt",
}


def generate_instruction_comment(instr: X86Instruction) -> Optional[str]:
    """
    Generate a comment for an instruction based on patterns.

    Args:
        instr: The instruction to comment

    Returns:
        A comment string or None if no pattern matches
    """
    # Combine mnemonic and operands
    instr_text = f"{instr.mnemonic} {instr.operands}"

    # Check instruction patterns
    for pattern, comment in INSTRUCTION_PATTERNS.items():
        if re.match(pattern, instr_text, re.IGNORECASE):
            return comment

    # Check Oregon Trail specific patterns
    for pattern, comment in OREGON_TRAIL_PATTERNS.items():
        if re.match(pattern, instr_text, re.IGNORECASE):
            return comment

    return None


def generate_code_block_comment(instructions: List[X86Instruction]) -> Optional[str]:
    """
    Generate a comment for a block of code based on patterns.

    Args:
        instructions: The instructions to comment

    Returns:
        A comment string or None if no pattern matches
    """
    # Combine instructions into a single string
    code_text = "\n".join(
        f"{instr.mnemonic} {instr.operands}" for instr in instructions
    )

    # Check code patterns
    for pattern, comment in CODE_PATTERNS.items():
        if re.search(pattern, code_text, re.IGNORECASE | re.MULTILINE):
            return comment

    return None


def generate_function_purpose_comment(function: DOSFunction) -> str:
    """
    Generate a comment describing the purpose of a function.

    Args:
        function: The function to comment

    Returns:
        A comment string
    """
    # Default comment
    purpose = "Unknown function purpose"

    # Check if we have instructions
    if not function.instructions:
        return purpose

    # Check for DOS interrupts
    dos_interrupts = []
    for instr in function.instructions:
        if instr.mnemonic == "int" and instr.operands.strip() in [
            "0x21",
            "0x10",
            "0x16",
            "0x33",
        ]:
            dos_interrupts.append(instr.operands.strip())

    # Determine function purpose based on interrupts
    if "0x21" in dos_interrupts:
        # DOS function
        ah_values = []
        for i, instr in enumerate(function.instructions):
            if instr.mnemonic == "mov" and instr.operands.startswith("ah,"):
                try:
                    ah_value = int(instr.operands.split(",")[1].strip(), 16)
                    ah_values.append(ah_value)
                except ValueError:
                    pass

        if ah_values:
            if 0x3D in ah_values:  # Open file
                purpose = "Opens a file"
            elif 0x3E in ah_values:  # Close file
                purpose = "Closes a file"
            elif 0x3F in ah_values:  # Read from file
                purpose = "Reads data from a file"
            elif 0x40 in ah_values:  # Write to file
                purpose = "Writes data to a file"
            elif 0x41 in ah_values:  # Delete file
                purpose = "Deletes a file"
            elif 0x42 in ah_values:  # Move file pointer
                purpose = "Moves file pointer"
            elif 0x48 in ah_values:  # Allocate memory
                purpose = "Allocates memory"
            elif 0x49 in ah_values:  # Free memory
                purpose = "Frees memory"
            elif 0x4A in ah_values:  # Resize memory block
                purpose = "Resizes memory block"
            else:
                purpose = "Performs DOS operations"

    elif "0x10" in dos_interrupts:
        # Video BIOS function
        ah_values = []
        for i, instr in enumerate(function.instructions):
            if instr.mnemonic == "mov" and instr.operands.startswith("ah,"):
                try:
                    ah_value = int(instr.operands.split(",")[1].strip(), 16)
                    ah_values.append(ah_value)
                except ValueError:
                    pass

        if ah_values:
            if 0x00 in ah_values or 0x01 in ah_values:  # Set video mode
                purpose = "Sets video mode"
            elif 0x02 in ah_values or 0x03 in ah_values:  # Set cursor position
                purpose = "Sets cursor position"
            elif 0x08 in ah_values or 0x09 in ah_values:  # Read/write character
                purpose = "Reads/writes characters to screen"
            elif 0x0C in ah_values or 0x0D in ah_values:  # Write/read pixel
                purpose = "Draws graphics on screen"
            elif 0x13 in ah_values:  # Write string
                purpose = "Writes text to screen"
            else:
                purpose = "Performs video operations"

    elif "0x16" in dos_interrupts:
        # Keyboard BIOS function
        purpose = "Handles keyboard input"

    elif "0x33" in dos_interrupts:
        # Mouse interrupt
        purpose = "Handles mouse input"

    # Check for string operations
    string_ops = [
        "movsb",
        "movsw",
        "stosb",
        "stosw",
        "lodsb",
        "lodsw",
        "cmpsb",
        "cmpsw",
        "scasb",
        "scasw",
    ]
    if any(instr.mnemonic in string_ops for instr in function.instructions):
        if purpose == "Unknown function purpose":
            purpose = "Manipulates strings or memory blocks"
        else:
            purpose += " and manipulates strings or memory blocks"

    # Check for arithmetic operations
    arithmetic_ops = ["add", "sub", "mul", "imul", "div", "idiv"]
    if any(instr.mnemonic in arithmetic_ops for instr in function.instructions):
        if purpose == "Unknown function purpose":
            purpose = "Performs arithmetic calculations"
        else:
            purpose += " and performs calculations"

    return purpose


def add_comments_to_function(function: DOSFunction):
    """
    Add comments to a function.

    Args:
        function: The function to add comments to
    """
    # Add function purpose comment
    function.purpose = generate_function_purpose_comment(function)

    # Add instruction comments
    for instr in function.instructions:
        instr.comment = generate_instruction_comment(instr)

    # Add code block comments
    block_size = 5  # Look at blocks of 5 instructions
    for i in range(len(function.instructions) - block_size + 1):
        block = function.instructions[i : i + block_size]
        block_comment = generate_code_block_comment(block)
        if block_comment:
            # Add the comment to the first instruction in the block
            if not block[0].comment:
                block[0].comment = block_comment
            else:
                block[0].comment += f"; {block_comment}"
