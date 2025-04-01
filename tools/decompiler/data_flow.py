"""
Data flow analysis for the DOS decompiler.
"""

from typing import Set, Optional
from .models import DOSFunction, Variable, X86Instruction


class RegisterState:
    """Represents the state of registers at a specific point in the program"""

    def __init__(self):
        self.registers = {
            "ax": None,
            "bx": None,
            "cx": None,
            "dx": None,
            "si": None,
            "di": None,
            "bp": None,
            "sp": None,
            "cs": None,
            "ds": None,
            "es": None,
            "ss": None,
            "flags": None,
        }
        self.memory = {}  # Address -> Value

    def update_register(self, reg: str, value: int):
        """Update a register value"""
        if reg in self.registers:
            self.registers[reg] = value

    def get_register(self, reg: str) -> Optional[int]:
        """Get a register value"""
        return self.registers.get(reg)

    def update_memory(self, address: int, value: int):
        """Update a memory location"""
        self.memory[address] = value

    def get_memory(self, address: int) -> Optional[int]:
        """Get a memory value"""
        return self.memory.get(address)

    def copy(self):
        """Create a copy of this register state"""
        new_state = RegisterState()
        new_state.registers = self.registers.copy()
        new_state.memory = self.memory.copy()
        return new_state


class DataFlowAnalyzer:
    """Analyzes data flow in a function"""

    def __init__(self, function: DOSFunction):
        self.function = function
        self.variables = {}  # name -> Variable
        self.register_states = {}  # instruction address -> RegisterState
        self.initial_state = RegisterState()

    def analyze(self):
        """Perform data flow analysis on the function"""
        if not self.function.cfg or not self.function.cfg.entry_block:
            return {}

        # Start with the entry block
        self._analyze_block(self.function.cfg.entry_block, self.initial_state, set())

        # Identify variables
        self._identify_variables()

        return self.variables

    def _analyze_block(self, block, input_state, visited: Set[int]):
        """Analyze data flow in a basic block"""
        if block.start_address in visited:
            return

        visited.add(block.start_address)
        current_state = input_state.copy()

        # Process each instruction in the block
        for instr in block.instructions:
            self.register_states[instr.address] = current_state.copy()
            self._process_instruction(instr, current_state)

        # Process successors
        for succ_addr in block.successors:
            if succ_addr in self.function.cfg.blocks:
                succ_block = self.function.cfg.blocks[succ_addr]
                self._analyze_block(succ_block, current_state.copy(), visited.copy())

    def _process_instruction(self, instr: X86Instruction, state: RegisterState):
        """Process a single instruction and update register state"""
        # This is a simplified version - a real implementation would handle all instructions
        mnemonic = instr.mnemonic
        operands = instr.operands

        if mnemonic == "mov":
            # Parse operands (simplified)
            parts = operands.split(",")
            if len(parts) == 2:
                dest = parts[0].strip()
                src = parts[1].strip()

                # Handle immediate values
                if src.startswith("0x"):
                    try:
                        value = int(src, 16)
                        if dest in state.registers:
                            state.update_register(dest, value)
                        else:
                            # Memory destination (simplified)
                            if "ptr [" in dest:
                                # Extract address from memory reference
                                addr_str = dest.split("[")[1].split("]")[0].strip()
                                if addr_str.isdigit() or addr_str.startswith("0x"):
                                    addr = int(addr_str, 0)
                                    state.update_memory(addr, value)
                    except ValueError:
                        pass

                # Handle register-to-register moves
                elif src in state.registers:
                    value = state.get_register(src)
                    if value is not None:
                        if dest in state.registers:
                            state.update_register(dest, value)
                        else:
                            # Memory destination (simplified)
                            if "ptr [" in dest:
                                # Extract address from memory reference
                                addr_str = dest.split("[")[1].split("]")[0].strip()
                                if addr_str.isdigit() or addr_str.startswith("0x"):
                                    try:
                                        addr = int(addr_str, 0)
                                        state.update_memory(addr, value)
                                    except ValueError:
                                        pass

        elif mnemonic == "xor":
            # Handle XOR operation (simplified)
            parts = operands.split(",")
            if len(parts) == 2:
                dest = parts[0].strip()
                src = parts[1].strip()

                if dest == src and dest in state.registers:
                    # XOR with self = zero
                    state.update_register(dest, 0)

        # Add more instruction handlers here...

    def _identify_variables(self):
        """Identify variables based on register and memory usage"""
        # Identify memory variables
        memory_accesses = {}

        # Collect memory accesses from register states
        for addr, state in self.register_states.items():
            for mem_addr in state.memory:
                if mem_addr not in memory_accesses:
                    memory_accesses[mem_addr] = []
                memory_accesses[mem_addr].append(addr)

        # Find instructions that reference each memory address
        memory_instructions = {}
        for mem_addr in memory_accesses:
            memory_instructions[mem_addr] = []

            for instr in self.function.instructions:
                # Check if the instruction references this memory address
                addr_hex = f"0x{mem_addr:X}"
                if addr_hex in instr.operands:
                    memory_instructions[mem_addr].append(instr)

        # Create variables for memory locations
        for mem_addr, accesses in memory_accesses.items():
            var_name = f"var_{mem_addr:X}"
            var = Variable(var_name, address=mem_addr)
            var.references = accesses

            # Determine variable type based on usage patterns
            if mem_addr in memory_instructions and memory_instructions[mem_addr]:
                var_type, var_size = self._infer_variable_type(
                    mem_addr, memory_instructions[mem_addr]
                )
                var.type = var_type
                var.size = var_size
            else:
                # Default type based on address alignment
                if mem_addr % 2 == 0:  # Even addresses are likely word-sized
                    var.type = "int"
                    var.size = 2
                else:  # Odd addresses are likely byte-sized
                    var.type = "char"
                    var.size = 1

            self.variables[var_name] = var

        # Identify register variables (simplified)
        # In a real implementation, you'd track register lifetimes and usage patterns
        for reg in ["ax", "bx", "cx", "dx", "si", "di", "bp"]:
            var_name = f"reg_{reg}"
            var = Variable(var_name, register=reg)
            var.type = "int"  # Most registers are 16-bit in 16-bit x86
            var.size = 2
            self.variables[var_name] = var

        # Add special variables for common memory locations in DOS programs
        # This is a simplified approach - in a real implementation, you'd identify these
        # based on usage patterns and DOS API calls

        # Common DOS memory locations
        dos_variables = {
            0x80: ("cmd_line_len", "char", 1),
            0x81: ("cmd_line", "char[]", 127),
            0x5C: ("fcb1", "struct", 16),
            0x6C: ("fcb2", "struct", 16),
            0x2C: ("env_segment", "int", 2),
        }

        for addr, (name, type_, size) in dos_variables.items():
            if addr not in memory_accesses:  # Only add if not already identified
                var_name = f"dos_{name}"
                var = Variable(var_name, address=addr)
                var.type = type_
                var.size = size
                self.variables[var_name] = var

    def _infer_variable_type(self, mem_addr, instructions):
        """Infer the type of a variable based on its usage"""
        # Default type and size
        var_type = "int"
        var_size = 2

        # Check if the variable is used with byte ptr, word ptr, or dword ptr
        for instr in instructions:
            addr_hex = f"0x{mem_addr:X}"

            if "byte ptr" in instr.operands and addr_hex in instr.operands:
                var_type = "char"
                var_size = 1
                break
            elif "word ptr" in instr.operands and addr_hex in instr.operands:
                var_type = "int"
                var_size = 2
                break
            elif "dword ptr" in instr.operands and addr_hex in instr.operands:
                var_type = "long"
                var_size = 4
                break

        # Check if the variable is used in string operations
        for instr in instructions:
            if instr.mnemonic in [
                "movsb",
                "movsw",
                "movsd",
                "stosb",
                "stosw",
                "stosd",
                "lodsb",
                "lodsw",
                "lodsd",
            ]:
                addr_hex = f"0x{mem_addr:X}"
                if addr_hex in instr.operands:
                    if instr.mnemonic in ["movsb", "stosb", "lodsb"]:
                        var_type = "char[]"
                        var_size = 1
                    elif instr.mnemonic in ["movsw", "stosw", "lodsw"]:
                        var_type = "int[]"
                        var_size = 2
                    elif instr.mnemonic in ["movsd", "stosd", "lodsd"]:
                        var_type = "long[]"
                        var_size = 4
                    break

        # Check if the variable is used in array-like operations
        array_access = False
        for instr in instructions:
            addr_hex = f"0x{mem_addr:X}"
            if addr_hex in instr.operands and "+" in instr.operands:
                array_access = True
                break

        if array_access:
            if var_type == "char":
                var_type = "char[]"
            elif var_type == "int":
                var_type = "int[]"
            elif var_type == "long":
                var_type = "long[]"

        return var_type, var_size
