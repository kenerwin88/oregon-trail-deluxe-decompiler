#!/usr/bin/env python3
"""
Basic DOS Executable Decompiler for OREGON.EXE
"""

import struct
import os
import argparse
from typing import Dict, List, Set
from capstone import Cs, CS_ARCH_X86, CS_MODE_16
import networkx as nx
import matplotlib.pyplot as plt


class X86Instruction:
    """Represents a disassembled x86 instruction"""

    def __init__(
        self, address: int, bytes_data: bytes, mnemonic: str, operands: str = ""
    ):
        self.address = address
        self.bytes_data = bytes_data
        self.mnemonic = mnemonic
        self.operands = operands

    def __str__(self) -> str:
        bytes_str = " ".join(f"{b:02X}" for b in self.bytes_data)
        return f"{self.address:08X}: {bytes_str:<12} {self.mnemonic} {self.operands}"


class DOSSegment:
    """Represents a segment in the DOS executable"""

    def __init__(
        self, name: str, start_offset: int, size: int, segment_type: str = "CODE"
    ):
        self.name = name
        self.start_offset = start_offset
        self.size = size
        self.type = segment_type  # CODE, DATA, STACK, etc.
        self.data = bytes()
        self.instructions: List[X86Instruction] = []

    def load_data(self, data: bytes):
        """Load segment data"""
        self.data = data

    def __str__(self) -> str:
        return f"Segment {self.name}: offset={self.start_offset:08X}, size={self.size:X}, type={self.type}"


class BasicBlock:
    """Represents a basic block of instructions with a single entry and exit point"""

    def __init__(self, start_address: int):
        self.start_address = start_address
        self.end_address = 0
        self.instructions = []
        self.successors = []  # Addresses of blocks that may follow this one
        self.predecessors = []  # Addresses of blocks that may lead to this one
        self.successors = []  # Addresses of blocks that may follow this one
        self.predecessors = []  # Addresses of blocks that may lead to this one

    def add_instruction(self, instruction):
        """Add an instruction to this block"""
        self.instructions.append(instruction)
        self.end_address = instruction.address

    def is_conditional_branch(self):
        """Check if this block ends with a conditional branch"""
        if not self.instructions:
            return False
        last_instr = self.instructions[-1]
        return last_instr.mnemonic in [
            "je",
            "jne",
            "jz",
            "jnz",
            "jg",
            "jge",
            "jl",
            "jle",
            "ja",
            "jae",
            "jb",
            "jbe",
        ]

    def is_unconditional_jump(self):
        """Check if this block ends with an unconditional jump"""
        if not self.instructions:
            return False
        last_instr = self.instructions[-1]
        return last_instr.mnemonic in ["jmp", "jmpf"]

    def is_function_return(self):
        """Check if this block ends with a return instruction"""
        if not self.instructions:
            return False
        last_instr = self.instructions[-1]
        return last_instr.mnemonic in ["ret", "retf", "iret"]

    def __str__(self):
        return f"Block 0x{self.start_address:X} - 0x{self.end_address:X}"


class ControlFlowGraph:
    """Represents the control flow graph of a function"""

    def __init__(self, function):
        self.function = function
        self.blocks = {}  # Map from start address to BasicBlock
        self.entry_block = None
        self.exit_blocks = []

    def build(self):
        """Build the control flow graph from function instructions"""
        if not self.function.instructions:
            return

        # Identify block boundaries
        boundaries = set([self.function.start_address])

        # Add targets of jumps and calls as boundaries
        for instr in self.function.instructions:
            # Current instruction is a boundary
            boundaries.add(instr.address)

            # Target of jump/call is a boundary
            if instr.mnemonic.startswith("j") or instr.mnemonic == "call":
                try:
                    target = int(instr.operands, 16)
                    boundaries.add(target)
                except ValueError:
                    pass

            # Instruction after jump is a boundary
            if instr.mnemonic.startswith("j"):
                next_addr = instr.address + len(instr.bytes_data)
                boundaries.add(next_addr)

        # Sort boundaries
        sorted_boundaries = sorted(boundaries)

        # Create basic blocks
        current_block = None
        for instr in sorted(self.function.instructions, key=lambda i: i.address):
            if instr.address in boundaries:
                # Start a new block
                current_block = BasicBlock(instr.address)
                self.blocks[instr.address] = current_block

                # Set entry block
                if instr.address == self.function.start_address:
                    self.entry_block = current_block

            # Add instruction to current block
            if current_block:
                current_block.add_instruction(instr)

            # Check if this instruction ends a block
            if instr.mnemonic.startswith("j") or instr.mnemonic in [
                "ret",
                "retf",
                "iret",
            ]:
                boundaries.add(instr.address + len(instr.bytes_data))

        # Connect blocks
        for addr, block in self.blocks.items():
            if not block.instructions:
                continue

            last_instr = block.instructions[-1]
            next_addr = last_instr.address + len(last_instr.bytes_data)

            if block.is_conditional_branch():
                # Add both branch targets
                try:
                    target = int(last_instr.operands, 16)
                    if target in self.blocks:
                        block.successors.append(target)
                        self.blocks[target].predecessors.append(block.start_address)
                except ValueError:
                    pass

                # Add fall-through
                if next_addr in self.blocks:
                    block.successors.append(next_addr)
                    self.blocks[next_addr].predecessors.append(block.start_address)

            elif block.is_unconditional_jump():
                # Add jump target
                try:
                    target = int(last_instr.operands, 16)
                    if target in self.blocks:
                        block.successors.append(target)
                        self.blocks[target].predecessors.append(block.start_address)
                except ValueError:
                    pass
            elif not block.is_function_return():
                # Add fall-through for non-returns
                if next_addr in self.blocks:
                    block.successors.append(next_addr)
                    self.blocks[next_addr].predecessors.append(block.start_address)
            else:
                # This is a return block
                self.exit_blocks.append(block)

    def to_networkx(self):
        """Convert to a NetworkX graph for visualization and analysis"""
        G = nx.DiGraph()

        # Add nodes
        for addr, block in self.blocks.items():
            label = f"0x{addr:X}"
            if block == self.entry_block:
                label = f"ENTRY: {label}"
            if block in self.exit_blocks:
                label = f"EXIT: {label}"
            G.add_node(addr, label=label)

        # Add edges
        for addr, block in self.blocks.items():
            for succ in block.successors:
                G.add_edge(addr, succ)

        return G

    def visualize(self, output_file=None):
        """Visualize the control flow graph"""
        G = self.to_networkx()
        pos = nx.spring_layout(G)
        labels = nx.get_node_attributes(G, "label")

        plt.figure(figsize=(12, 8))
        nx.draw(
            G,
            pos,
            with_labels=False,
            node_size=700,
            node_color="lightblue",
            font_weight="bold",
        )
        nx.draw_networkx_labels(G, pos, labels=labels)

        if output_file:
            plt.savefig(output_file)
        else:
            plt.show()


