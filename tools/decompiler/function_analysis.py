"""
Function parameter and return value detection for the decompiler.
"""

import re
from typing import List, Optional, Tuple

from .models import DOSFunction, Variable


class FunctionParameter:
    """Represents a function parameter"""

    def __init__(self, name: str, type: str, size: int, register: Optional[str] = None):
        self.name = name
        self.type = type
        self.size = size
        self.register = register

    def __str__(self):
        return f"{self.type} {self.name}"


class FunctionSignature:
    """Represents a function signature with parameters and return value"""

    def __init__(self, function: DOSFunction):
        self.function = function
        self.parameters: List[FunctionParameter] = []
        self.return_type: Optional[str] = None
        self.return_register: Optional[str] = None

    def add_parameter(self, param: FunctionParameter):
        self.parameters.append(param)

    def set_return_type(self, type_name: str, register: Optional[str] = None):
        self.return_type = type_name
        self.return_register = register

    def __str__(self):
        params_str = ", ".join(str(p) for p in self.parameters)
        return_str = self.return_type if self.return_type else "void"
        return f"{return_str} {self.function.name}({params_str})"


def detect_parameters(function: DOSFunction) -> List[FunctionParameter]:
    """
    Detect function parameters based on register and stack usage.

    In x86 16-bit calling conventions, parameters are typically passed:
    1. In registers (AX, BX, CX, DX) for small functions
    2. On the stack for larger functions (accessed via BP+n)

    Args:
        function: The function to analyze

    Returns:
        A list of detected parameters
    """
    parameters = []

    # Check if we have instructions
    if not function.instructions:
        return parameters

    # Look for stack-based parameters (accessed via BP+n)
    stack_params = set()
    for instr in function.instructions[:20]:  # Check first 20 instructions
        # Look for BP+n references
        if "bp+" in instr.operands.lower():
            # Extract the offset
            match = re.search(r"bp\+(\d+)", instr.operands.lower())
            if match:
                offset = int(match.group(1))
                if offset >= 4:  # Skip saved BP and return address
                    stack_params.add(offset)

    # Create parameters for stack-based parameters
    for i, offset in enumerate(sorted(stack_params)):
        param = FunctionParameter(
            name=f"param_{i + 1}",
            type="int",  # Default type
            size=2,  # Default size
        )
        parameters.append(param)

    # Look for register-based parameters
    reg_params = set()
    for instr in function.instructions[:10]:  # Check first 10 instructions
        # Look for register usage
        if instr.mnemonic in ["mov", "push", "pop", "test", "cmp"] and any(
            reg in instr.operands.lower() for reg in ["ax", "bx", "cx", "dx"]
        ):
            for reg in ["ax", "bx", "cx", "dx"]:
                if reg in instr.operands.lower():
                    reg_params.add(reg)

    # Create parameters for register-based parameters
    for i, reg in enumerate(sorted(reg_params)):
        # Only add if we don't already have stack parameters
        if not stack_params:
            param = FunctionParameter(
                name=f"reg_{reg}",
                type="int",  # Default type
                size=2,  # Default size
                register=reg,
            )
            parameters.append(param)

    return parameters


def detect_return_value(function: DOSFunction) -> Optional[Tuple[str, str]]:
    """
    Detect function return value based on register usage.

    In x86 16-bit calling conventions, return values are typically:
    1. In AX for 16-bit values
    2. In DX:AX for 32-bit values

    Args:
        function: The function to analyze

    Returns:
        A tuple of (return_type, return_register) or None if no return value
    """
    # Check if we have instructions
    if not function.instructions:
        return None

    # Look for return value in AX
    ax_return = False
    dx_ax_return = False

    # Check the last 10 instructions before any ret
    for i in range(
        len(function.instructions) - 1, max(0, len(function.instructions) - 10), -1
    ):
        instr = function.instructions[i]

        # Stop if we hit a return
        if instr.mnemonic in ["ret", "retf"]:
            break

        # Look for AX usage
        if "ax" in instr.operands.lower() and instr.mnemonic in [
            "mov",
            "add",
            "sub",
            "xor",
            "or",
            "and",
        ]:
            ax_return = True

        # Look for DX:AX usage
        if (
            "dx" in instr.operands.lower()
            and "ax" in instr.operands.lower()
            and instr.mnemonic in ["mov", "add", "sub", "xor", "or", "and"]
        ):
            dx_ax_return = True

    if dx_ax_return:
        return ("long", "dx:ax")
    elif ax_return:
        return ("int", "ax")

    return None


def analyze_function_signature(function: DOSFunction) -> FunctionSignature:
    """
    Analyze a function to determine its signature (parameters and return value).

    Args:
        function: The function to analyze

    Returns:
        A FunctionSignature object
    """
    signature = FunctionSignature(function)

    # Detect parameters
    params = detect_parameters(function)
    for param in params:
        signature.add_parameter(param)

    # Detect return value
    return_info = detect_return_value(function)
    if return_info:
        return_type, return_reg = return_info
        signature.set_return_type(return_type, return_reg)

    return signature


def update_function_signature(function: DOSFunction):
    """
    Update a function with its detected signature.

    Args:
        function: The function to update
    """
    signature = analyze_function_signature(function)

    # Update function name to include parameter types
    param_types = [p.type for p in signature.parameters]
    if param_types:
        function.signature = f"{signature.return_type or 'void'} {function.name}({', '.join(param_types)})"
    else:
        function.signature = f"{signature.return_type or 'void'} {function.name}(void)"

    # Add parameters to function variables
    for i, param in enumerate(signature.parameters):
        var_name = f"param_{i + 1}"
        if var_name not in function.variables:
            var = Variable(name=var_name, address=None, register=param.register)
            var.type = param.type
            var.size = param.size
            var.is_parameter = True
            var.parameter_index = i + 1
            function.variables[var_name] = var

    # Add return value to function
    function.return_type = signature.return_type
    function.return_register = signature.return_register
