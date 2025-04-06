"""
Basic disassembler for DOS executables.
"""

import os
import struct
from typing import List, Dict
import re

from .models import DOSSegment, DOSFunction, X86Instruction


class DOSDecompiler:
    """Basic DOS executable decompiler"""

    def __init__(self, filename: str):
        self.filename = filename
        self.file_size = os.path.getsize(filename)
        self.segments: List[DOSSegment] = []
        self.functions: List[DOSFunction] = []
        self.strings: Dict[int, str] = {}
        self.entry_point = 0

    def decompile(self):
        """Run the full decompilation process"""
        self.parse_header()
        self.extract_segments()
        self.find_strings()
        self.disassemble()
        self.identify_functions()
        return self.functions

    def parse_header(self):
        """Parse the MZ header of the DOS executable"""
        with open(self.filename, "rb") as f:
            # Read MZ header
            header = f.read(28)
            if header[0:2] != b"MZ":
                raise ValueError("Not a valid DOS executable (missing MZ signature)")

            # Extract header fields
            header_size = struct.unpack("<H", header[8:10])[0] * 16
            self.entry_point = struct.unpack("<H", header[24:26])[0]

            print(f"MZ Header parsed: Entry point at {self.entry_point:08X}")

            return header_size

    def extract_segments(self):
        """Extract segments from the DOS executable"""
        # Simplified approach - in a real decompiler, you'd parse the relocation table
        # and other headers to identify segments more accurately

        # Parse the header to get the header size
        header_size = self.parse_header()

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

        print(f"Extracted {len(self.segments)} segments")

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

        print(f"Found {len(self.strings)} strings")

        return self.strings

    def disassemble(self):
        """Disassemble the code segment (simplified)"""
        for segment in self.segments:
            if segment.type != "CODE":
                continue

            # Simple pattern-based disassembly (very simplified)
            # In a real decompiler, you'd use a proper disassembly library like Capstone

            i = 0
            while i < len(segment.data):
                # Check for common instruction patterns
                if i + 1 < len(segment.data):
                    # MOV reg, imm
                    if segment.data[i] == 0xB8:  # MOV AX, imm
                        value = struct.unpack("<H", segment.data[i + 1 : i + 3])[0]
                        instr = X86Instruction(
                            segment.start_offset + i,
                            segment.data[i : i + 3],
                            "mov",
                            f"ax, 0x{value:X}",
                        )
                        segment.instructions.append(instr)
                        i += 3
                        continue

                    # INT instruction
                    if segment.data[i] == 0xCD:  # INT xx
                        value = segment.data[i + 1]
                        instr = X86Instruction(
                            segment.start_offset + i,
                            segment.data[i : i + 2],
                            "int",
                            f"0x{value:X}",
                        )
                        segment.instructions.append(instr)
                        i += 2
                        continue

                # Default: treat as a single-byte instruction
                instr = X86Instruction(
                    segment.start_offset + i,
                    segment.data[i : i + 1],
                    "db",
                    f"0x{segment.data[i]:02X}",
                )
                segment.instructions.append(instr)
                i += 1

        return self.segments

    def identify_functions(self):
        """Identify functions in the code segment"""
        # Start with the entry point
        entry_function = DOSFunction("entry", self.entry_point)
        self.functions.append(entry_function)

        # In a real decompiler, you'd use more sophisticated techniques:
        # - Look for function prologues (PUSH BP, MOV BP, SP)
        # - Follow call instructions
        # - Analyze the control flow

        # For now, just assign all instructions to the entry function
        for segment in self.segments:
            if segment.type != "CODE":
                continue

            for instr in segment.instructions:
                if self.entry_point <= instr.address < self.file_size:
                    entry_function.instructions.append(instr)

        print(f"Identified {len(self.functions)} functions")

        return self.functions

    def generate_pseudocode(self):
        """Generate pseudocode from disassembly"""
        pseudocode = []
        pseudocode.append("// Pseudocode for " + os.path.basename(self.filename))
        pseudocode.append("")

        # Add forward declarations for all functions
        pseudocode.append("// Function declarations")
        for function in self.functions:
            pseudocode.append(f"void {function.name}();")
        pseudocode.append("")

        # Generate function bodies
        for function in self.functions:
            pseudocode.append(f"void {function.name}() {{")

            if function.instructions:
                for instr in function.instructions:
                    # Check if this instruction references a string
                    if instr.mnemonic == "mov" and "offset" in instr.operands:
                        # Try to extract the offset
                        match = re.search(r"offset\s+(\w+)", instr.operands)
                        if match:
                            offset_str = match.group(1)
                            try:
                                offset = int(offset_str, 16)
                                if offset in self.strings:
                                    pseudocode.append(
                                        f'    // String reference: "{self.strings[offset]}"'
                                    )
                            except ValueError:
                                pass

                    pseudocode.append(f"    // {instr.mnemonic} {instr.operands}")
            else:
                pseudocode.append("    // No instructions found for this function")

            pseudocode.append("}")
            pseudocode.append("")

        return "\n".join(pseudocode)

    def save_output(self, output_dir: str, visualize: bool = False):
        """Save the decompilation output to files"""
        os.makedirs(output_dir, exist_ok=True)

        # Save header information
        with open(os.path.join(output_dir, "header.txt"), "w") as f:
            f.write(f"Filename: {self.filename}\n")
            f.write(f"File size: {self.file_size} bytes\n")
            f.write(f"Entry point: 0x{self.entry_point:X}\n")
            f.write("\nSegments:\n")
            for segment in self.segments:
                f.write(f"  {segment}\n")

        # Save disassembly
        with open(os.path.join(output_dir, "disassembly.asm"), "w") as f:
            for segment in self.segments:
                f.write(f"; Segment {segment.name}\n")
                for instr in segment.instructions:
                    f.write(f"{instr.address:08X}: {instr.mnemonic} {instr.operands}\n")

        # Save strings
        with open(os.path.join(output_dir, "strings.txt"), "w") as f:
            for addr, string in sorted(self.strings.items()):
                f.write(f'{addr:08X}: "{string}"\n')

        # Save pseudocode
        with open(os.path.join(output_dir, "pseudocode.c"), "w") as f:
            f.write(self.generate_pseudocode())

        print(f"Output saved to {output_dir}")
