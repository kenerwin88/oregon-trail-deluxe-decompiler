"""
Compatibility module for comment generation.
"""

def add_comments_to_function(function):
    """
    Add explanatory comments to a function.
    
    Args:
        function: The function to add comments to
        
    Returns:
        True if comments were added, False otherwise
    """
    # Simple implementation
    comments_added = 0
    
    # Check if function already has instructions with comments
    has_comments = any(
        hasattr(instr, "comment") and instr.comment
        for instr in function.instructions
    ) if hasattr(function, "instructions") else False
    
    if not has_comments and hasattr(function, "instructions"):
        # Add some basic comments
        for i, instr in enumerate(function.instructions):
            # Add comment for function entry
            if i == 0:
                instr.comment = "Function entry point"
                comments_added += 1
                
            # Add comment for return instructions
            elif instr.mnemonic.lower() in ["ret", "retf", "retn", "iret"]:
                instr.comment = "Return from function"
                comments_added += 1
                
            # Add comment for call instructions
            elif instr.mnemonic.lower() == "call":
                instr.comment = "Call to another function"
                comments_added += 1
    
    # Add a comment about function purpose if not present
    if not hasattr(function, "purpose") or not function.purpose:
        if function.name == "entry":
            function.purpose = "Program entry point"
            comments_added += 1
    
    return comments_added > 0