class RegisterState:
    """Represents the state of CPU registers at a specific point"""

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
        self.memory = {}  # Address -> Value mapping

    def copy(self):
        """Create a copy of the current state"""
        new_state = RegisterState()
        new_state.registers = self.registers.copy()
        new_state.memory = self.memory.copy()
        return new_state

    def update_register(self, reg, value):
        """Update a register with a new value"""
        # Handle 8-bit registers
        if reg in ["al", "ah", "bl", "bh", "cl", "ch", "dl", "dh"]:
            parent = reg[0] + "x"  # Convert to 16-bit register name
            if reg[1] == "l":  # Low byte
                # Preserve high byte if it exists
                if self.registers[parent] is not None:
                    high_byte = (self.registers[parent] >> 8) & 0xFF
                    self.registers[parent] = (high_byte << 8) | (value & 0xFF)
                else:
                    self.registers[parent] = value & 0xFF
            else:  # High byte
                # Preserve low byte if it exists
                if self.registers[parent] is not None:
                    low_byte = self.registers[parent] & 0xFF
                    self.registers[parent] = ((value & 0xFF) << 8) | low_byte
                else:
                    self.registers[parent] = (value & 0xFF) << 8
        else:
            # 16-bit register
            self.registers[reg] = value

    def get_register(self, reg):
        """Get the value of a register"""
        # Handle 8-bit registers
        if reg in ["al", "ah", "bl", "bh", "cl", "ch", "dl", "dh"]:
            parent = reg[0] + "x"  # Convert to 16-bit register name
            if self.registers[parent] is None:
                return None

            if reg[1] == "l":  # Low byte
                return self.registers[parent] & 0xFF
            else:  # High byte
                return (self.registers[parent] >> 8) & 0xFF
        else:
            # 16-bit register
            return self.registers[reg]

    def update_memory(self, address, value, size=2):
        """Update memory at the specified address"""
        if size == 1:
            self.memory[address] = value & 0xFF
        else:
            self.memory[address] = value & 0xFFFF

    def get_memory(self, address, size=2):
        """Get memory value at the specified address"""
        if address not in self.memory:
            return None

        return self.memory[address]


class Variable:
    """Represents a variable in the program"""

    def __init__(self, name, address=None, register=None, size=2, var_type="int"):
        self.name = name
        self.address = address  # Memory address or None for register variables
        self.register = register  # Register name or None for memory variables
        self.size = size  # 1 for byte, 2 for word
        self.type = var_type  # "int", "char", "pointer", etc.
        self.values = []  # List of values assigned to this variable
        self.references = []  # Instructions that reference this variable

    def __str__(self):
        if self.address is not None:
            return f"Variable {self.name}: memory[0x{self.address:X}], type={self.type}, size={self.size}"
        else:
            return f"Variable {self.name}: register {self.register}, type={self.type}, size={self.size}"


class DataFlowAnalyzer:
    """Analyzes data flow in a function"""

    def __init__(self, function):
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

    def _analyze_block(self, block, input_state, visited):
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

    def _process_instruction(self, instr, state):
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

        # Create variables for memory locations
        for mem_addr, accesses in memory_accesses.items():
            var_name = f"var_{mem_addr:X}"
            var = Variable(var_name, address=mem_addr)
            var.references = accesses

            # Determine variable type based on usage patterns (simplified)
            # In a real implementation, you'd analyze the instructions that use this memory
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

    def __str__(self) -> str:
        return (
            f"Function {self.name}: {self.start_address:08X} - {self.end_address:08X}"
        )

    def build_cfg(self):
        """Build the control flow graph for this function"""
        self.cfg = ControlFlowGraph(self)
        self.cfg.build()
        return self.cfg


