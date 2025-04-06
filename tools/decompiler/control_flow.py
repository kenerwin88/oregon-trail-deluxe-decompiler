"""
Control flow analysis module for the DOS decompiler.
This module identifies high-level control structures in the
control flow graph such as loops, if statements, and switch statements.
"""

def improve_control_flow(cfg):
    """
    Analyze control flow graph to identify high-level structures.
    
    Args:
        cfg: Control flow graph to analyze
        
    Returns:
        Dictionary mapping structure types to lists of structures
    """
    # Initialize the structures dictionary
    structures = {
        "loops": [],
        "if_statements": [],
        "switch_statements": []
    }
    
    # Identify loops using dominator analysis
    structures["loops"] = identify_loops(cfg)
    
    # Identify if statements by looking for conditional branches
    structures["if_statements"] = identify_if_statements(cfg)
    
    # Identify switch statements by looking for jump tables
    structures["switch_statements"] = identify_switch_statements(cfg)
    
    return structures

def identify_loops(cfg):
    """
    Identify loops in the control flow graph using back edges in the depth-first search.
    
    Args:
        cfg: Control flow graph to analyze
        
    Returns:
        List of sets of block addresses that form loops
    """
    loops = []
    visited = set()
    path = set()
    
    def dfs(block):
        if not block:
            return
            
        block_addr = block.start_address
        
        # Skip if already fully processed
        if block_addr in visited:
            return
            
        # Back edge detected - we found a loop
        if block_addr in path:
            # Create a new loop starting from the current block
            loop_blocks = set()
            for succ in block.successors:
                # Add all reachable blocks to the loop
                if succ != block_addr:  # Avoid immediate self-loops
                    add_reachable_blocks(cfg, succ, block_addr, loop_blocks)
            
            # Include the loop header
            loop_blocks.add(block_addr)
            
            # Add the loop if it's not empty
            if loop_blocks:
                loops.append(loop_blocks)
            
            return
        
        # Add to current path
        path.add(block_addr)
        
        # Process successors
        for succ_addr in block.successors:
            succ_block = get_block_from_cfg(cfg, succ_addr)
            dfs(succ_block)
        
        # Remove from current path and mark as visited
        path.remove(block_addr)
        visited.add(block_addr)
    
    # Start DFS from entry block
    dfs(cfg.entry_block)
    
    return loops

# Helper method to get a block from a CFG
def get_block_from_cfg(cfg, addr):
    """Get a basic block from the CFG by its address"""
    if hasattr(cfg, 'get_block'):
        return cfg.get_block(addr)
    elif hasattr(cfg, 'blocks') and addr in cfg.blocks:
        return cfg.blocks[addr]
    return None
    
def add_reachable_blocks(cfg, start_addr, end_addr, result_set):
    """Helper function to add all blocks reachable from start_addr until end_addr"""
    visited = set()
    
    def dfs(addr):
        if addr == end_addr or addr in visited:
            return
        
        visited.add(addr)
        result_set.add(addr)
        
        block = get_block_from_cfg(cfg, addr)
        if block:
            for succ in block.successors:
                dfs(succ)
    
    dfs(start_addr)

def identify_if_statements(cfg):
    """
    Identify if statements by looking for conditional branches.
    
    Args:
        cfg: Control flow graph to analyze
        
    Returns:
        List of dictionaries representing if statements
    """
    if_statements = []
    
    for block in cfg.blocks.values():
        # Look for blocks with exactly two successors (true/false branch)
        if len(block.successors) == 2:
            # Extract the condition from the last instruction
            condition = None
            if block.instructions:
                last_instr = block.instructions[-1]
                if last_instr.mnemonic in ["je", "jne", "jz", "jnz", "jg", "jge", "jl", "jle"]:
                    condition = translate_condition(last_instr.mnemonic, last_instr.operands)
            
            if condition:
                # Create an if statement structure
                if_stmt = {
                    "header_block": block.start_address,
                    "condition": condition,
                    "true_branch": block.successors[0],
                    "false_branch": block.successors[1] if len(block.successors) > 1 else None
                }
                if_statements.append(if_stmt)
    
    return if_statements

def identify_switch_statements(cfg):
    """
    Identify switch statements by looking for jump tables.
    
    Args:
        cfg: Control flow graph to analyze
        
    Returns:
        List of dictionaries representing switch statements
    """
    switch_statements = []
    
    for block in cfg.blocks.values():
        # Look for blocks with 3+ successors (potential switch)
        if len(block.successors) >= 3:
            # Look for indirect jumps or jump tables
            has_indirect_jump = False
            switch_var = None
            
            for instr in block.instructions:
                if instr.mnemonic in ["jmp", "call"] and "[" in instr.operands:
                    has_indirect_jump = True
                    # Try to extract the switch variable
                    switch_var = extract_switch_variable(instr.operands)
                    break
            
            if has_indirect_jump:
                # Create a switch statement structure
                switch_stmt = {
                    "header_block": block.start_address,
                    "variable": switch_var,
                    "cases": [{"value": i, "target": succ} for i, succ in enumerate(block.successors)]
                }
                switch_statements.append(switch_stmt)
    
    return switch_statements

def extract_switch_variable(operand):
    """Extract the variable name from an indirect jump operand"""
    # Example: jmp [ax + table] -> return "ax"
    parts = operand.replace("[", "").replace("]", "").split("+")
    if parts:
        return parts[0].strip()
    return None

def translate_condition(mnemonic, operands):
    """
    Translate an assembly conditional jump to a C-like condition.
    
    Args:
        mnemonic: Jump instruction mnemonic (je, jne, etc.)
        operands: Jump instruction operands
        
    Returns:
        String containing a C-like condition
    """
    # This is a simple mapping of jump instructions to C conditions
    condition_map = {
        "je": "== 0",   # Jump if equal (zero)
        "jz": "== 0",   # Jump if zero
        "jne": "!= 0",  # Jump if not equal (not zero)
        "jnz": "!= 0",  # Jump if not zero
        "jg": "> 0",    # Jump if greater
        "jge": ">= 0",  # Jump if greater or equal
        "jl": "< 0",    # Jump if less
        "jle": "<= 0",  # Jump if less or equal
    }
    
    # Default to the mnemonic if we don't have a mapping
    condition = condition_map.get(mnemonic, mnemonic)
    
    # Simple case: just return the condition based on flags
    return condition
