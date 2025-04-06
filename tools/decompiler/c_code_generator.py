"""
Comprehensive C code generator for the Oregon Trail decompiler.
This module transforms the analyzed functions into readable C code with
game-specific knowledge integration.
"""

from .control_flow import get_block_from_cfg
from .oregon_trail_specific import (
    enhance_c_code_with_game_knowledge,
    enhance_function_signature,
    identify_game_data_structures,
    enhance_instruction_with_game_knowledge
)

def generate_c_code(functions, strings=None):
    """
    Generate comprehensive C code from analyzed functions.
    
    Args:
        functions: List of functions to generate code for
        strings: Optional dictionary of string literals
        
    Returns:
        Generated C code as a string
    """
    # First, enhance functions with game-specific knowledge
    for func in functions:
        # Try to identify and enhance function signatures
        enhance_function_signature(func)
        
        # Identify game-specific data structures
        if hasattr(func, "instructions") and func.instructions:
            structs = identify_game_data_structures(func)
            if not hasattr(func, "struct_defs"):
                func.struct_defs = {}
            func.struct_defs.update(structs)
    
    code = []
    
    # Add includes
    code.append("#include <stdio.h>")
    code.append("#include <stdlib.h>")
    code.append("#include <string.h>")
    code.append("#include <dos.h>")  # For DOS-specific functions
    code.append("")
    
    # Generate data structure definitions
    struct_defs = {}
    for func in functions:
        if hasattr(func, "struct_defs"):
            for addr, struct_def in func.struct_defs.items():
                if addr not in struct_defs:
                    struct_defs[addr] = struct_def
    
    if struct_defs:
        code.append("// Data structure definitions")
        for addr, struct_def in sorted(struct_defs.items()):
            code.append(str(struct_def))
        code.append("")
    
    # Gather all global variables
    global_vars = set()
    for func in functions:
        if hasattr(func, "variables"):
            for var in func.variables.values():
                if hasattr(var, "is_global") and var.is_global:
                    global_vars.add(var)
    
    # Add global variable declarations
    if global_vars:
        code.append("// Global variables")
        for var in sorted(global_vars, key=lambda v: v.name):
            if hasattr(var, "is_array") and var.is_array:
                code.append(f"{var.type} {var.name}[{var.array_length}];")
            elif hasattr(var, "is_struct") and var.is_struct:
                code.append(f"struct {var.struct_name} {var.name};")
            else:
                code.append(f"{var.type} {var.name};")
        code.append("")
    
    # Add forward declarations
    code.append("// Forward declarations")
    for func in sorted(functions, key=lambda f: f.name):
        if hasattr(func, "signature") and func.signature:
            code.append(f"{func.signature};")
        else:
            code.append(f"void {func.name}();")
    code.append("")
    
    # Add string literals if provided
    if strings:
        code.append("// String literals")
        for addr, string in sorted(strings.items()):
            safe_string = string.replace('"', '\\"').replace('\n', '\\n')
            code.append(f'const char *str_{addr:X} = "{safe_string}";')
        code.append("")
    
    # Add function implementations
    for func in sorted(functions, key=lambda f: f.name):
        # Add function signature
        if hasattr(func, "signature") and func.signature:
            code.append(f"{func.signature} {{")
        else:
            code.append(f"void {func.name}() {{")
        
        # Add function purpose
        if hasattr(func, "purpose") and func.purpose:
            code.append(f"    // Purpose: {func.purpose}")
            code.append("")
        
        # Add variable declarations
        if hasattr(func, "variables") and func.variables:
            local_vars = [v for v in func.variables.values()
                         if not getattr(v, "is_parameter", False) and
                            not getattr(v, "is_return_value", False) and
                            not getattr(v, "is_global", False)]
            
            if local_vars:
                code.append("    // Local variables")
                for var in sorted(local_vars, key=lambda v: v.name):
                    if getattr(var, "is_array", False):
                        code.append(f"    {var.type} {var.name}[{getattr(var, 'array_length', 0)}];")
                    elif getattr(var, "is_struct", False):
                        code.append(f"    struct {var.struct_name} {var.name};")
                    else:
                        code.append(f"    {var.type} {var.name};")
                code.append("")
        
        # Get function implementation
        implementation = get_function_implementation(func)
        if implementation:
            code.extend(["    " + line for line in implementation.split("\n")])
        else:
            # Fallback if no implementation could be generated
            if hasattr(func, "cfg") and func.cfg and func.cfg.entry_block:
                code.append("    // Implementation not available - control flow analysis only")
                code.append("    // Control flow structures:")
                if hasattr(func, "cfg") and func.cfg:
                    if hasattr(func.cfg, "loops") and func.cfg.loops:
                        code.append(f"    // - {len(func.cfg.loops)} loops identified")
                    if hasattr(func.cfg, "if_statements") and func.cfg.if_statements:
                        code.append(f"    // - {len(func.cfg.if_statements)} if statements identified")
            else:
                code.append("    // TODO: Implementation")
        
        code.append("}")
        code.append("")
    
    # Generate the basic C code
    c_code = "\n".join(code)
    
    # Enhance with game-specific knowledge
    enhanced_code = enhance_c_code_with_game_knowledge(c_code, functions)
    
    return enhanced_code

