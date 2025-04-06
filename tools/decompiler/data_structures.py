"""
Compatibility module for data structure recognition.
This redirects to the new analyzers.data_structures module.
"""

from .analyzers.data_structures import DataStructure, Array, Struct

def update_function_with_data_structures(function):
    """
    Legacy function for updating functions with data structure information.
    Now simply returns True as this functionality is handled in the analyzers.
    
    Args:
        function: The function to update
        
    Returns:
        True to indicate success
    """
    # This functionality is now handled in the DataStructureRecognizer class
    return True
