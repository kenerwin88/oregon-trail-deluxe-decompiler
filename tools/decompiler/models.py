"""
Data models for the DOS decompiler.
"""

from typing import List, Dict, Optional


class X86Instruction:
    """Represents an x86 instruction"""

    def __init__(self, address: int, bytes_data: bytes, mnemonic: str, operands: str):
        self.address = address
        self.bytes_data = bytes_data
        self.mnemonic = mnemonic
        self.operands = operands
        self.comment = None  # Comment explaining the instruction
        self.simplified = None  # Simplified version of the instruction

    def __str__(self) -> str:
        if self.comment:
            return (
                f"{self.address:08X}: {self.mnemonic} {self.operands} // {self.comment}"
            )
        else:
            return f"{self.address:08X}: {self.mnemonic} {self.operands}"


class DOSSegment:
    """Represents a segment in the DOS executable"""

    def __init__(self, name: str, start_offset: int, size: int, type: str = "CODE"):
        self.name = name
        self.start_offset = start_offset
        self.size = size
        self.type = type
        self.data = bytearray()
        self.instructions: List[X86Instruction] = []

    def load_data(self, data: bytes):
        """Load segment data"""
        self.data = bytearray(data)

    def __str__(self) -> str:
        return f"Segment {self.name}: {self.start_offset:08X} - {self.start_offset + self.size:08X}, Type: {self.type}"


class BasicBlock:
    """Represents a basic block in the control flow graph"""

    def __init__(self, start_address: int):
        self.start_address = start_address
        self.instructions: List[X86Instruction] = []
        self.successors: List[int] = []  # Addresses of successor blocks

    def add_instruction(self, instruction: X86Instruction):
        """Add an instruction to the block"""
        self.instructions.append(instruction)

    def add_successor(self, address: int):
        """Add a successor block address"""
        if address not in self.successors:
            self.successors.append(address)

    def is_conditional_branch(self) -> bool:
        """Check if the block ends with a conditional branch"""
        if not self.instructions:
            return False

        last_instr = self.instructions[-1]
        return last_instr.mnemonic.startswith("j") and last_instr.mnemonic not in [
            "jmp",
            "jmpe",
        ]

    def is_unconditional_jump(self) -> bool:
        """Check if the block ends with an unconditional jump"""
        if not self.instructions:
            return False

        last_instr = self.instructions[-1]
        return last_instr.mnemonic in ["jmp", "jmpe"]

    def is_function_return(self) -> bool:
        """Check if the block ends with a return instruction"""
        if not self.instructions:
            return False

        last_instr = self.instructions[-1]
        return last_instr.mnemonic in ["ret", "retf", "retn", "iret"]

    def __str__(self) -> str:
        return (
            f"Block 0x{self.start_address:X} with {len(self.instructions)} instructions"
        )


class ControlFlowGraph:
    """Represents a control flow graph for a function"""

    def __init__(self, function):
        self.function = function
        self.blocks: Dict[int, BasicBlock] = {}  # Address -> BasicBlock
        self.entry_block = None

    def build(self):
        """Build the control flow graph from the function's instructions"""
        if not self.function.instructions:
            return

        # Create the entry block
        self.entry_block = BasicBlock(self.function.start_address)
        self.blocks[self.function.start_address] = self.entry_block

        # First pass: identify basic block boundaries
        block_starts = {self.function.start_address}

        for instr in self.function.instructions:
            # Check if this instruction is a branch
            if instr.mnemonic.startswith("j"):
                # Add the target address as a block start
                try:
                    target = int(instr.operands, 16)
                    block_starts.add(target)
                except ValueError:
                    pass

                # Add the next instruction as a block start (except for unconditional jumps)
                if instr.mnemonic != "jmp":
                    next_addr = instr.address + len(instr.bytes_data)
                    block_starts.add(next_addr)

            # Check if this instruction is a call
            elif instr.mnemonic == "call":
                # Add the next instruction as a block start
                next_addr = instr.address + len(instr.bytes_data)
                block_starts.add(next_addr)

            # Check if this instruction is a return
            elif instr.mnemonic in ["ret", "retf", "retn", "iret"]:
                # Add the next instruction as a block start
                next_addr = instr.address + len(instr.bytes_data)
                block_starts.add(next_addr)

        # Create blocks for all identified block starts
        for addr in sorted(block_starts):
            if addr not in self.blocks:
                self.blocks[addr] = BasicBlock(addr)

        # Second pass: assign instructions to blocks
        current_block = self.entry_block

        for instr in sorted(self.function.instructions, key=lambda i: i.address):
            # Check if this instruction starts a new block
            if (
                instr.address in self.blocks
                and instr.address != current_block.start_address
            ):
                current_block = self.blocks[instr.address]

            # Add the instruction to the current block
            current_block.add_instruction(instr)

            # Check if this instruction ends the current block
            if instr.mnemonic.startswith("j"):
                # Add the target address as a successor
                try:
                    target = int(instr.operands, 16)
                    current_block.add_successor(target)
                except ValueError:
                    pass

                # Add the next instruction as a successor (except for unconditional jumps)
                if instr.mnemonic != "jmp":
                    next_addr = instr.address + len(instr.bytes_data)
                    current_block.add_successor(next_addr)

                # Start a new block
                next_addr = instr.address + len(instr.bytes_data)
                if next_addr in self.blocks:
                    current_block = self.blocks[next_addr]

            # Check if this instruction is a call
            elif instr.mnemonic == "call":
                # Add the next instruction as a successor
                next_addr = instr.address + len(instr.bytes_data)
                current_block.add_successor(next_addr)

                # Start a new block
                if next_addr in self.blocks:
                    current_block = self.blocks[next_addr]

            # Check if this instruction is a return
            elif instr.mnemonic in ["ret", "retf", "retn", "iret"]:
                # No successors for return instructions

                # Start a new block
                next_addr = instr.address + len(instr.bytes_data)
                if next_addr in self.blocks:
                    current_block = self.blocks[next_addr]


