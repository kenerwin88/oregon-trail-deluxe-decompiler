"""
Code pattern recognition and simplification for the decompiler.
"""

from typing import Dict, List, Optional
import re

from .models import X86Instruction


class CodePattern:
    """Represents a code pattern that can be simplified"""

    def __init__(
        self,
        name: str,
        description: str,
        pattern: List[Dict[str, str]],
        replacement: str,
    ):
        self.name = name
        self.description = description
        self.pattern = pattern  # List of instruction patterns to match
        self.replacement = replacement  # Replacement code template

    def match(self, instructions: List[X86Instruction]) -> Optional[Dict[str, str]]:
        """
        Check if the instructions match this pattern.

        Args:
            instructions: List of instructions to check

        Returns:
            A dictionary of captured variables if matched, None otherwise
        """
        if len(instructions) < len(self.pattern):
            return None

        captures = {}

        for i, pattern_instr in enumerate(self.pattern):
            if i >= len(instructions):
                return None

            instr = instructions[i]

            # Check mnemonic
            if "mnemonic" in pattern_instr:
                if pattern_instr["mnemonic"] != instr.mnemonic:
                    return None

            # Check operands with regex
            if "operands_regex" in pattern_instr:
                regex = pattern_instr["operands_regex"]
                match = re.match(regex, instr.operands)
                if not match:
                    return None

                # Add captured groups to the captures dictionary
                for j, group in enumerate(match.groups(), 1):
                    captures[f"${i}_{j}"] = group

            # Check exact operands
            elif "operands" in pattern_instr:
                if pattern_instr["operands"] != instr.operands:
                    return None

        return captures

    def apply(self, captures: Dict[str, str]) -> str:
        """
        Apply the pattern replacement with the captured variables.

        Args:
            captures: Dictionary of captured variables

        Returns:
            The replacement code
        """
        result = self.replacement

        for key, value in captures.items():
            result = result.replace(key, value)

        return result


