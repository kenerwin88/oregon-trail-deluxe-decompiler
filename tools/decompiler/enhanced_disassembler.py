"""
Enhanced disassembler for DOS executables using Capstone.
"""

from typing import Set
from capstone import Cs, CS_ARCH_X86, CS_MODE_16

from .models import DOSFunction, X86Instruction
from .disassembler import DOSDecompiler
from .data_flow import DataFlowAnalyzer
from .utils import replace_memory_references, translate_condition
from .dos_api import recognize_interrupt
from .code_patterns import simplify_instruction, simplify_instruction_sequence
from .control_flow import improve_control_flow
from .variable_naming import rename_variables, apply_variable_renaming
from .function_analysis import update_function_signature
from .data_structures import update_function_with_data_structures
from .comment_generator import add_comments_to_function
from .oregon_trail_specific import (
    identify_game_constant,
    identify_memory_address,
    identify_game_pattern,
    enhance_with_game_knowledge,
    identify_game_function
)
from .c_code_generator import generate_c_code


class EnhancedDOSDecompiler(DOSDecompiler):
    """Enhanced DOS decompiler with Capstone integration"""

    def __init__(self, filename: str):
        super().__init__(filename)
        self.capstone = Cs(CS_ARCH_X86, CS_MODE_16)
        self.capstone.detail = True
        self.use_improved_decompiler = False

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

        # Apply improved decompiler features if enabled
        if self.use_improved_decompiler:
            print("Applying improved decompiler features...")
            for func in self.functions:
                # Skip functions without instructions
                if not func.instructions:
                    continue

                # Analyze function parameters and return values
                update_function_signature(func)

                # Analyze data structures
                update_function_with_data_structures(func)

                # Rename variables to more meaningful names
                if hasattr(func, "variables") and func.variables:
                    rename_variables(func)

                # Add comments to function
                add_comments_to_function(func)

                # Calculate function complexity
                func.calculate_complexity()
                
                # Identify game-specific function purpose
                if not func.purpose:
                    instructions_text = [f"{instr.mnemonic} {instr.operands}" for instr in func.instructions]
                    game_purpose = identify_game_function(func.name, instructions_text)
                    if game_purpose:
                        func.purpose = game_purpose

            print("Improved decompiler features applied")

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

        print("Disassembly completed")
        return self.segments

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
        """Generate improved pseudocode with variable information and control flow structures"""
        pseudocode = []
        pseudocode.append(
            "// Enhanced Pseudocode for OREGON.EXE with Control Flow and Data Flow Analysis"
        )
        pseudocode.append("// Generated with Capstone-based disassembler")
        pseudocode.append("")

        # Process functions with our new modules
        for function in self.functions:
            # Analyze function parameters and return values
            update_function_signature(function)

            # Analyze data structures
            update_function_with_data_structures(function)

            # Rename variables to more meaningful names
            if hasattr(function, "variables") and function.variables:
                name_map = rename_variables(function)

            # Add comments to function
            add_comments_to_function(function)

            # Calculate function complexity
            function.calculate_complexity()

        # Add struct definitions
        struct_defs = {}
        for function in self.functions:
            if hasattr(function, "struct_defs"):
                for addr, struct_def in function.struct_defs.items():
                    if addr not in struct_defs:
                        struct_defs[addr] = struct_def

        if struct_defs:
            pseudocode.append("// Struct definitions")
            for addr, struct_def in sorted(struct_defs.items()):
                pseudocode.append(str(struct_def))
            pseudocode.append("")

        # Add forward declarations for all functions
        pseudocode.append("// Function declarations")
        for function in sorted(self.functions, key=lambda f: f.name):
            if function.signature:
                pseudocode.append(f"{function.signature};")
            else:
                pseudocode.append(f"void {function.name}();")
        pseudocode.append("")

        # Generate function bodies with control flow and variables
        for function in sorted(self.functions, key=lambda f: f.name):
            # Add function signature and purpose
            if function.signature:
                pseudocode.append(f"{function.signature} {{")
            else:
                pseudocode.append(f"void {function.name}() {{")

            if function.purpose:
                pseudocode.append(f"    // Purpose: {function.purpose}")
                pseudocode.append("")

            # Add complexity information
            if function.complexity > 0:
                pseudocode.append(f"    // Complexity: {function.complexity}")
                pseudocode.append("")

            # Add struct definitions specific to this function
            if hasattr(function, "struct_defs") and function.struct_defs:
                pseudocode.append("    // Local struct definitions")
                for addr, struct_def in sorted(function.struct_defs.items()):
                    if (
                        addr not in struct_defs
                    ):  # Only add if not already added globally
                        pseudocode.append(
                            "    " + str(struct_def).replace("\n", "\n    ")
                        )
                pseudocode.append("")

            # Add variable declarations if available
            if hasattr(function, "variables") and function.variables:
                pseudocode.append("    // Variable declarations")

                # First add parameters
                params = [v for v in function.variables.values() if v.is_parameter]
                if params:
                    pseudocode.append("    // Parameters:")
                    for var in sorted(params, key=lambda v: v.parameter_index):
                        if var.is_array:
                            pseudocode.append(
                                f"    // {var.type} {var.name}[]; // from parameter {var.parameter_index}"
                            )
                        elif var.is_struct:
                            pseudocode.append(
                                f"    // struct {var.struct_name} {var.name}; // from parameter {var.parameter_index}"
                            )
                        else:
                            pseudocode.append(
                                f"    // {var.type} {var.name}; // from parameter {var.parameter_index}"
                            )

                # Then add local variables
                locals = [
                    v
                    for v in function.variables.values()
                    if not v.is_parameter and not v.is_return_value
                ]
                if locals:
                    pseudocode.append("    // Local variables:")
                    for var in sorted(locals, key=lambda v: v.name):
                        if var.is_array:
                            pseudocode.append(
                                f"    {var.type} {var.name}[{var.array_length}];"
                            )
                        elif var.is_struct:
                            pseudocode.append(
                                f"    struct {var.struct_name} {var.name};"
                            )
                        else:
                            pseudocode.append(f"    {var.type} {var.name};")

                # Finally add return value if any
                return_vars = [
                    v for v in function.variables.values() if v.is_return_value
                ]
                if return_vars:
                    pseudocode.append("    // Return value:")
                    for var in return_vars:
                        pseudocode.append(
                            f"    // {var.type} {var.name}; // return value"
                        )

                pseudocode.append("")

            if function.instructions:
                # Use control flow graph if available
                if function.cfg and function.cfg.entry_block:
                    # Improve control flow structure
                    structures = improve_control_flow(function.cfg)

                    # Check if we identified any control flow structures
                    if any(structures.values()):
                        pseudocode.append("    // Control flow structures identified:")
                        if structures["loops"]:
                            pseudocode.append(
                                f"    // - {len(structures['loops'])} loops"
                            )
                        if structures["if_statements"]:
                            pseudocode.append(
                                f"    // - {len(structures['if_statements'])} if statements"
                            )
                        if structures["switch_statements"]:
                            pseudocode.append(
                                f"    // - {len(structures['switch_statements'])} switch statements"
                            )
                        pseudocode.append("")

                    # Generate code with improved control flow
                    block_code = self._generate_block_code(
                        function.cfg, function.cfg.entry_block, set(), 1
                    )

                    # Apply variable renaming to the generated code
                    if hasattr(function, "variables") and function.variables:
                        name_map = {
                            var.name: var.name for var in function.variables.values()
                        }
                        block_code_str = "\n".join(block_code)
                        block_code_str = apply_variable_renaming(
                            block_code_str, name_map
                        )
                        block_code = block_code_str.split("\n")

                    pseudocode.extend(block_code)
                else:
                    # Fallback to simple instruction listing
                    for instr in function.instructions:
                        # Try to simplify the instruction
                        simplified = simplify_instruction(instr)
                        if instr.comment:
                            pseudocode.append(f"    {simplified} // {instr.comment}")
                        else:
                            pseudocode.append(f"    {simplified}")

                # Add function calls
                if function.calls:
                    pseudocode.append("")
                    pseudocode.append("    // Function calls:")
                    for call_addr in function.calls:
                        # Find the function name for this address
                        for called_func in self.functions:
                            if called_func.start_address == call_addr:
                                if called_func.signature:
                                    pseudocode.append(
                                        f"    {called_func.name}(); // {called_func.purpose or ''}"
                                    )
                                else:
                                    pseudocode.append(
                                        f"    {called_func.name}(); // {called_func.purpose or ''}"
                                    )
                                break
                        else:
                            pseudocode.append(
                                f"    // Call to unknown function at 0x{call_addr:X}"
                            )
            else:
                pseudocode.append("    // No instructions found for this function")

            pseudocode.append("}")
            pseudocode.append("")

        print("Pseudocode generation completed")
        
        # Apply Oregon Trail specific enhancements if improved decompiler is enabled
        if self.use_improved_decompiler:
            print("Applying Oregon Trail specific enhancements...")
            pseudocode_str = "\n".join(pseudocode)
            pseudocode_str = enhance_with_game_knowledge(pseudocode_str)
            return pseudocode_str
        else:
            return "\n".join(pseudocode)
            
    def generate_c_code(self):
        """Generate readable C code from the disassembled functions"""
        print("Generating C code...")
        
        # Make sure all functions have been properly analyzed
        for function in self.functions:
            # Skip functions without instructions
            if not function.instructions:
                continue
                
            # Analyze function parameters and return values if not already done
            if not hasattr(function, 'signature') or not function.signature:
                update_function_signature(function)
            
            # Analyze data structures if not already done
            update_function_with_data_structures(function)
            
            # Rename variables to more meaningful names if not already done
            if hasattr(function, "variables") and function.variables:
                if not any(hasattr(var, 'is_renamed') and var.is_renamed for var in function.variables.values()):
                    rename_variables(function)
            
            # Add comments to function if not already done
            add_comments_to_function(function)
            
            # Identify game-specific function purpose if not already done
            if not hasattr(function, 'purpose') or not function.purpose:
                instructions_text = [f"{instr.mnemonic} {instr.operands}" for instr in function.instructions]
                game_purpose = identify_game_function(function.name, instructions_text)
                if game_purpose:
                    function.purpose = game_purpose
        
        # Generate C code
        c_code = generate_c_code(self.functions)
        
        print("C code generation completed")
        return c_code

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

        # Simplify the instruction sequence
        simplified_code = simplify_instruction_sequence(block.instructions[:-1])

        # Add instructions with variable references where possible
        for i, instr in enumerate(block.instructions[:-1]):  # All but last instruction
            # Replace memory references with variable names
            op_with_vars = instr.operands
            if hasattr(cfg.function, "variables") and cfg.function.variables:
                op_with_vars = replace_memory_references(
                    op_with_vars, cfg.function.variables
                )

            # Check for interrupt calls
            if instr.mnemonic == "int":
                try:
                    interrupt_num = int(op_with_vars, 16)
                    # Look for the function number in AH
                    function_num = None
                    for j in range(i - 1, max(0, i - 5), -1):
                        prev_instr = block.instructions[j]
                        if (
                            prev_instr.mnemonic == "mov"
                            and prev_instr.operands.startswith("ah,")
                        ):
                            try:
                                function_num = int(
                                    prev_instr.operands.split(",")[1].strip(), 16
                                )
                                break
                            except ValueError:
                                pass

                    interrupt = recognize_interrupt(interrupt_num, function_num)
                    if interrupt:
                        lines.append(
                            f"{'    ' * indent_level}{interrupt.name}();  // {instr.mnemonic} {op_with_vars}"
                        )
                        continue
                except ValueError:
                    pass

            # Use simplified code if available
            if i < len(simplified_code):
                lines.append(f"{'    ' * indent_level}{simplified_code[i]}")
            else:
                lines.append(f"{'    ' * indent_level}{instr.mnemonic} {op_with_vars};")

        # Handle last instruction based on control flow
        if block.is_conditional_branch():
            # This is an if statement
            last_instr = block.instructions[-1]

            # Replace memory references with variable names
            op_with_vars = last_instr.operands
            if hasattr(cfg.function, "variables") and cfg.function.variables:
                op_with_vars = replace_memory_references(
                    op_with_vars, cfg.function.variables
                )

            condition = translate_condition(last_instr.mnemonic)
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

            # Replace memory references with variable names
            op_with_vars = last_instr.operands
            if hasattr(cfg.function, "variables") and cfg.function.variables:
                op_with_vars = replace_memory_references(
                    op_with_vars, cfg.function.variables
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

            # Replace memory references with variable names
            op_with_vars = last_instr.operands
            if hasattr(cfg.function, "variables") and cfg.function.variables:
                op_with_vars = replace_memory_references(
                    op_with_vars, cfg.function.variables
                )

            lines.append(
                f"{'    ' * indent_level}return;  // {last_instr.mnemonic} {op_with_vars}"
            )

        else:
            # Regular instruction with fall-through
            if block.instructions:
                last_instr = block.instructions[-1]

                # Replace memory references with variable names
                op_with_vars = last_instr.operands
                if hasattr(cfg.function, "variables") and cfg.function.variables:
                    op_with_vars = replace_memory_references(
                        op_with_vars, cfg.function.variables
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

    # Removed _translate_condition method - now using utility function
