"""
Utility functions for the DOS decompiler.
"""

import re
from typing import Dict, List, Tuple

from .models import Variable


def replace_memory_references(operands: str, variables: Dict[str, Variable]) -> str:
    """
    Replace memory references with variable names.

    Args:
        operands: The instruction operands string
        variables: Dictionary of variables (name -> Variable)

    Returns:
        The operands string with memory references replaced by variable names
    """
    if not variables:
        return operands

    result = operands

    # Create a mapping of addresses to variable names
    addr_to_var = {}
    for var_name, var in variables.items():
        if var.address is not None:
            addr_to_var[var.address] = var_name

    # Find all memory references in the operands
    # Pattern: [0xXXXX] or word ptr [0xXXXX] or byte ptr [0xXXXX], etc.
    mem_refs = re.finditer(
        r"((?:word|byte|dword|qword)?\s*ptr\s*)?\[0x([0-9A-Fa-f]+)(?:\s*\+\s*([^\]]+))?\]",
        result,
    )

    # Replace each memory reference with the corresponding variable name
    for match in mem_refs:
        ptr_type = match.group(1) or ""
        addr_hex = match.group(2)
        offset = match.group(3)

        try:
            addr = int(addr_hex, 16)
            if addr in addr_to_var:
                var_name = addr_to_var[addr]

                if offset:
                    # Memory reference with offset: [0xXXXX + offset]
                    if ptr_type:
                        # With ptr type: word ptr [0xXXXX + offset]
                        old_ref = f"{ptr_type}[0x{addr_hex} + {offset}]"
                        new_ref = f"{ptr_type}{var_name}[{offset}]"
                    else:
                        # Without ptr type: [0xXXXX + offset]
                        old_ref = f"[0x{addr_hex} + {offset}]"
                        new_ref = f"{var_name}[{offset}]"
                else:
                    # Simple memory reference: [0xXXXX]
                    if ptr_type:
                        # With ptr type: word ptr [0xXXXX]
                        old_ref = f"{ptr_type}[0x{addr_hex}]"
                        new_ref = f"{ptr_type}{var_name}"
                    else:
                        # Without ptr type: [0xXXXX]
                        old_ref = f"[0x{addr_hex}]"
                        new_ref = var_name

                result = result.replace(old_ref, new_ref)
        except ValueError:
            pass

    return result


def infer_variable_type(var: Variable, instructions: List) -> Tuple[str, int]:
    """
    Infer the type of a variable based on its usage.

    Args:
        var: The variable to infer the type for
        instructions: List of instructions that reference the variable

    Returns:
        A tuple of (type, size)
    """
    # Default type and size
    var_type = "int"
    var_size = 2

    # Check if the variable is used with byte ptr, word ptr, or dword ptr
    for instr in instructions:
        if var.address is not None:
            addr_hex = f"0x{var.address:X}"

            if "byte ptr" in instr.operands and addr_hex in instr.operands:
                var_type = "char"
                var_size = 1
                break
            elif "word ptr" in instr.operands and addr_hex in instr.operands:
                var_type = "int"
                var_size = 2
                break
            elif "dword ptr" in instr.operands and addr_hex in instr.operands:
                var_type = "long"
                var_size = 4
                break

    # Check if the variable is used in string operations
    for instr in instructions:
        if instr.mnemonic in [
            "movsb",
            "movsw",
            "movsd",
            "stosb",
            "stosw",
            "stosd",
            "lodsb",
            "lodsw",
            "lodsd",
        ]:
            if var.address is not None:
                addr_hex = f"0x{var.address:X}"
                if addr_hex in instr.operands:
                    if instr.mnemonic in ["movsb", "stosb", "lodsb"]:
                        var_type = "char[]"
                        var_size = 1
                    elif instr.mnemonic in ["movsw", "stosw", "lodsw"]:
                        var_type = "int[]"
                        var_size = 2
                    elif instr.mnemonic in ["movsd", "stosd", "lodsd"]:
                        var_type = "long[]"
                        var_size = 4
                    break

    return var_type, var_size


def translate_condition(mnemonic: str) -> str:
    """
    Translate a jump mnemonic to a C-like condition.

    Args:
        mnemonic: The jump mnemonic

    Returns:
        A C-like condition string
    """
    translations = {
        "je": "a == b",
        "jne": "a != b",
        "jz": "a == 0",
        "jnz": "a != 0",
        "jg": "a > b",
        "jge": "a >= b",
        "jl": "a < b",
        "jle": "a <= b",
        "ja": "a > b (unsigned)",
        "jae": "a >= b (unsigned)",
        "jb": "a < b (unsigned)",
        "jbe": "a <= b (unsigned)",
    }
    return translations.get(mnemonic, f"condition_{mnemonic}")