def get_function_implementation(func):
    """
    Generate the implementation for a function based on its control flow graph and instructions.
    
    Args:
        func: The function object to generate implementation for
        
    Returns:
        String containing the function implementation
    """
    # If we have a control flow graph, use it to generate structured code
    if hasattr(func, "cfg") and func.cfg and func.cfg.entry_block:
        return generate_structured_code_from_cfg(func)
    
    # Otherwise, fallback to direct instruction to C conversion
    elif hasattr(func, "instructions") and func.instructions:
        return generate_code_from_instructions(func)
    
    # No code can be generated
    return None

def generate_structured_code_from_cfg(func):
    """
    Generate structured C code based on a function's control flow graph.
    
    Args:
        func: The function object with a control flow graph
        
    Returns:
        String containing structured C code
    """
    lines = []
    
    # Function implementation based on CFG
    # Process basic blocks in order
    processed_blocks = set()
    
    def process_block(block, indent=""):
        if block.address in processed_blocks:
            return
        
        processed_blocks.add(block.address)
        
        # Convert each instruction to C
        for instr in block.instructions:
            # Skip instruction if it's just part of a control structure
            if hasattr(instr, "is_control_structure") and instr.is_control_structure:
                continue
                
            # Convert instruction to C code with game-specific enhancements
            enhanced_instr = enhance_instruction_with_game_knowledge(instr)
            c_line = instruction_to_c(instr, func)
            
            if c_line:
                if hasattr(instr, "comment") and instr.comment:
                    lines.append(f"{indent}{c_line} // {instr.comment}")
                else:
                    lines.append(f"{indent}{c_line}")
        
        # Handle control flow
        if hasattr(block, "condition") and block.condition:
            # If statement
            lines.append(f"{indent}if ({block.condition}) {{")
            
            # Process true branch
            if block.true_branch:
                true_block = get_block_from_cfg(func.cfg, block.true_branch)
                if true_block:
                    process_block(true_block, indent + "    ")
            
            # Add else branch if needed
            if block.false_branch:
                lines.append(f"{indent}}} else {{")
                false_block = get_block_from_cfg(func.cfg, block.false_branch)
                if false_block:
                    process_block(false_block, indent + "    ")
            
            lines.append(f"{indent}}}")
        
        # Handle loops
        elif hasattr(func.cfg, "loops") and any(block.start_address in loop for loop in func.cfg.loops):
            # Find the loop this block is part of
            for loop_blocks in func.cfg.loops:
                if block.start_address in loop_blocks:
                    # Loop header
                    lines.append(f"{indent}while (1) {{  // Loop at {block.start_address:X}")
                    
                    # Process loop body
                    for loop_block_addr in loop_blocks:
                        if loop_block_addr != block.start_address:  # Skip the header we're already processing
                            loop_block = get_block_from_cfg(func.cfg, loop_block_addr)
                            if loop_block:
                                process_block(loop_block, indent + "    ")
                    
                    lines.append(f"{indent}}}")
                    break
        
        # Handle straight-line successors
        elif block.successors and len(block.successors) == 1 and block.successors[0] not in processed_blocks:
            next_block = get_block_from_cfg(func.cfg, block.successors[0])
            if next_block:
                process_block(next_block, indent)
    
    # Start with the entry block
    if func.cfg and func.cfg.entry_block:
        process_block(func.cfg.entry_block)
    
    return "\n".join(lines)