class DOSDecompiler:
    """Basic decompiler for DOS executables"""

    def __init__(self, filename: str):
        self.filename = filename
        self.file_size = 0
        self.header = {}
        self.segments: List[DOSSegment] = []
        self.functions: List[DOSFunction] = []
        self.strings: Dict[int, str] = {}
        self.entry_point = 0

    def parse_header(self) -> Dict:
        """Parse the MZ header of the DOS executable"""
        with open(self.filename, "rb") as f:
            header_data = f.read(28)  # Standard MZ header size

            if header_data[:2] != b"MZ":
                raise ValueError(f"Not a valid DOS executable: {self.filename}")

            # Parse header fields
            self.header = {
                "signature": header_data[:2],
                "last_page_size": struct.unpack("<H", header_data[2:4])[0],
                "pages_in_file": struct.unpack("<H", header_data[4:6])[0],
                "relocations": struct.unpack("<H", header_data[6:8])[0],
                "header_size_paragraphs": struct.unpack("<H", header_data[8:10])[0],
                "min_extra_paragraphs": struct.unpack("<H", header_data[10:12])[0],
                "max_extra_paragraphs": struct.unpack("<H", header_data[12:14])[0],
                "ss": struct.unpack("<H", header_data[14:16])[0],
                "sp": struct.unpack("<H", header_data[16:18])[0],
                "checksum": struct.unpack("<H", header_data[18:20])[0],
                "ip": struct.unpack("<H", header_data[20:22])[0],
                "cs": struct.unpack("<H", header_data[22:24])[0],
                "reloc_table_offset": struct.unpack("<H", header_data[24:26])[0],
                "overlay_number": struct.unpack("<H", header_data[26:28])[0],
            }

            # Calculate file size
            f.seek(0, os.SEEK_END)
            self.file_size = f.tell()

            # Calculate entry point
            self.entry_point = (self.header["cs"] << 4) + self.header["ip"]

            return self.header

    def extract_segments(self):
        """Extract segments from the executable"""
        # Calculate header size in bytes
        header_size = self.header["header_size_paragraphs"] * 16

        # Create a CODE segment starting at the entry point
        code_segment = DOSSegment("CODE", header_size, self.file_size - header_size)

        # Load segment data
        with open(self.filename, "rb") as f:
            f.seek(header_size)
            code_segment.load_data(f.read(code_segment.size))

        self.segments.append(code_segment)

        # Create a DATA segment (simplified approach)
        # In a real decompiler, you'd need to analyze the code to identify data areas
        data_segment = DOSSegment("DATA", 0, header_size, "DATA")
        with open(self.filename, "rb") as f:
            data_segment.load_data(f.read(header_size))

        self.segments.append(data_segment)

        return self.segments

    def find_strings(self):
        """Find ASCII strings in the executable"""
        for segment in self.segments:
            if segment.type != "CODE":
                continue

            current_string = ""
            start_offset = 0

            for i, byte in enumerate(segment.data):
                if 32 <= byte <= 126:  # Printable ASCII
                    if not current_string:
                        start_offset = i
                    current_string += chr(byte)
                else:
                    if len(current_string) >= 4:  # Minimum string length
                        self.strings[segment.start_offset + start_offset] = (
                            current_string
                        )
                    current_string = ""

        return self.strings

    def identify_functions(self):
        """Identify functions in the code segment"""
        # Start with the entry point
        entry_function = DOSFunction("entry", self.entry_point)
        self.functions.append(entry_function)

        # In a real decompiler, you'd use more sophisticated techniques:
        # - Look for function prologues (PUSH BP, MOV BP, SP)
        # - Follow call instructions
        # - Analyze stack frame setup

        return self.functions

    def disassemble(self):
        """Basic disassembly of code segments"""
        # This is a very simplified disassembler for demonstration
        # In a real implementation, you'd use a library like Capstone

        # Simple opcode map for common instructions
        opcode_map = {
            0x33: ("XOR", 2),
            0x50: ("PUSH AX", 1),
            0x51: ("PUSH CX", 1),
            0x52: ("PUSH DX", 1),
            0x53: ("PUSH BX", 1),
            0x55: ("PUSH BP", 1),
            0x56: ("PUSH SI", 1),
            0x57: ("PUSH DI", 1),
            0x58: ("POP AX", 1),
            0x59: ("POP CX", 1),
            0x5A: ("POP DX", 1),
            0x5B: ("POP BX", 1),
            0x5D: ("POP BP", 1),
            0x5E: ("POP SI", 1),
            0x5F: ("POP DI", 1),
            0x74: ("JE", 2),
            0x75: ("JNE", 2),
            0x89: ("MOV", 2),
            0x8B: ("MOV", 2),
            0x90: ("NOP", 1),
            0xB8: ("MOV AX,", 3),
            0xB9: ("MOV CX,", 3),
            0xBA: ("MOV DX,", 3),
            0xBB: ("MOV BX,", 3),
            0xE8: ("CALL", 3),
            0xE9: ("JMP", 3),
            0xEB: ("JMP SHORT", 2),
            0xC3: ("RET", 1),
            0xCF: ("IRET", 1),
        }

        for segment in self.segments:
            if segment.type != "CODE":
                continue

            offset = 0
            while offset < len(segment.data):
                opcode = segment.data[offset]

                if opcode in opcode_map:
                    mnemonic, size = opcode_map[opcode]

                    # Handle operands for some instructions
                    operands = ""
                    if size > 1 and offset + size <= len(segment.data):
                        if opcode in [0xB8, 0xB9, 0xBA, 0xBB]:  # MOV reg, imm16
                            imm = struct.unpack(
                                "<H", segment.data[offset + 1 : offset + 3]
                            )[0]
                            operands = f"0x{imm:04X}"
                        elif opcode == 0xE8:  # CALL
                            rel = struct.unpack(
                                "<H", segment.data[offset + 1 : offset + 3]
                            )[0]
                            target = (offset + 3 + rel) & 0xFFFF
                            operands = f"0x{target:04X}"

                    instr = X86Instruction(
                        segment.start_offset + offset,
                        segment.data[offset : offset + size],
                        mnemonic,
                        operands,
                    )
                    segment.instructions.append(instr)
                else:
                    # Unknown opcode
                    instr = X86Instruction(
                        segment.start_offset + offset,
                        bytes([opcode]),
                        "DB",
                        f"0x{opcode:02X}",
                    )
                    segment.instructions.append(instr)
                    size = 1

                offset += size

    def generate_pseudocode(self):
        """Generate basic pseudocode from disassembly"""
        # This is a placeholder for a more sophisticated decompilation process
        # Real decompilation would involve:
        # - Control flow analysis
        # - Data flow analysis
        # - Type inference
        # - Variable identification

        pseudocode = []
        pseudocode.append("// Pseudocode for OREGON.EXE")
        pseudocode.append("// This is a very basic representation")
        pseudocode.append("")

        for function in self.functions:
            pseudocode.append(f"function {function.name}() {{")

            # In a real decompiler, you'd analyze the control flow
            # and convert assembly to higher-level constructs

            pseudocode.append("    // Function body would be decompiled here")
            pseudocode.append("}")
            pseudocode.append("")

        return "\n".join(pseudocode)

    def decompile(self):
        """Run the full decompilation process"""
        print(f"Decompiling {self.filename}...")

        # Step 1: Parse the header
        self.parse_header()
        print(f"MZ Header parsed: Entry point at {self.entry_point:08X}")

        # Step 2: Extract segments
        self.extract_segments()
        print(f"Extracted {len(self.segments)} segments")

        # Step 3: Find strings
        self.find_strings()
        print(f"Found {len(self.strings)} strings")

        # Step 4: Identify functions
        self.identify_functions()
        print(f"Identified {len(self.functions)} functions")

        # Step 5: Disassemble
        self.disassemble()
        print("Disassembly completed")

        # Step 6: Generate pseudocode
        pseudocode = self.generate_pseudocode()
        print("Pseudocode generation completed")

        return {
            "header": self.header,
            "segments": self.segments,
            "functions": self.functions,
            "strings": self.strings,
            "pseudocode": pseudocode,
        }

    def save_output(self, output_dir: str, visualize=False):
        """Save decompilation results to files"""
        os.makedirs(output_dir, exist_ok=True)

        # Save header information
        with open(os.path.join(output_dir, "header.txt"), "w") as f:
            f.write("MZ Header Information:\n")
            for key, value in self.header.items():
                f.write(f"{key}: {value}\n")

        # Save disassembly
        with open(os.path.join(output_dir, "disassembly.asm"), "w") as f:
            f.write("; Disassembly of OREGON.EXE\n\n")

            for segment in self.segments:
                if segment.type == "CODE":
                    f.write(f"; {segment}\n")
                    for instr in segment.instructions:
                        f.write(f"{instr}\n")

        # Save strings
        with open(os.path.join(output_dir, "strings.txt"), "w") as f:
            f.write("Strings found in OREGON.EXE:\n\n")
            for addr, string in sorted(self.strings.items()):
                f.write(f'{addr:08X}: "{string}"\n')

        # Save pseudocode
        with open(os.path.join(output_dir, "pseudocode.c"), "w") as f:
            f.write(self.generate_pseudocode())

        # Save control flow graphs if requested
        if visualize:
            cfg_dir = os.path.join(output_dir, "cfg")
            os.makedirs(cfg_dir, exist_ok=True)

            for function in self.functions:
                if function.cfg:
                    output_file = os.path.join(cfg_dir, f"{function.name}.png")
                    function.cfg.visualize(output_file)

        print(f"Output saved to {output_dir}")


