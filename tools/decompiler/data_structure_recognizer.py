"""
Advanced data structure recognition for the Oregon Trail decompiler.
"""

from typing import Dict, List, Set, Tuple, Optional
import re
from .models import DOSFunction, Variable, X86Instruction

class DataStructure:
    """Base class for recognized data structures."""
    
    def __init__(self, name: str, address: int, size: int = 0):
        """
        Initialize a data structure.
        
        Args:
            name: Name of the data structure
            address: Memory address of the data structure
            size: Size in bytes
        """
        self.name = name
        self.address = address
        self.size = size
        self.references = []  # Instructions referencing this structure
        self.comment = None  # Optional comment
        
    def __str__(self):
        return f"{self.name} at 0x{self.address:X} (size: {self.size} bytes)"


class Array(DataStructure):
    """Array data structure."""
    
    def __init__(self, name: str, address: int, element_type: str, element_size: int, length: int):
        """
        Initialize an array.
        
        Args:
            name: Name of the array
            address: Memory address of the array
            element_type: Type of array elements
            element_size: Size of each element in bytes
            length: Number of elements in the array
        """
        super().__init__(name, address, element_size * length)
        self.element_type = element_type
        self.element_size = element_size
        self.length = length
        self.elements = {}  # Mapped by offset
        
    def __str__(self):
        return f"{self.element_type} {self.name}[{self.length}]; // at 0x{self.address:X}"


class Struct(DataStructure):
    """Struct data structure."""
    
    def __init__(self, name: str, address: int):
        """
        Initialize a struct.
        
        Args:
            name: Name of the struct
            address: Memory address of the struct
        """
        super().__init__(name, address)
        self.fields = []  # List of (offset, name, type, size) tuples
        
    def add_field(self, offset: int, name: str, field_type: str, size: int):
        """
        Add a field to the struct.
        
        Args:
            offset: Offset from the struct base address
            name: Field name
            field_type: Type of the field
            size: Size of the field in bytes
        """
        self.fields.append((offset, name, field_type, size))
        self.size = max(self.size, offset + size)
        
    def __str__(self):
        """Generate C-style struct definition."""
        lines = [f"struct {self.name} {{"]
        for offset, name, field_type, size in sorted(self.fields, key=lambda x: x[0]):
            lines.append(f"    {field_type} {name}; // offset: {offset}, size: {size}")
        lines.append("};")
        return "\n".join(lines)