def generate_code_from_instructions(func):
    """
    Generate C code by directly translating each instruction.
    
    Args:
        func: The function object with instructions
        
    Returns:
        String containing C code
    """
    lines = []
    
    for instr in func.instructions:
        # Enhance instruction with game-specific knowledge
        enhance_instruction_with_game_knowledge(instr)
        
        c_line = instruction_to_c(instr, func)
        if c_line:
            if hasattr(instr, "comment") and instr.comment:
                lines.append(f"{c_line} // {instr.comment}")
            else:
                lines.append(c_line)
    
    return "\n".join(lines)

def instruction_to_c(instr, func):
    """
    Convert an assembly instruction to equivalent C code.
    
    Args:
        instr: Assembly instruction object
        func: Function context
        
    Returns:
        String containing C code equivalent of the instruction
    """
    # Skip function prologue/epilogue instructions
    if instr.mnemonic in ["push", "pop"] and instr.operands in ["bp", "sp"]:
        return None
    if instr.mnemonic == "mov" and instr.operands in ["bp, sp", "sp, bp"]:
        return None
    if instr.mnemonic == "ret":
        return "return;"
    
    # Basic instruction conversion - this is simplified and would need to be expanded
    if instr.mnemonic == "mov":
        parts = instr.operands.split(", ")
        if len(parts) == 2:
            dest, src = parts
            # Check if either operand is a variable
            dest_var = get_variable_for_operand(dest, func)
            src_var = get_variable_for_operand(src, func)
            
            if dest_var and src_var:
                return f"{dest_var} = {src_var};"
            elif dest_var:
                return f"{dest_var} = {src};"
            elif src_var:
                return f"{dest} = {src_var};"
            else:
                # Special case for game-specific memory addresses
                if "[game_state]" in dest or "[game_state]" in src:
                    if "0x" in src:
                        # Try to make value more readable for game states
                        for state_val, state_name in {0: "GAME_STATE_MENU", 1: "GAME_STATE_SETUP"}.items():
                            if f"0x{state_val}" in src or str(state_val) in src:
                                return f"{dest} = {state_name};"
                return f"{dest} = {src};"
    
    elif instr.mnemonic == "call":
        # Check if it's a call to a known function
        try:
            target = int(instr.operands, 16)
            for target_func in func.all_functions if hasattr(func, "all_functions") else []:
                if hasattr(target_func, "start_address") and target_func.start_address == target:
                    if hasattr(target_func, "purpose") and target_func.purpose:
                        return f"{target_func.name}();  // {target_func.purpose}"
                    return f"{target_func.name}();"
            return f"call_function_0x{target:X}();"
        except ValueError:
            # Handle register/memory calls
            return f"call_via_{instr.operands}();"
    
    elif instr.mnemonic == "int":
        # Handle DOS/BIOS interrupts with more specific game-related knowledge
        if instr.operands == "0x21":
            # DOS function
            return "dos_interrupt();"
        elif instr.operands == "0x10":
            # Video services
            return "bios_video_interrupt();"
        elif instr.operands == "0x33":
            # Mouse services
            return "mouse_interrupt();"
        return f"interrupt({instr.operands});"
    
    # For now, return a comment for other instructions
    return f"/* {instr.mnemonic} {instr.operands} */"

def get_variable_for_operand(operand, func):
    """
    Find the variable name for an assembly operand.
    
    Args:
        operand: Assembly operand string
        func: Function context
        
    Returns:
        Variable name if found, otherwise None
    """
    if not hasattr(func, "variables") or not func.variables:
        return None
    
    # Simple version - would need expansion for memory references, etc.
    for var in func.variables.values():
        if hasattr(var, "register") and var.register == operand:
            return var.name
        if hasattr(var, "memory_reference") and var.memory_reference in operand:
            return var.name
    
    # Check for game-specific memory references
    if "0x5c00" in operand:
        return "game_state"
    elif "0x5c02" in operand:
        return "current_month"
    elif "0x5c04" in operand:
        return "current_day"
    elif "0x5c06" in operand:
        return "current_year"
    elif "0x5c08" in operand:
        return "total_miles_traveled"
    
    return None