class EnhancedDOSDecompiler(DOSDecompiler):
    """Enhanced DOS decompiler with Capstone integration"""

    def decompile(self):
        """Run the full decompilation process with data flow analysis"""
        result = super().decompile()

        # Perform data flow analysis on each function
        print("Performing data flow analysis...")
        for func in self.functions:
            if func.cfg:
                analyzer = DataFlowAnalyzer(func)
                func.variables = analyzer.analyze()
                if func.variables:
                    var_count = len(func.variables)
                    print(f"Identified {var_count} variables in function {func.name}")

        return result

    def disassemble(self):
        """Enhanced disassembly using Capstone"""
        print("Using enhanced Capstone-based disassembler...")

        # Initialize Capstone for 16-bit x86
        md = Cs(CS_ARCH_X86, CS_MODE_16)
        md.detail = True  # Enable detailed output

        for segment in self.segments:
            if segment.type != "CODE":
                continue

            # Track potential functions
            function_starts = set([self.entry_point])

            print(
                f"Disassembling segment {segment.name} at offset 0x{segment.start_offset:X}..."
            )

            # First pass: disassemble and identify function boundaries
            instructions_by_address = {}

            try:
                for i, instruction in enumerate(
                    md.disasm(segment.data, segment.start_offset)
                ):
                    # Create instruction object
                    instr = X86Instruction(
                        instruction.address,
                        segment.data[
                            instruction.address
                            - segment.start_offset : instruction.address
                            - segment.start_offset
                            + instruction.size
                        ],
                        instruction.mnemonic,
                        instruction.op_str,
                    )

                    # Store instruction
                    segment.instructions.append(instr)
                    instructions_by_address[instruction.address] = instr

                    # Look for function prologues (PUSH BP; MOV BP, SP)
                    if instruction.mnemonic == "push" and instruction.op_str == "bp":
                        # Check if next instruction is MOV BP, SP
                        next_addr = instruction.address + instruction.size
                        if i + 1 < len(segment.instructions):
                            next_instr = segment.instructions[i + 1]
                            if (
                                next_instr.mnemonic == "mov"
                                and next_instr.operands.startswith("bp, sp")
                            ):
                                function_starts.add(instruction.address)
                                print(
                                    f"Found function prologue at 0x{instruction.address:X}"
                                )

                    # Look for CALL instructions to identify more functions
                    if instruction.mnemonic == "call":
                        try:
                            # Extract target address from operand
                            target = int(instruction.op_str, 16)
                            function_starts.add(target)
                            print(f"Found function call to 0x{target:X}")
                        except ValueError:
                            # Handle indirect calls
                            pass

                    # Look for INT instructions (system calls)
                    if instruction.mnemonic == "int":
                        print(
                            f"Found interrupt call at 0x{instruction.address:X}: {instruction.op_str}"
                        )

            except Exception as e:
                print(f"Error during disassembly: {str(e)}")
                # Continue with what we have

            # Create function objects
            for start_addr in sorted(function_starts):
                func_name = f"sub_{start_addr:X}"
                if start_addr == self.entry_point:
                    func_name = "entry"

                func = DOSFunction(func_name, start_addr)
                self.functions.append(func)

            # Assign instructions to functions
            self._assign_instructions_to_functions(instructions_by_address)

            # Build control flow graphs for each function
            for func in self.functions:
                func.build_cfg()

    def _assign_instructions_to_functions(self, instructions_by_address=None):
        """Assign disassembled instructions to functions"""
        # Sort functions by address
        sorted_funcs = sorted(self.functions, key=lambda f: f.start_address)

        # Assign end addresses based on next function start
        for i in range(len(sorted_funcs) - 1):
            sorted_funcs[i].end_address = sorted_funcs[i + 1].start_address - 1

        # Assign instructions to functions
        for segment in self.segments:
            if segment.type != "CODE":
                continue

            for instr in segment.instructions:
                for func in self.functions:
                    if func.start_address <= instr.address and (
                        func.end_address == 0 or instr.address <= func.end_address
                    ):
                        func.instructions.append(instr)

                        # Track function calls
                        if instr.mnemonic == "call":
                            try:
                                target = int(instr.operands, 16)
                                func.calls.append(target)
                            except ValueError:
                                pass

                        break

    def generate_pseudocode(self):
        """Generate improved pseudocode with variable information"""
        pseudocode = []
        pseudocode.append(
            "// Enhanced Pseudocode for OREGON.EXE with Control Flow and Data Flow Analysis"
        )
        pseudocode.append("// Generated with Capstone-based disassembler")
        pseudocode.append("")

        # Add forward declarations for all functions
        pseudocode.append("// Function declarations")
        for function in sorted(self.functions, key=lambda f: f.name):
            pseudocode.append(f"void {function.name}();")
        pseudocode.append("")

        # Generate function bodies with control flow and variables
        for function in sorted(self.functions, key=lambda f: f.name):
            pseudocode.append(f"void {function.name}() {{")

            # Add variable declarations if available
            if hasattr(function, "variables") and function.variables:
                pseudocode.append("    // Variable declarations")
                for var_name, var in function.variables.items():
                    if var.type == "int" and var.size == 2:
                        pseudocode.append(f"    int {var_name};")
                    elif var.type == "char" or var.size == 1:
                        pseudocode.append(f"    char {var_name};")
                    else:
                        pseudocode.append(f"    // Unknown type: {var_name}")
                pseudocode.append("")

            if function.instructions:
                # Use control flow graph if available
                if function.cfg and function.cfg.entry_block:
                    pseudocode.extend(
                        self._generate_block_code(
                            function.cfg, function.cfg.entry_block, set(), 1
                        )
                    )
                else:
                    # Fallback to simple instruction listing
                    for instr in function.instructions:
                        pseudocode.append(f"    // {instr.mnemonic} {instr.operands}")

                # Add function calls
                if function.calls:
                    pseudocode.append("")
                    pseudocode.append("    // Function calls:")
                    for call_addr in function.calls:
                        # Find the function name for this address
                        for called_func in self.functions:
                            if called_func.start_address == call_addr:
                                pseudocode.append(f"    {called_func.name}();")
                                break
                        else:
                            pseudocode.append(
                                f"    // Call to unknown function at 0x{call_addr:X}"
                            )
            else:
                pseudocode.append("    // No instructions found for this function")

            pseudocode.append("}")
            pseudocode.append("")

        return "\n".join(pseudocode)

    def _generate_block_code(self, cfg, block, visited: Set[int], indent_level: int):
        """Recursively generate code for a basic block and its successors with variable information"""
        if block.start_address in visited:
            return [
                f"{'    ' * indent_level}// Jump to block at 0x{block.start_address:X}"
            ]

        visited.add(block.start_address)
        lines = []

        # Add block header comment
        lines.append(f"{'    ' * indent_level}// Block 0x{block.start_address:X}")

        # Add instructions with variable references where possible
        for instr in block.instructions[:-1]:  # All but last instruction
            # Try to map memory references to variables (simplified)
            op_with_vars = instr.operands
            if hasattr(cfg.function, "variables") and cfg.function.variables:
                for var_name, var in cfg.function.variables.items():
                    if var.address is not None:
                        # Replace memory references with variable names
                        # Handle different formats of memory references
                        addr_hex = f"0x{var.address:X}"

                        # Check for exact memory address matches
                        if f"[{addr_hex}]" in op_with_vars:
                            # Simple memory reference [0xXXXX]
                            if "word ptr [" in op_with_vars:
                                op_with_vars = op_with_vars.replace(
                                    f"word ptr [{addr_hex}]", f"word ptr {var_name}"
                                )
                            elif "byte ptr [" in op_with_vars:
                                op_with_vars = op_with_vars.replace(
                                    f"byte ptr [{addr_hex}]", f"byte ptr {var_name}"
                                )
                            elif "dword ptr [" in op_with_vars:
                                op_with_vars = op_with_vars.replace(
                                    f"dword ptr [{addr_hex}]", f"dword ptr {var_name}"
                                )
                            else:
                                op_with_vars = op_with_vars.replace(
                                    f"[{addr_hex}]", var_name
                                )

                        # Check for memory address with offset
                        elif f"[{addr_hex} + " in op_with_vars:
                            # Find the offset part
                            parts = op_with_vars.split(f"[{addr_hex} + ")
                            if len(parts) > 1:
                                offset_part = parts[1].split("]")[0]

                                if "word ptr [" in op_with_vars:
                                    op_with_vars = op_with_vars.replace(
                                        f"word ptr [{addr_hex} + {offset_part}]",
                                        f"word ptr {var_name}[{offset_part}]",
                                    )
                                elif "byte ptr [" in op_with_vars:
                                    op_with_vars = op_with_vars.replace(
                                        f"byte ptr [{addr_hex} + {offset_part}]",
                                        f"byte ptr {var_name}[{offset_part}]",
                                    )
                                elif "dword ptr [" in op_with_vars:
                                    op_with_vars = op_with_vars.replace(
                                        f"dword ptr [{addr_hex} + {offset_part}]",
                                        f"dword ptr {var_name}[{offset_part}]",
                                    )
                                else:
                                    op_with_vars = op_with_vars.replace(
                                        f"[{addr_hex} + {offset_part}]",
                                        f"{var_name}[{offset_part}]",
                                    )

            lines.append(f"{'    ' * indent_level}{instr.mnemonic} {op_with_vars};")

        # Handle last instruction based on control flow
        if block.is_conditional_branch():
            # This is an if statement
            last_instr = block.instructions[-1]

            # Try to map memory references to variables in the last instruction
            op_with_vars = last_instr.operands
            if hasattr(cfg.function, "variables") and cfg.function.variables:
                for var_name, var in cfg.function.variables.items():
                    if var.address is not None:
                        # Replace memory references with variable names
                        # Handle different formats of memory references
                        addr_hex = f"0x{var.address:X}"

                        # Check for exact memory address matches
                        if f"[{addr_hex}]" in op_with_vars:
                            # Simple memory reference [0xXXXX]
                            if "word ptr [" in op_with_vars:
                                op_with_vars = op_with_vars.replace(
                                    f"word ptr [{addr_hex}]", f"word ptr {var_name}"
                                )
                            elif "byte ptr [" in op_with_vars:
                                op_with_vars = op_with_vars.replace(
                                    f"byte ptr [{addr_hex}]", f"byte ptr {var_name}"
                                )
                            elif "dword ptr [" in op_with_vars:
                                op_with_vars = op_with_vars.replace(
                                    f"dword ptr [{addr_hex}]", f"dword ptr {var_name}"
                                )
                            else:
                                op_with_vars = op_with_vars.replace(
                                    f"[{addr_hex}]", var_name
                                )

                        # Check for memory address with offset
                        elif f"[{addr_hex} + " in op_with_vars:
                            # Find the offset part
                            parts = op_with_vars.split(f"[{addr_hex} + ")
                            if len(parts) > 1:
                                offset_part = parts[1].split("]")[0]

                                if "word ptr [" in op_with_vars:
                                    op_with_vars = op_with_vars.replace(
                                        f"word ptr [{addr_hex} + {offset_part}]",
                                        f"word ptr {var_name}[{offset_part}]",
                                    )
                                elif "byte ptr [" in op_with_vars:
                                    op_with_vars = op_with_vars.replace(
                                        f"byte ptr [{addr_hex} + {offset_part}]",
                                        f"byte ptr {var_name}[{offset_part}]",
                                    )
                                elif "dword ptr [" in op_with_vars:
                                    op_with_vars = op_with_vars.replace(
                                        f"dword ptr [{addr_hex} + {offset_part}]",
                                        f"dword ptr {var_name}[{offset_part}]",
                                    )
                                else:
                                    op_with_vars = op_with_vars.replace(
                                        f"[{addr_hex} + {offset_part}]",
                                        f"{var_name}[{offset_part}]",
                                    )

            condition = self._translate_condition(last_instr.mnemonic)
            lines.append(
                f"{'    ' * indent_level}if ({condition}) {{  // {last_instr.mnemonic} {op_with_vars}"
            )

            # True branch
            try:
                target = int(last_instr.operands, 16)
                if target in cfg.blocks:
                    true_block = cfg.blocks[target]
                    lines.extend(
                        self._generate_block_code(
                            cfg, true_block, visited.copy(), indent_level + 1
                        )
                    )
            except ValueError:
                pass

            lines.append(f"{'    ' * indent_level}}} else {{")

            # False branch (fall-through)
            next_addr = last_instr.address + len(last_instr.bytes_data)
            if next_addr in cfg.blocks:
                false_block = cfg.blocks[next_addr]
                lines.extend(
                    self._generate_block_code(
                        cfg, false_block, visited.copy(), indent_level + 1
                    )
                )

            lines.append(f"{'    ' * indent_level}}}")

        elif block.is_unconditional_jump():
            # This is a goto
            last_instr = block.instructions[-1]

            # Try to map memory references to variables in the last instruction
            op_with_vars = last_instr.operands
            if hasattr(cfg.function, "variables") and cfg.function.variables:
                for var_name, var in cfg.function.variables.items():
                    if var.address is not None:
                        # Replace memory references with variable names
                        addr_hex = f"0x{var.address:X}"
                        patterns = [
                            f"[{addr_hex}]",  # [0xXXXX]
                            f"word ptr [{addr_hex}]",  # word ptr [0xXXXX]
                            f"byte ptr [{addr_hex}]",  # byte ptr [0xXXXX]
                            f"dword ptr [{addr_hex}]",  # dword ptr [0xXXXX]
                            f"[{addr_hex} + ",  # [0xXXXX + ...
                            f"word ptr [{addr_hex} + ",  # word ptr [0xXXXX + ...
                            f"byte ptr [{addr_hex} + ",  # byte ptr [0xXXXX + ...
                            f"dword ptr [{addr_hex} + ",  # dword ptr [0xXXXX + ...
                        ]

                        for pattern in patterns:
                            if pattern in op_with_vars:
                                if "ptr" in pattern:
                                    # Preserve the ptr type
                                    ptr_type = pattern.split()[0] + " ptr "
                                    if "+" in pattern:
                                        # Handle offsets: replace [0xXXXX + with [var_name +
                                        op_with_vars = op_with_vars.replace(
                                            pattern, f"{ptr_type}[{var_name} + "
                                        )
                                    else:
                                        # Simple replacement
                                        op_with_vars = op_with_vars.replace(
                                            pattern, f"{ptr_type}{var_name}"
                                        )
                                else:
                                    if "+" in pattern:
                                        # Handle offsets without ptr type
                                        op_with_vars = op_with_vars.replace(
                                            pattern, f"[{var_name} + "
                                        )
                                    else:
                                        # Simple replacement without ptr type
                                        op_with_vars = op_with_vars.replace(
                                            pattern, var_name
                                        )

            lines.append(
                f"{'    ' * indent_level}{last_instr.mnemonic} {op_with_vars};"
            )

            # Follow the jump
            try:
                target = int(last_instr.operands, 16)
                if target in cfg.blocks and target not in visited:
                    target_block = cfg.blocks[target]
                    lines.extend(
                        self._generate_block_code(
                            cfg, target_block, visited, indent_level
                        )
                    )
            except ValueError:
                pass

        elif block.is_function_return():
            # This is a return
            last_instr = block.instructions[-1]

            # Try to map memory references to variables in the last instruction
            op_with_vars = last_instr.operands
            if hasattr(cfg.function, "variables") and cfg.function.variables:
                for var_name, var in cfg.function.variables.items():
                    if var.address is not None:
                        # Replace memory references with variable names
                        addr_hex = f"0x{var.address:X}"
                        patterns = [
                            f"[{addr_hex}]",  # [0xXXXX]
                            f"word ptr [{addr_hex}]",  # word ptr [0xXXXX]
                            f"byte ptr [{addr_hex}]",  # byte ptr [0xXXXX]
                            f"dword ptr [{addr_hex}]",  # dword ptr [0xXXXX]
                            f"[{addr_hex} + ",  # [0xXXXX + ...
                            f"word ptr [{addr_hex} + ",  # word ptr [0xXXXX + ...
                            f"byte ptr [{addr_hex} + ",  # byte ptr [0xXXXX + ...
                            f"dword ptr [{addr_hex} + ",  # dword ptr [0xXXXX + ...
                        ]

                        for pattern in patterns:
                            if pattern in op_with_vars:
                                if "ptr" in pattern:
                                    # Preserve the ptr type
                                    ptr_type = pattern.split()[0] + " ptr "
                                    if "+" in pattern:
                                        # Handle offsets: replace [0xXXXX + with [var_name +
                                        op_with_vars = op_with_vars.replace(
                                            pattern, f"{ptr_type}[{var_name} + "
                                        )
                                    else:
                                        # Simple replacement
                                        op_with_vars = op_with_vars.replace(
                                            pattern, f"{ptr_type}{var_name}"
                                        )
                                else:
                                    if "+" in pattern:
                                        # Handle offsets without ptr type
                                        op_with_vars = op_with_vars.replace(
                                            pattern, f"[{var_name} + "
                                        )
                                    else:
                                        # Simple replacement without ptr type
                                        op_with_vars = op_with_vars.replace(
                                            pattern, var_name
                                        )

            lines.append(
                f"{'    ' * indent_level}return;  // {last_instr.mnemonic} {op_with_vars}"
            )

        else:
            # Regular instruction with fall-through
            if block.instructions:
                last_instr = block.instructions[-1]

                # Try to map memory references to variables in the last instruction
                op_with_vars = last_instr.operands
                if hasattr(cfg.function, "variables") and cfg.function.variables:
                    for var_name, var in cfg.function.variables.items():
                        if var.address is not None:
                            # Replace memory references with variable names
                            addr_hex = f"0x{var.address:X}"
                            patterns = [
                                f"[{addr_hex}]",  # [0xXXXX]
                                f"word ptr [{addr_hex}]",  # word ptr [0xXXXX]
                                f"byte ptr [{addr_hex}]",  # byte ptr [0xXXXX]
                                f"dword ptr [{addr_hex}]",  # dword ptr [0xXXXX]
                                f"[{addr_hex} + ",  # [0xXXXX + ...
                                f"word ptr [{addr_hex} + ",  # word ptr [0xXXXX + ...
                                f"byte ptr [{addr_hex} + ",  # byte ptr [0xXXXX + ...
                                f"dword ptr [{addr_hex} + ",  # dword ptr [0xXXXX + ...
                            ]

                            for pattern in patterns:
                                if pattern in op_with_vars:
                                    if "ptr" in pattern:
                                        # Preserve the ptr type
                                        ptr_type = pattern.split()[0] + " ptr "
                                        if "+" in pattern:
                                            # Handle offsets: replace [0xXXXX + with [var_name +
                                            op_with_vars = op_with_vars.replace(
                                                pattern, f"{ptr_type}[{var_name} + "
                                            )
                                        else:
                                            # Simple replacement
                                            op_with_vars = op_with_vars.replace(
                                                pattern, f"{ptr_type}{var_name}"
                                            )
                                    else:
                                        if "+" in pattern:
                                            # Handle offsets without ptr type
                                            op_with_vars = op_with_vars.replace(
                                                pattern, f"[{var_name} + "
                                            )
                                        else:
                                            # Simple replacement without ptr type
                                            op_with_vars = op_with_vars.replace(
                                                pattern, var_name
                                            )

                lines.append(
                    f"{'    ' * indent_level}{last_instr.mnemonic} {op_with_vars};"
                )

            # Follow fall-through
            if block.successors:
                next_block = cfg.blocks.get(block.successors[0])
                if next_block and next_block.start_address not in visited:
                    lines.extend(
                        self._generate_block_code(
                            cfg, next_block, visited, indent_level
                        )
                    )

        return lines

    def _translate_condition(self, mnemonic):
        """Translate jump mnemonic to a C-like condition"""
        translations = {
            "je": "a == b",
            "jne": "a != b",
            "jz": "a == 0",
            "jnz": "a != 0",
            "jg": "a > b",
            "jge": "a >= b",
            "jl": "a < b",
            "jle": "a <= b",
            "ja": "a > b (unsigned)",
            "jae": "a >= b (unsigned)",
            "jb": "a < b (unsigned)",
            "jbe": "a <= b (unsigned)",
        }
        return translations.get(mnemonic, f"condition_{mnemonic}")


def main():
    parser = argparse.ArgumentParser(description="DOS Executable Decompiler")
    parser.add_argument("file", help="DOS executable file to decompile")
    parser.add_argument("--output", "-o", default="decompiled", help="Output directory")
    parser.add_argument(
        "--enhanced",
        "-e",
        action="store_true",
        help="Use enhanced Capstone-based disassembler",
    )
    parser.add_argument(
        "--visualize",
        "-v",
        action="store_true",
        help="Generate control flow graph visualizations",
    )
    parser.add_argument(
        "--data-flow", "-d", action="store_true", help="Perform data flow analysis"
    )
    args = parser.parse_args()

    if args.enhanced:
        print("Using enhanced Capstone-based disassembler")
        decompiler = EnhancedDOSDecompiler(args.file)
    else:
        decompiler = DOSDecompiler(args.file)

    decompiler.decompile()
    decompiler.save_output(args.output, args.visualize)


if __name__ == "__main__":
    main()