class DataStructureRecognizer:
    """Recognizes data structures in DOS code."""
    
    def __init__(self, functions: List[DOSFunction], strings: Dict[int, str]):
        """
        Initialize the recognizer.
        
        Args:
            functions: List of functions from the decompiled code
            strings: Dictionary of strings from the decompiled code
        """
        self.functions = functions
        self.strings = strings
        self.arrays = {}  # Address -> Array
        self.structs = {}  # Address -> Struct
        self.data_accesses = {}  # Address -> list of access instructions
        
    def analyze(self):
        """Analyze the code for data structures."""
        # First, identify all memory accesses
        self._collect_memory_accesses()
        
        # Then, identify arrays
        self._identify_arrays()
        
        # Then, identify structs
        self._identify_structs()
        
        # Finally, enhance functions with data structure information
        self._enhance_functions()
        
        return self.arrays, self.structs
    
    def _collect_memory_accesses(self):
        """Collect all memory access instructions."""
        for func in self.functions:
            for instr in func.instructions:
                # Look for memory accesses
                if "ptr [" in instr.operands:
                    # Extract memory address from operands
                    self._process_memory_access(instr)
    
    def _process_memory_access(self, instr: X86Instruction):
        """
        Process a memory access instruction.
        
        Args:
            instr: The instruction to process
        """
        # Look for direct memory accesses like [0x1234]
        direct_accesses = re.findall(r'\[(?:word |byte |dword )?ptr (?:ds:)?0x([0-9A-Fa-f]+)\]', instr.operands)
        
        for hex_addr in direct_accesses:
            addr = int(hex_addr, 16)
            if addr not in self.data_accesses:
                self.data_accesses[addr] = []
            self.data_accesses[addr].append(instr)
            
        # Look for indexed accesses like [0x1234 + ax] which might indicate arrays
        indexed_accesses = re.findall(r'\[(?:word |byte |dword )?ptr (?:ds:)?0x([0-9A-Fa-f]+)[\s+]*\+[\s+]*(\w+)\]', instr.operands)
        
        for hex_addr, index_reg in indexed_accesses:
            addr = int(hex_addr, 16)
            # This looks like an array access
            if addr not in self.data_accesses:
                self.data_accesses[addr] = []
            instr.is_array_access = True
            instr.array_index_reg = index_reg
            self.data_accesses[addr].append(instr)
            
        # Look for struct field accesses like [bx + 4]
        struct_accesses = re.findall(r'\[(?:word |byte |dword )?ptr (?:ds:)?(\w+)[\s+]*\+[\s+]*([0-9]+)\]', instr.operands)
        
        for base_reg, offset_str in struct_accesses:
            # This might be a struct access - we need to track the register
            offset = int(offset_str)
            instr.is_struct_access = True
            instr.struct_base_reg = base_reg
            instr.struct_field_offset = offset
            
            # We don't know the struct address yet, but we'll track this instruction
            key = f"struct_{base_reg}_{offset}"
            if key not in self.data_accesses:
                self.data_accesses[key] = []
            self.data_accesses[key].append(instr)
    
    def _identify_arrays(self):
        """Identify arrays based on collected memory accesses."""
        # Look for sequential memory accesses with increasing offsets
        potential_arrays = {}
        
        for addr, instrs in self.data_accesses.items():
            if isinstance(addr, int):  # Only process direct memory addresses
                # Check if any instructions use indexed addressing
                has_indexed_access = any(
                    hasattr(instr, "is_array_access") and instr.is_array_access
                    for instr in instrs
                )
                
                if has_indexed_access:
                    # Determine element size based on operand prefixes
                    element_size = self._determine_element_size(instrs)
                    
                    # Try to determine array length
                    array_length = self._estimate_array_length(addr, element_size)
                    
                    # Create an array object
                    array_name = f"array_{addr:X}"
                    element_type = self._determine_element_type(element_size)
                    
                    array = Array(array_name, addr, element_type, element_size, array_length)
                    array.references = instrs
                    
                    self.arrays[addr] = array
        
        # Look for adjacent arrays
        self._identify_adjacent_arrays()
    
    def _determine_element_size(self, instrs: List[X86Instruction]) -> int:
        """
        Determine the element size of an array based on the instructions.
        
        Args:
            instrs: List of instructions accessing the array
            
        Returns:
            Element size in bytes
        """
        # Default to 2 bytes (word) for 16-bit code
        element_size = 2
        
        for instr in instrs:
            if "byte ptr" in instr.operands:
                element_size = 1
            elif "dword ptr" in instr.operands:
                element_size = 4
        
        return element_size
    
    def _determine_element_type(self, element_size: int) -> str:
        """
        Determine the element type based on size.
        
        Args:
            element_size: Size of the element in bytes
            
        Returns:
            C type name
        """
        if element_size == 1:
            return "char"
        elif element_size == 2:
            return "int"
        elif element_size == 4:
            return "long"
        else:
            return f"uint{element_size * 8}_t"
    
    def _estimate_array_length(self, addr: int, element_size: int) -> int:
        """
        Estimate the length of an array.
        
        Args:
            addr: Base address of the array
            element_size: Size of each element in bytes
            
        Returns:
            Estimated array length
        """
        # Start with a default length
        length = 10
        
        # Check if we see access to elements with higher indices
        for offset in range(element_size, 101 * element_size, element_size):
            if addr + offset in self.data_accesses:
                length = max(length, offset // element_size + 1)
        
        # Check for evidence of loops or index comparison
        for func in self.functions:
            for instr in func.instructions:
                if instr.mnemonic.lower() in ["cmp", "jl", "jle"]:
                    # Look for comparison with literal values that might be array bounds
                    try:
                        operands = instr.operands.split(',')
                        if len(operands) >= 2:
                            value_str = operands[1].strip()
                            if value_str.isdigit():
                                bound = int(value_str)
                                if 1 < bound < 1000:  # Reasonable array size
                                    length = max(length, bound)
                    except (ValueError, IndexError):
                        pass
        
        return length
    
    def _identify_adjacent_arrays(self):
        """Identify arrays that are adjacent to each other, which might be 2D arrays."""
        # Sort arrays by address
        sorted_addrs = sorted(self.arrays.keys())
        
        # Check for adjacent arrays with same element type and size
        i = 0
        while i < len(sorted_addrs) - 1:
            addr1 = sorted_addrs[i]
            addr2 = sorted_addrs[i + 1]
            array1 = self.arrays[addr1]
            array2 = self.arrays[addr2]
            
            # Check if they're adjacent
            if addr1 + array1.size == addr2 and array1.element_type == array2.element_type:
                # These might be rows of a 2D array
                num_rows = 0
                row_size = array1.size
                base_addr = addr1
                
                # Count how many consecutive arrays match this pattern
                for j in range(i, len(sorted_addrs)):
                    addr_j = sorted_addrs[j]
                    if addr_j == base_addr + num_rows * row_size and self.arrays[addr_j].element_type == array1.element_type:
                        num_rows += 1
                    else:
                        break
                
                if num_rows > 1:
                    # Create a 2D array
                    array_name = f"array2d_{addr1:X}"
                    element_type = array1.element_type
                    element_size = array1.element_size
                    cols = array1.length
                    
                    # Create a new array object for the 2D array
                    array_2d = Array(array_name, addr1, element_type, element_size, cols * num_rows)
                    array_2d.is_2d = True
                    array_2d.rows = num_rows
                    array_2d.cols = cols
                    array_2d.comment = f"2D array: {element_type} {array_name}[{num_rows}][{cols}]"
                    
                    # Replace the individual arrays with the 2D array
                    for j in range(num_rows):
                        addr_j = base_addr + j * row_size
                        if addr_j in self.arrays:
                            array_2d.references.extend(self.arrays[addr_j].references)
                            del self.arrays[addr_j]
                    
                    self.arrays[addr1] = array_2d
                    i += num_rows  # Skip the arrays we just processed
                    continue
            
            i += 1
    
    def _identify_structs(self):
        """Identify structs based on collected memory accesses."""
        # Look for register+offset memory accesses
        struct_fields = {}
        
        for key, instrs in self.data_accesses.items():
            if isinstance(key, str) and key.startswith("struct_"):
                # This is a potential struct field access
                parts = key.split("_")
                if len(parts) >= 3:
                    base_reg = parts[1]
                    offset = int(parts[2])
                    
                    # Group fields by base register
                    if base_reg not in struct_fields:
                        struct_fields[base_reg] = {}
                    
                    if offset not in struct_fields[base_reg]:
                        struct_fields[base_reg][offset] = []
                        
                    struct_fields[base_reg][offset].extend(instrs)
        
        # For each potential struct (identified by base register)
        for base_reg, fields in struct_fields.items():
            if len(fields) > 1:  # Require at least two fields to consider it a struct
                # Try to determine the struct's base address
                struct_addr = self._determine_struct_address(base_reg, fields)
                
                if struct_addr is not None:
                    # Create a struct object
                    struct_name = f"struct_{struct_addr:X}"
                    struct = Struct(struct_name, struct_addr)
                    
                    # Add fields
                    for offset, instrs in sorted(fields.items()):
                        field_size = self._determine_field_size(instrs)
                        field_type = self._determine_element_type(field_size)
                        field_name = f"field_{offset:X}"
                        
                        struct.add_field(offset, field_name, field_type, field_size)
                        struct.references.extend(instrs)
                    
                    self.structs[struct_addr] = struct
    
    def _determine_struct_address(self, base_reg: str, fields: Dict[int, List[X86Instruction]]) -> Optional[int]:
        """
        Try to determine the base address of a struct.
        
        Args:
            base_reg: Base register used for struct accesses
            fields: Dictionary mapping field offsets to access instructions
            
        Returns:
            Base address of the struct, or None if it can't be determined
        """
        # Look for instructions that load the struct address into the base register
        for func in self.functions:
            for i, instr in enumerate(func.instructions):
                if instr.mnemonic.lower() == "mov" and f"{base_reg}," in instr.operands.lower():
                    # Check if the source operand is a memory address
                    operands = instr.operands.split(',')
                    if len(operands) >= 2:
                        src = operands[1].strip()
                        if src.startswith('0x'):
                            try:
                                return int(src, 16)
                            except ValueError:
                                pass
                        elif 'offset' in src.lower():
                            # Handle "offset label" format
                            match = re.search(r'offset\s+(\w+)', src, re.IGNORECASE)
                            if match:
                                label = match.group(1)
                                # Try to find the label address in the function
                                for j, preceding in enumerate(func.instructions[:i]):
                                    if preceding.mnemonic.lower() == "mov" and label in preceding.operands:
                                        addr_match = re.search(r'0x([0-9A-Fa-f]+)', preceding.operands)
                                        if addr_match:
                                            return int(addr_match.group(1), 16)
        
        # If we can't determine the address, use a placeholder
        return None
    
    def _determine_field_size(self, instrs: List[X86Instruction]) -> int:
        """
        Determine the size of a struct field based on the instructions.
        
        Args:
            instrs: List of instructions accessing the field
            
        Returns:
            Field size in bytes
        """
        # Default to 2 bytes (word) for 16-bit code
        field_size = 2
        
        for instr in instrs:
            if "byte ptr" in instr.operands:
                field_size = 1
            elif "dword ptr" in instr.operands:
                field_size = 4
        
        return field_size
    
    def _enhance_functions(self):
        """Enhance functions with data structure information."""
        # For each function, add data structure information to its variables
        for func in self.functions:
            # Initialize struct_defs if it doesn't exist
            if not hasattr(func, "struct_defs"):
                func.struct_defs = {}
            
            # Add array information
            for addr, array in self.arrays.items():
                # Check if this function references the array
                if any(instr in array.references for instr in func.instructions):
                    # Add array as a variable
                    var_name = array.name
                    var = Variable(var_name, address=addr)
                    var.type = array.element_type
                    var.is_array = True
                    var.array_length = array.length
                    var.element_size = array.element_size
                    
                    if hasattr(array, "is_2d") and array.is_2d:
                        var.is_2d_array = True
                        var.rows = array.rows
                        var.cols = array.cols
                        var.comment = array.comment
                    
                    if not hasattr(func, "variables"):
                        func.variables = {}
                    
                    func.variables[var_name] = var
            
            # Add struct information
            for addr, struct in self.structs.items():
                # Check if this function references the struct
                if any(instr in struct.references for instr in func.instructions):
                    # Add struct definition to function
                    func.struct_defs[addr] = struct
                    
                    # Add struct as a variable
                    var_name = struct.name
                    var = Variable(var_name, address=addr)
                    var.type = "struct"
                    var.is_struct = True
                    var.struct_name = struct.name
                    var.struct_size = struct.size
                    
                    if not hasattr(func, "variables"):
                        func.variables = {}
                    
                    func.variables[var_name] = var
    
    def generate_structure_report(self) -> str:
        """
        Generate a report of the recognized data structures.
        
        Returns:
            A formatted report string
        """
        report = []
        report.append("=== Data Structure Analysis Report ===")
        report.append("")
        
        # Arrays
        if self.arrays:
            report.append("Recognized Arrays:")
            for addr, array in sorted(self.arrays.items()):
                if hasattr(array, "is_2d") and array.is_2d:
                    report.append(f"  {array.element_type} {array.name}[{array.rows}][{array.cols}]; // at 0x{array.address:X}")
                else:
                    report.append(f"  {array.element_type} {array.name}[{array.length}]; // at 0x{array.address:X}")
            report.append("")
        
        # Structs
        if self.structs:
            report.append("Recognized Structs:")
            for addr, struct in sorted(self.structs.items()):
                report.append(f"  struct {struct.name} {{ // at 0x{struct.address:X}")
                for offset, name, field_type, size in sorted(struct.fields, key=lambda x: x[0]):
                    report.append(f"    {field_type} {name}; // offset: {offset}, size: {size}")
                report.append("  };")
            report.append("")
        
        # Most accessed structures
        if self.arrays or self.structs:
            report.append("Most Referenced Structures:")
            all_structures = list(self.arrays.values()) + list(self.structs.values())
            sorted_structures = sorted(all_structures, key=lambda s: len(s.references), reverse=True)
            
            for structure in sorted_structures[:10]:  # Top 10
                if isinstance(structure, Array):
                    type_str = "Array"
                else:
                    type_str = "Struct"
                report.append(f"  {structure.name} ({type_str}): Referenced {len(structure.references)} times")
            
            report.append("")
        
        return "\n".join(report)