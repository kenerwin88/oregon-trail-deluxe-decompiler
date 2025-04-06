"""
Compatibility module for DOS API functions.
This redirects to the new enhanced_output module.
"""

from .enhanced_output import analyze_interrupt as recognize_interrupt

# Re-export the function for backward compatibility
__all__ = ['recognize_interrupt']