class Variable:
    """Represents a variable in the decompiled code"""

    def __init__(
        self, name: str, address: Optional[int] = None, register: Optional[str] = None
    ):
        self.name = name
        self.address = address
        self.register = register
        self.type = "int"  # Default type
        self.size = 2  # Default size (16-bit)
        self.references: List[
            int
        ] = []  # Instruction addresses that reference this variable
        self.is_array = False  # Whether this variable is an array
        self.is_struct = False  # Whether this variable is a struct
        self.array_length = 0  # Length of the array (if is_array is True)
        self.struct_name = ""  # Name of the struct (if is_struct is True)
        self.is_parameter = False  # Whether this variable is a function parameter
        self.parameter_index = -1  # Index of the parameter (if is_parameter is True)
        self.is_return_value = False  # Whether this variable is a return value
        self.usage_pattern = (
            ""  # Usage pattern of the variable (e.g., "counter", "flag", etc.)
        )
        self.description = ""  # Description of the variable

    def __str__(self):
        if self.address is not None:
            base = f"Variable {self.name}: memory[0x{self.address:X}], type={self.type}, size={self.size}"
        else:
            base = f"Variable {self.name}: register {self.register}, type={self.type}, size={self.size}"

        if self.is_array:
            base += f", array[{self.array_length}]"
        if self.is_struct:
            base += f", struct {self.struct_name}"
        if self.is_parameter:
            base += f", parameter {self.parameter_index}"
        if self.is_return_value:
            base += ", return value"
        if self.usage_pattern:
            base += f", usage: {self.usage_pattern}"

        return base


class DOSFunction:
    """Represents a function in the DOS executable"""

    def __init__(self, name: str, start_address: int, end_address: int = 0):
        self.name = name
        self.start_address = start_address
        self.end_address = end_address
        self.instructions: List[X86Instruction] = []
        self.calls: List[int] = []  # Addresses of functions called by this function
        self.cfg = None  # Control flow graph
        self.variables = {}  # Variables used in this function
        self.parameters = []  # Parameters of the function
        self.return_type = None  # Return type of the function
        self.return_register = None  # Register used for return value
        self.signature = None  # Function signature (e.g., "void func(int, char*)")
        self.purpose = None  # Purpose of the function
        self.struct_defs = {}  # Struct definitions used in this function
        self.array_defs = {}  # Array definitions used in this function
        self.local_variables = []  # Local variables of the function
        self.is_recursive = False  # Whether this function calls itself
        self.is_leaf = False  # Whether this function doesn't call any other functions
        self.is_library = False  # Whether this function is a library function
        self.is_interrupt_handler = (
            False  # Whether this function is an interrupt handler
        )
        self.is_entry_point = False  # Whether this function is an entry point
        self.is_exit_point = False  # Whether this function is an exit point
        self.complexity = 0  # Cyclomatic complexity of the function

    def __str__(self) -> str:
        if self.signature:
            return f"Function {self.signature}: {self.start_address:08X} - {self.end_address:08X}"
        else:
            return f"Function {self.name}: {self.start_address:08X} - {self.end_address:08X}"

    def build_cfg(self):
        """Build the control flow graph for this function"""
        self.cfg = ControlFlowGraph(self)
        self.cfg.build()
        return self.cfg

    def calculate_complexity(self):
        """Calculate the cyclomatic complexity of the function"""
        if not self.cfg:
            return 0

        # Complexity = E - N + 2, where E is the number of edges and N is the number of nodes
        edges = sum(len(block.successors) for block in self.cfg.blocks.values())
        nodes = len(self.cfg.blocks)

        self.complexity = edges - nodes + 2
        return self.complexity
