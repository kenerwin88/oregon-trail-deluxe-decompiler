"""
Analyzer modules package for the Oregon Trail decompiler.

This package contains various analyzer modules that provide different
kinds of analysis on the decompiled code:

- CallGraphAnalyzer: Analyzes function call relationships
- ResourceAnalyzer: Analyzes references to resource files
- StateMachineAnalyzer: Analyzes state machines in the decompiled code
- DataStructureRecognizer: Analyzes data structures in the decompiled code
"""

from .call_graph import CallGraphAnalyzer
from .resources import ResourceAnalyzer
from .state_machine import StateMachineAnalyzer
from .data_structures import DataStructureRecognizer

__all__ = [
    'CallGraphAnalyzer',
    'ResourceAnalyzer',
    'StateMachineAnalyzer',
    'DataStructureRecognizer',
]