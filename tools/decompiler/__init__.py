"""
DOS Executable Decompiler Package

This package provides tools for decompiling DOS executables.
"""

from .models import DOSSegment, DOSFunction, X86Instruction, Variable
from .disassembler import DOSDecompiler
from .enhanced_disassembler import EnhancedDOSDecompiler
from .data_flow import DataFlowAnalyzer
from .dos_api import recognize_interrupt, format_interrupt_call
from .code_patterns import simplify_instruction, simplify_instruction_sequence
from .control_flow import improve_control_flow
from .utils import replace_memory_references, infer_variable_type, translate_condition
from .variable_naming import rename_variables, apply_variable_renaming
from .function_analysis import (
    update_function_signature,
    detect_parameters,
    detect_return_value,
)
from .data_structures import (
    update_function_with_data_structures,
    StructDefinition,
    ArrayDefinition,
)
from .comment_generator import add_comments_to_function, generate_instruction_comment