# Common x86 assembly patterns and their high-level equivalents
COMMON_PATTERNS = [
    # Zero register
    CodePattern(
        "zero_register",
        "Zero a register using XOR",
        [{"mnemonic": "xor", "operands_regex": r"([a-z]+),\s*\1"}],
        "$1 = 0;",
    ),
    # Increment
    CodePattern(
        "increment",
        "Increment a register or memory location",
        [{"mnemonic": "inc", "operands_regex": r"(.+)"}],
        "$1++;",
    ),
    # Decrement
    CodePattern(
        "decrement",
        "Decrement a register or memory location",
        [{"mnemonic": "dec", "operands_regex": r"(.+)"}],
        "$1--;",
    ),
    # Move immediate to register
    CodePattern(
        "move_immediate",
        "Move immediate value to register",
        [{"mnemonic": "mov", "operands_regex": r"([a-z]+),\s*(0x[0-9A-Fa-f]+|[0-9]+)"}],
        "$1 = $2;",
    ),
    # Move register to register
    CodePattern(
        "move_register",
        "Move register to register",
        [{"mnemonic": "mov", "operands_regex": r"([a-z]+),\s*([a-z]+)"}],
        "$1 = $2;",
    ),
    # Move memory to register
    CodePattern(
        "move_memory_to_register",
        "Move memory to register",
        [
            {
                "mnemonic": "mov",
                "operands_regex": r"([a-z]+),\s*(?:word|byte|dword)?\s*ptr\s*\[(.+)\]",
            }
        ],
        "$1 = *($2);",
    ),
    # Move register to memory
    CodePattern(
        "move_register_to_memory",
        "Move register to memory",
        [
            {
                "mnemonic": "mov",
                "operands_regex": r"(?:word|byte|dword)?\s*ptr\s*\[(.+)\],\s*([a-z]+)",
            }
        ],
        "*($1) = $2;",
    ),
    # Add immediate to register
    CodePattern(
        "add_immediate",
        "Add immediate value to register",
        [{"mnemonic": "add", "operands_regex": r"([a-z]+),\s*(0x[0-9A-Fa-f]+|[0-9]+)"}],
        "$1 += $2;",
    ),
    # Add register to register
    CodePattern(
        "add_register",
        "Add register to register",
        [{"mnemonic": "add", "operands_regex": r"([a-z]+),\s*([a-z]+)"}],
        "$1 += $2;",
    ),
    # Subtract immediate from register
    CodePattern(
        "subtract_immediate",
        "Subtract immediate value from register",
        [{"mnemonic": "sub", "operands_regex": r"([a-z]+),\s*(0x[0-9A-Fa-f]+|[0-9]+)"}],
        "$1 -= $2;",
    ),
    # Subtract register from register
    CodePattern(
        "subtract_register",
        "Subtract register from register",
        [{"mnemonic": "sub", "operands_regex": r"([a-z]+),\s*([a-z]+)"}],
        "$1 -= $2;",
    ),
    # Multiply register by immediate
    CodePattern(
        "multiply_immediate",
        "Multiply register by immediate value",
        [
            {
                "mnemonic": "imul",
                "operands_regex": r"([a-z]+),\s*(0x[0-9A-Fa-f]+|[0-9]+)",
            }
        ],
        "$1 *= $2;",
    ),
    # Compare register with immediate
    CodePattern(
        "compare_immediate",
        "Compare register with immediate value",
        [{"mnemonic": "cmp", "operands_regex": r"([a-z]+),\s*(0x[0-9A-Fa-f]+|[0-9]+)"}],
        "// Compare $1 with $2",
    ),
    # Compare register with register
    CodePattern(
        "compare_register",
        "Compare register with register",
        [{"mnemonic": "cmp", "operands_regex": r"([a-z]+),\s*([a-z]+)"}],
        "// Compare $1 with $2",
    ),
    # Push register
    CodePattern(
        "push_register",
        "Push register onto stack",
        [{"mnemonic": "push", "operands_regex": r"([a-z]+)"}],
        "push($1);",
    ),
    # Pop register
    CodePattern(
        "pop_register",
        "Pop value from stack into register",
        [{"mnemonic": "pop", "operands_regex": r"([a-z]+)"}],
        "$1 = pop();",
    ),
    # Call function
    CodePattern(
        "call_function",
        "Call function",
        [{"mnemonic": "call", "operands_regex": r"(.+)"}],
        "$1();",
    ),
    # Return
    CodePattern(
        "return",
        "Return from function",
        [{"mnemonic": "ret", "operands_regex": r".*"}],
        "return;",
    ),
    # Jump
    CodePattern(
        "jump",
        "Jump to address",
        [{"mnemonic": "jmp", "operands_regex": r"(.+)"}],
        "goto $1;",
    ),
    # Conditional jumps
    CodePattern(
        "jump_equal",
        "Jump if equal",
        [{"mnemonic": "je", "operands_regex": r"(.+)"}],
        "if (ZF) goto $1;",
    ),
    CodePattern(
        "jump_not_equal",
        "Jump if not equal",
        [{"mnemonic": "jne", "operands_regex": r"(.+)"}],
        "if (!ZF) goto $1;",
    ),
    CodePattern(
        "jump_zero",
        "Jump if zero",
        [{"mnemonic": "jz", "operands_regex": r"(.+)"}],
        "if (ZF) goto $1;",
    ),
    CodePattern(
        "jump_not_zero",
        "Jump if not zero",
        [{"mnemonic": "jnz", "operands_regex": r"(.+)"}],
        "if (!ZF) goto $1;",
    ),
    # More complex patterns
    # Swap registers using XOR
    CodePattern(
        "swap_registers_xor",
        "Swap registers using XOR",
        [
            {"mnemonic": "xor", "operands_regex": r"([a-z]+),\s*([a-z]+)"},
            {"mnemonic": "xor", "operands_regex": r"([a-z]+),\s*([a-z]+)"},
            {"mnemonic": "xor", "operands_regex": r"([a-z]+),\s*([a-z]+)"},
        ],
        "// Swap $1_1 and $1_2",
    ),
    # Loop initialization
    CodePattern(
        "loop_init",
        "Initialize loop counter",
        [
            {
                "mnemonic": "mov",
                "operands_regex": r"([a-z]+),\s*(0x[0-9A-Fa-f]+|[0-9]+)",
            },
            {
                "mnemonic": "cmp",
                "operands_regex": r"([a-z]+),\s*([a-z]+|0x[0-9A-Fa-f]+|[0-9]+)",
            },
        ],
        "for ($1_1 = $1_2; $1_1 < $2_2; $1_1++) {",
    ),
]


def simplify_instruction(instr: X86Instruction) -> str:
    """
    Simplify a single instruction using pattern matching.

    Args:
        instr: The instruction to simplify

    Returns:
        A simplified C-like representation of the instruction
    """
    # Create a single-instruction list for pattern matching
    instrs = [instr]

    # Try each pattern
    for pattern in COMMON_PATTERNS:
        captures = pattern.match(instrs)
        if captures:
            return pattern.apply(captures)

    # If no pattern matches, return the original instruction
    return f"{instr.mnemonic} {instr.operands};"


def simplify_instruction_sequence(instrs: List[X86Instruction]) -> List[str]:
    """
    Simplify a sequence of instructions using pattern matching.

    Args:
        instrs: The instructions to simplify

    Returns:
        A list of simplified C-like statements
    """
    result = []
    i = 0

    while i < len(instrs):
        # Try multi-instruction patterns first
        matched = False

        for pattern in sorted(
            COMMON_PATTERNS, key=lambda p: len(p.pattern), reverse=True
        ):
            if i + len(pattern.pattern) <= len(instrs):
                captures = pattern.match(instrs[i : i + len(pattern.pattern)])
                if captures:
                    result.append(pattern.apply(captures))
                    i += len(pattern.pattern)
                    matched = True
                    break

        # If no multi-instruction pattern matched, simplify the current instruction
        if not matched:
            result.append(simplify_instruction(instrs[i]))
            i += 1

    return result
