"""
Compatibility module for function analysis.
"""

def update_function_signature(function):
    """
    Update function signature based on analysis of parameters and return values.
    
    Args:
        function: The function to update
        
    Returns:
        True if signature was updated, False otherwise
    """
    # Simple implementation
    if not hasattr(function, "signature") or not function.signature:
        # Set a default signature
        if hasattr(function, "return_type") and function.return_type:
            function.signature = f"{function.return_type} {function.name}()"
        else:
            function.signature = f"void {function.name}()"
        
        # Add parameters if available
        if hasattr(function, "variables"):
            params = [v for v in function.variables.values() if hasattr(v, "is_parameter") and v.is_parameter]
            if params:
                param_list = []
                for param in sorted(params, key=lambda p: p.parameter_index if hasattr(p, "parameter_index") else 0):
                    param_type = param.type if hasattr(param, "type") else "int"
                    param_list.append(f"{param_type} {param.name}")
                
                function.signature = f"{function.return_type or 'void'} {function.name}({', '.join(param_list)})"
        
        return True
    
    return False
