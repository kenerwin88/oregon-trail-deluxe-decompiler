"""
Compatibility module for code pattern detection.
"""

def simplify_instruction(instruction):
    """
    Simplify an instruction for better readability.
    
    Args:
        instruction: The instruction to simplify
        
    Returns:
        Simplified instruction text
    """
    # Basic implementation - in a real implementation we would do more complex analysis
    if hasattr(instruction, "simplified") and instruction.simplified:
        return instruction.simplified
    
    if not hasattr(instruction, "mnemonic") or not hasattr(instruction, "operands"):
        return str(instruction)
        
    return f"{instruction.mnemonic} {instruction.operands}"

def simplify_instruction_sequence(instructions):
    """
    Simplify a sequence of instructions into higher-level operations.
    
    Args:
        instructions: List of instructions to simplify
        
    Returns:
        List of simplified instruction text
    """
    # Basic implementation
    return [simplify_instruction(instr) for instr in instructions]
